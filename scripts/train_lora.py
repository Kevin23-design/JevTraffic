"""LoRA fine-tuning of the Jev-style decider on the answer token only.

The prompt is exactly what TypedDecider builds at inference (build_prompt + PHASE_QUESTION); the loss reads the
same position and the same 4 option-letter logits (softmax restricted to A-D), so training and readout match.
Options are shown in a random order per sample, so the model has to read the option text instead of a letter.

Losses
  ce    hard label = MaxPressure's phase (stage 1: distillation)
  soft  target distribution softmax(-(c - min c) / (tau * (max c - min c))) over the rollout costs c
        (stage 2: learn from the simulator's counterfactual outcomes; states with no cost gap are skipped)
  dpo   pairs (best, worse) phases by rollout cost, reference = the model at init (stage 2, alternative)
For stage 2 pass --init_adapter <stage-1 adapter>: it is merged into the base, a fresh LoRA is trained on top,
and (for dpo) the merged model with the new adapter disabled is the reference policy.

Single GPU:   python scripts/train_lora.py --train data/finetune/train/*.jsonl --out ckpt/distill
Multi GPU:    torchrun --nproc_per_node 4 scripts/train_lora.py ...
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import random
import sys
import time

import torch
import torch.distributed as dist
import torch.nn.functional as F

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jevtraffic.decider import Choice, build_prompt, load_model, single_token_ids  # noqa: E402
from jevtraffic.env import PHASES  # noqa: E402
from jevtraffic.prompts import PHASE_QUESTION, SYSTEM_PROMPT  # noqa: E402


def load_records(patterns, state_key, loss, min_gap, keep_idle, seed):
    rng = random.Random(seed)
    files = sorted({f for p in patterns for f in glob.glob(p)})
    recs, skipped_idle, skipped_gap = [], 0, 0
    for f in files:
        for line in open(f):
            r = json.loads(line)
            idle = max(r["queues"]) == 0 and max(r.get("rollout_costs") or [0]) == 0
            if idle and rng.random() > keep_idle:
                skipped_idle += 1
                continue
            if loss in ("soft", "dpo"):
                c = r["rollout_costs"]
                if max(c) - min(c) < min_gap:
                    skipped_gap += 1
                    continue
            recs.append({"state": r[state_key], "mp": r["mp_action"], "costs": r.get("rollout_costs")})
    return files, recs, {"skipped_idle": skipped_idle, "skipped_gap": skipped_gap}


def soft_target(costs, tau):
    c = torch.tensor(costs, dtype=torch.float32)
    span = (c.max() - c.min()).clamp_min(1e-6)
    return torch.softmax(-(c - c.min()) / (tau * span), dim=0)


def make_batch(tokenizer, recs, rng, loss, tau):
    """Prompts with a random option order per record, plus targets mapped into that order."""
    prompts, targets, pairs = [], [], []
    for r in recs:
        order = list(range(len(PHASES)))
        rng.shuffle(order)  # order[pos] = phase shown at letter pos
        q = Choice(PHASE_QUESTION.question, [PHASE_QUESTION.options[j] for j in order], PHASE_QUESTION.name)
        prompts.append(build_prompt(tokenizer, r["state"], q, SYSTEM_PROMPT))
        pos_of = {ph: pos for pos, ph in enumerate(order)}
        if loss == "ce":
            targets.append(pos_of[r["mp"]])
        elif loss == "soft":
            t = soft_target(r["costs"], tau)
            targets.append(torch.stack([t[order[pos]] for pos in range(len(order))]))
        else:  # dpo: best vs each strictly worse phase
            c = r["costs"]
            best = min(range(len(c)), key=c.__getitem__)
            pairs.append([(pos_of[best], pos_of[k]) for k in range(len(c)) if c[k] > c[best]])
    return prompts, targets, pairs


def letter_logprobs(model, tokenizer, prompts, letter_ids, device, max_len):
    enc = tokenizer(prompts, return_tensors="pt", padding=True, add_special_tokens=False,
                    truncation=True, max_length=max_len).to(device)
    logits = model(**enc, logits_to_keep=1).logits[:, -1, :]
    return F.log_softmax(logits[:, letter_ids].float(), dim=-1)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", default=os.path.expanduser("~/zzy/hf_models/Qwen2.5-7B-Instruct"))
    p.add_argument("--train", nargs="+", required=True, help="jsonl files / globs from collect_data.py")
    p.add_argument("--out", required=True)
    p.add_argument("--state_key", default="state_typed", choices=["state_typed", "state_raw"])
    p.add_argument("--loss", default="ce", choices=["ce", "soft", "dpo"])
    p.add_argument("--init_adapter", default=None, help="adapter merged into the base before training (stage 2)")
    p.add_argument("--tau", type=float, default=0.25, help="soft-target temperature (relative to cost span)")
    p.add_argument("--beta", type=float, default=0.5, help="DPO beta")
    p.add_argument("--min_gap", type=float, default=10.0, help="soft/dpo: skip states whose cost span is smaller")
    p.add_argument("--keep_idle", type=float, default=0.1, help="fraction of empty-intersection states to keep")
    p.add_argument("--epochs", type=float, default=1.0)
    p.add_argument("--batch_size", type=int, default=16, help="per GPU")
    p.add_argument("--grad_accum", type=int, default=1)
    p.add_argument("--lr", type=float, default=1e-4)
    p.add_argument("--rank", type=int, default=16)
    p.add_argument("--alpha", type=int, default=32)
    p.add_argument("--max_len", type=int, default=4096)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--log_every", type=int, default=20)
    p.add_argument("--save_every", type=int, default=200, help="optimizer steps between checkpoints (0 = only at end)")
    args = p.parse_args()

    ddp = "LOCAL_RANK" in os.environ
    if ddp:
        dist.init_process_group("nccl")
        local_rank = int(os.environ["LOCAL_RANK"])
        torch.cuda.set_device(local_rank)
        rank, world = dist.get_rank(), dist.get_world_size()
    else:
        local_rank, rank, world = 0, 0, 1
    device = torch.device("cuda", local_rank)
    main_proc = rank == 0

    from peft import LoraConfig, get_peft_model

    tokenizer, model = load_model(args.model, [args.init_adapter] if args.init_adapter else [], device=str(device))
    model.config.use_cache = False
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    model.enable_input_require_grads()
    model = get_peft_model(model, LoraConfig(
        r=args.rank, lora_alpha=args.alpha, lora_dropout=0.05, task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]))
    if main_proc:
        model.print_trainable_parameters()
    letter_ids = single_token_ids(tokenizer, "ABCD")

    files, recs, skipped = load_records(args.train, args.state_key, args.loss, args.min_gap, args.keep_idle, args.seed)
    rng = random.Random(args.seed)
    rng.shuffle(recs)
    recs = recs[rank::world]  # shard
    steps_per_epoch = len(recs) // args.batch_size
    total_steps = max(1, int(steps_per_epoch * args.epochs) // args.grad_accum)
    if main_proc:
        print(json.dumps({"files": len(files), "records_per_rank": len(recs), "world": world, "skipped": skipped,
                          "optimizer_steps": total_steps}), flush=True)

    params = [p_ for p_ in model.parameters() if p_.requires_grad]
    opt = torch.optim.AdamW(params, lr=args.lr, weight_decay=0.0)
    warmup = max(1, int(0.05 * total_steps))
    sched = torch.optim.lr_scheduler.LambdaLR(
        opt, lambda s: min(1.0, (s + 1) / warmup) * 0.5 * (1 + math.cos(math.pi * min(1.0, s / total_steps))))
    ddp_model = torch.nn.parallel.DistributedDataParallel(model, device_ids=[local_rank]) if ddp else model

    model.train()
    batch_rng = random.Random(args.seed + rank)
    step, micro, t0 = 0, 0, time.time()
    run_loss, run_acc, run_n = 0.0, 0.0, 0
    n_micro = total_steps * args.grad_accum
    while step < total_steps:
        for b in range(steps_per_epoch):
            if micro >= n_micro:
                break
            batch = recs[b * args.batch_size:(b + 1) * args.batch_size]
            prompts, targets, pairs = make_batch(tokenizer, batch, batch_rng, args.loss, args.tau)
            logp = letter_logprobs(ddp_model, tokenizer, prompts, letter_ids, device, args.max_len)
            if args.loss == "ce":
                tgt = torch.tensor(targets, device=device)
                loss = F.nll_loss(logp, tgt)
                acc = (logp.argmax(-1) == tgt).float().mean().item()
            elif args.loss == "soft":
                tgt = torch.stack(targets).to(device)
                loss = -(tgt * logp).sum(-1).mean()
                acc = (logp.argmax(-1) == tgt.argmax(-1)).float().mean().item()
            else:
                with torch.no_grad(), model.disable_adapter():
                    ref = letter_logprobs(model, tokenizer, prompts, letter_ids, device, args.max_len)
                terms = []
                for i, ps in enumerate(pairs):
                    for w, l in ps:
                        margin = (logp[i, w] - ref[i, w]) - (logp[i, l] - ref[i, l])
                        terms.append(-F.logsigmoid(args.beta * margin))
                loss = torch.stack(terms).mean() if terms else logp.sum() * 0.0
                acc = sum(int(logp[i].argmax().item() == ps[0][0]) for i, ps in enumerate(pairs) if ps) / max(
                    1, sum(1 for ps in pairs if ps))
            (loss / args.grad_accum).backward()
            micro += 1
            run_loss += loss.item()
            run_acc += acc
            run_n += 1
            if micro % args.grad_accum == 0:
                torch.nn.utils.clip_grad_norm_(params, 1.0)
                opt.step()
                sched.step()
                opt.zero_grad(set_to_none=True)
                step += 1
                if main_proc and args.save_every and step % args.save_every == 0 and step < total_steps:
                    model.save_pretrained(os.path.join(args.out, f"step{step}"))
                if main_proc and step % args.log_every == 0:
                    print(f"step {step}/{total_steps} loss={run_loss / run_n:.4f} acc={run_acc / run_n:.3f} "
                          f"lr={sched.get_last_lr()[0]:.2e} {time.time() - t0:.0f}s", flush=True)
                    run_loss, run_acc, run_n = 0.0, 0.0, 0
        if steps_per_epoch == 0:
            break

    if main_proc:
        os.makedirs(args.out, exist_ok=True)
        model.save_pretrained(args.out)
        with open(os.path.join(args.out, "train_meta.json"), "w") as f:
            json.dump({**vars(args), "files": files, "skipped": skipped, "optimizer_steps": total_steps,
                       "seconds": time.time() - t0}, f, indent=1)
        print("saved", args.out, flush=True)
    if ddp:
        dist.barrier()
        dist.destroy_process_group()


if __name__ == "__main__":
    main()
