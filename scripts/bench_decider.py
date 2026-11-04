"""Inference cost of Jev deciders: ms per decision by backbone x state format x prefix cache x batch size.

Reads real keep/switch states (scripts/sumo_collect_unitsa.py records), so prompt lengths are the deployed ones.
Also checks that the prefix-cached path gives the same probabilities as the plain one.

    python scripts/bench_decider.py --models ~/zzy/hf_models/Qwen2.5-0.5B-Instruct ~/zzy/hf_models/Qwen2.5-7B-Instruct \
        --data "data/sumo_unitsa/val/*.jsonl" --batch_sizes 1 8 32 --out results/sumo/bench/gpu.json
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import random
import statistics
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jevtraffic.decider import Choice, TypedDecider  # noqa: E402
from jevtraffic.sumo_prompts import SYSTEM_PROMPT  # noqa: E402


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--models", nargs="+", required=True)
    p.add_argument("--adapters", nargs="*", default=[], help="model=adapter pairs (optional)")
    p.add_argument("--data", required=True)
    p.add_argument("--n", type=int, default=64, help="states per setting")
    p.add_argument("--batch_sizes", nargs="+", type=int, default=[1, 8, 32])
    p.add_argument("--formats", nargs="+", default=["state", "state_compact"])
    p.add_argument("--device", default="cuda")
    p.add_argument("--dtype", default="bfloat16")
    p.add_argument("--threads", type=int, default=0, help="CPU: torch threads (0 = default)")
    p.add_argument("--out", required=True)
    p.add_argument("--modes", nargs="+", default=["plain", "prefix", "compile"])
    args = p.parse_args()

    import torch

    if args.threads:
        torch.set_num_threads(args.threads)
    recs = [json.loads(l) for f in sorted(glob.glob(args.data)) for l in open(f)]
    recs = [r for r in recs if r["kind"] == "switch"]
    random.Random(0).shuffle(recs)
    recs = recs[:args.n]
    adapters = dict(a.split("=", 1) for a in args.adapters)
    rows = []
    for model in args.models:
        if args.device == "cuda":
            torch.cuda.empty_cache()
            torch.cuda.reset_peak_memory_stats()
        dec = TypedDecider(model, device=args.device, dtype=args.dtype, system_prompt=SYSTEM_PROMPT,
                           adapters=[adapters[model]] if model in adapters else [])
        params = sum(x.numel() for x in dec.model.parameters())
        for fmt in args.formats:
            items = [(r[fmt], Choice(r["question"], r["options"], "switch")) for r in recs]
            tok = [len(dec.tokenizer(dec._prompt(s, q), add_special_tokens=False)["input_ids"]) for s, q in items]
            ref = None
            for mode in args.modes:
                dec.prefix_cache, dec.compile = mode == "prefix", mode == "compile"
                cache = mode == "prefix"
                for bs in args.batch_sizes:
                    dec.batch_size = bs
                    for _ in range(3):  # warm-up (compile: captures the graphs of the buckets used below)
                        for i in range(0, len(items) - bs + 1, bs):
                            dec.decide_items(items[i:i + bs])
                        if mode != "compile":
                            break
                    if args.device == "cuda":
                        torch.cuda.synchronize()
                    times, probs = [], []
                    for i in range(0, len(items) - bs + 1, bs):
                        t0 = time.perf_counter()
                        ds = dec.decide_items(items[i:i + bs])
                        if args.device == "cuda":
                            torch.cuda.synchronize()
                        times.append((time.perf_counter() - t0) / bs)
                        probs += [d.probabilities for d in ds]
                    if ref is None:
                        ref = probs
                    diff = max(abs(a - b) for pa, pb in zip(ref, probs) for a, b in zip(pa, pb))
                    row = {"model": os.path.basename(model.rstrip("/")), "params_M": round(params / 1e6, 1),
                           "device": args.device, "format": fmt, "mode": mode, "batch": bs,
                           "prompt_tokens": round(statistics.mean(tok), 1),
                           "prefix_tokens": len(dec._prefix()[0]) if cache else 0,
                           "ms_per_decision": round(1000 * statistics.median(times), 2),
                           "max_prob_diff_vs_plain": round(diff, 4)}
                    if args.device == "cuda":
                        row["peak_mem_GB"] = round(torch.cuda.max_memory_allocated() / 2**30, 2)
                    print(json.dumps(row), flush=True)
                    rows.append(row)
        del dec
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    json.dump(rows, open(args.out, "w"), indent=1)


if __name__ == "__main__":
    main()
    os._exit(0)
