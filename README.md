# JevTraffic

Use **Jev-style "System One" typed decision models** for traffic signal control (TSC). First version: an open-source,
self-hosted implementation (we do **not** call TypeSafe's official Jev API), evaluated on the
**Traffic Signal Control task of USTBench** ([arXiv:2505.17572](https://arxiv.org/abs/2505.17572), CityFlow, Hangzhou / Jinan real-world flows).

## Idea

Jev takes program state plus *typed questions* (choice / score / yes-no) and returns typed answers with
probabilities, without generating text. Signal control fits this exactly. Each intersection gets the
question "which phase next?" every 30 s, and the answer comes from a closed set
`{ETWT, NTST, ELWL, NLSL}`.

| | Generative LLM agent (USTBench style, "System Two") | Jev-style agent (this repo, "System One") |
|---|---|---|
| Output | free-text reasoning → parse answer | distribution over the 4 phases |
| Invalid output | possible (parse failures) | impossible by construction |
| Cost per decision | 1 prefill + hundreds of decode tokens | 1 prefill (single forward pass) |
| Confidence | none | probability per option → gating / escalation |

### Open-source Jev implementation (`jevtraffic/decider.py`)

This follows the recipe of [open-alternative-jev](https://github.com/ikermoel/open-alternative-jev) (Apache-2.0), "separate" mode:

1. Render state + one typed `Choice` (lettered options A–D) as a normal chat turn of an open-weights chat LLM (Qwen2.5-Instruct).
2. Run **one forward pass** and read the next-token logits at the assistant position.
3. Restrict to the option-letter tokens and apply softmax to get `P(phase | state)`.
4. Optional `permutations=k` scores k option orders and averages them. k=2 means identity + reversed; k≥n means all n cyclic shifts, a Latin square in which every option appears at every letter once.

On top of `Choice` there is a **`Score`** type (Jev's rubric/score question). The answer is one digit 0–9, read directly from the digit-token logits. `Decision.expected` gives the probability-weighted score. Many (state, question) pairs, of mixed types, are scored in one batched call (`decide_items`).

### Controllers (`jevtraffic/agents.py`)

| name | description |
|---|---|
| `fixedtime` | cycle the 4 phases, 30 s each |
| `random` | uniform random phase |
| `maxqueue` | phase with the largest queue |
| `maxpressure` | phase with the largest (queue upstream − queue downstream) |
| `jev-raw` | Jev decider on the **exact USTBench observation text** (target + neighbours + lane connectivity, ~1.9k tokens) |
| `jev-typed` | Jev decider on a compact **typed state** (per-phase queue / moving / wait / downstream occupancy, ~330 tokens) |
| `jev-typed` + `perm2` / `perm4` | the same Choice, debiased over 2 / 4 option orders |
| `jev-*-gate{τ}` | confidence gating: if `max P < τ` fall back to MaxPressure (Jev's "act when confident, escalate otherwise") |
| `jev-score-{raw,typed}` | four **Score** questions per intersection ("how urgent is green for phase p, 0–9?"), then argmax of expected urgency. There is no option list, so no position bias. |
| `llm-gen` | same LLM, generative CoT + `Answer: <phase>` via vLLM (USTBench-style baseline, no reflection loop) |

### Environment (`jevtraffic/env.py`)

This reuses USTBench's `TrafficSignalEnvironment` (CityFlow, 30 s decision interval, 5 s yellow, 3600 s → 120 decisions). Observation text and the metrics **ATT / AWT / AQL** are computed exactly as in USTBench. Only the agent loop is replaced.

> **Note:** USTBench's `_selection_to_signal_code` maps `['ETWT','ELWL','NTST','NLSL']` to action indices 0..3.
> But the roadnet `lightphases` (and `env_utils.four_phase_list`) order is `ETWT, NTST, ELWL, NLSL`.
> In the original benchmark, an LLM answer of `ELWL` therefore activates N/S through and vice versa.
> We use the roadnet order. This may partly explain the very high ATT numbers USTBench reports for LLMs (e.g. Qwen2.5-7B ATT 820 on Hangzhou).

## Layout

```
jevtraffic/   env.py (USTBench env wrapper) · decider.py (Jev-style typed decider) · prompts.py · agents.py
run_tsc.py    one episode: --agent {fixedtime,random,maxqueue,maxpressure,jev,llm-gen}
scripts/      fetch_third_party.sh · sync.sh · setup_server.sh · run_baselines.sh · run_llm.sh · analyze.py
              collect_all.sh / collect_data.py (MP rollouts + counterfactual costs) · train_lora.py · calibrate.py · run_finetuned.sh
results/      RESULTS.md (write-up) · summary.md / summary.csv (aggregated) · calib/*.json · runs/*.json (per-run, git-ignored)
```

## Reproduce

```bash
bash scripts/fetch_third_party.sh          # local: USTBench @ ee3978f + TSC data (server has no GitHub access)
bash scripts/sync.sh                       # rsync to root@202.120.87.207:~/zzy/JevTraffic (port 50030)
# on the server
bash scripts/setup_server.sh               # venv on top of conda env vllm_qwen3_cu124, build CityFlow, download Qwen2.5-7B-Instruct via hf-mirror
bash scripts/run_baselines.sh
MODELS="$HOME/zzy/hf_models/Qwen2.5-7B-Instruct $HOME/zzy/hf_models/Qwen2.5-0.5B-Instruct" GPUS="6 7" bash scripts/run_llm.sh
.venv/bin/python scripts/analyze.py        # -> results/summary.md
# fine-tuning (train: hangzhou_real, jinan_real, jinan_2000; held out: hangzhou_5816, jinan_2500)
bash scripts/collect_all.sh                # -> data/finetune/{train,val,test}/*.jsonl
T=scripts/train_lora.py; R="env CUDA_VISIBLE_DEVICES=6,7 .venv/bin/python -m torch.distributed.run --nproc_per_node 2"
$R $T --train "data/finetune/train/*.jsonl" --out ckpt/distill-typed --loss ce --batch_size 8 --epochs 0.5
$R $T --train "data/finetune/train/*.jsonl" --init_adapter ckpt/distill-typed --out ckpt/reward-dpo --loss dpo --batch_size 8 --epochs 0.5 --lr 5e-5
.venv/bin/python scripts/calibrate.py --adapters ckpt/distill-typed ckpt/reward-dpo --fit "data/finetune/val/*.jsonl" \
  --eval "data/finetune/test/hangzhou*" "data/finetune/test/jinan*" --label rollout   # writes calib.json (used automatically)
ADAPTERS="ckpt/distill-typed ckpt/reward-dpo" GPUS="6 7" bash scripts/run_finetuned.sh
# locally
bash scripts/sync.sh --pull
```

## Results

See [results/RESULTS.md](results/RESULTS.md).
