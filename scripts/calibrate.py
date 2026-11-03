"""Temperature calibration + offline evaluation of a (fine-tuned) Jev-style decider.

Reads the 4 option-letter logits exactly as JevAgent does at inference (identity option order, permutations=1),
fits one temperature T on --fit files by minimising NLL against the label, and reports accuracy / NLL / ECE
before and after on every --eval file group. T is written to <last adapter>/calib.json, which run_tsc.py
picks up automatically.

    python scripts/calibrate.py --adapters ckpt/distill --fit data/finetune/val/*.jsonl \
        --eval data/finetune/test/*.jsonl --label mp
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jevtraffic.decider import TypedDecider, softmax  # noqa: E402
from jevtraffic.prompts import PHASE_QUESTION, SYSTEM_PROMPT  # noqa: E402


def load(patterns, state_key, label, max_n, seed):
    files = sorted({f for p in patterns for f in glob.glob(p)})
    recs = []
    for f in files:
        for line in open(f):
            r = json.loads(line)
            if max(r["queues"]) == 0:
                continue  # empty intersection: every phase is equally fine
            if label == "rollout":
                c = r["rollout_costs"]
                if max(c) - min(c) < 10:
                    continue
                y = min(range(4), key=c.__getitem__)
            else:
                y = r["mp_action"]
            recs.append((r[state_key], y))
    random.Random(seed).shuffle(recs)
    return files, recs[:max_n] if max_n else recs


def metrics(raws, ys, T, bins=10):
    nll = acc = 0.0
    conf_bins = [[0, 0.0, 0.0] for _ in range(bins)]  # count, sum conf, sum correct
    for raw, y in zip(raws, ys):
        p = softmax(raw, T)
        k = max(range(len(p)), key=p.__getitem__)
        nll -= math.log(max(p[y], 1e-12))
        acc += k == y
        b = min(bins - 1, int(p[k] * bins))
        conf_bins[b][0] += 1
        conf_bins[b][1] += p[k]
        conf_bins[b][2] += k == y
    n = len(ys)
    ece = sum(abs(s_c - s_a) for c, s_c, s_a in conf_bins if c) / n
    return {"n": n, "acc": round(acc / n, 4), "nll": round(nll / n, 4), "ece": round(ece, 4)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", default=os.path.expanduser("~/zzy/hf_models/Qwen2.5-7B-Instruct"))
    p.add_argument("--adapters", nargs="*", default=[])
    p.add_argument("--fit", nargs="+", required=True)
    p.add_argument("--eval", nargs="*", default=[], help="file groups to report, e.g. per held-out traffic file")
    p.add_argument("--label", default="mp", choices=["mp", "rollout"])
    p.add_argument("--state_key", default="state_typed")
    p.add_argument("--max_n", type=int, default=1500)
    p.add_argument("--batch_size", type=int, default=32)
    p.add_argument("--out", default=None, help="where to write calib.json (default: last adapter dir)")
    args = p.parse_args()

    dec = TypedDecider(args.model, batch_size=args.batch_size, system_prompt=SYSTEM_PROMPT, adapters=args.adapters)

    def raw_scores(recs):
        return [d.raw_scores for d in dec.decide_many([s for s, _ in recs], PHASE_QUESTION)]

    _, fit = load(args.fit, args.state_key, args.label, args.max_n, 0)
    fit_raw, fit_y = raw_scores(fit), [y for _, y in fit]
    grid = [math.exp(x / 20) for x in range(-60, 61)]  # T in [0.05, 20]
    T = min(grid, key=lambda t: metrics(fit_raw, fit_y, t)["nll"])
    report = {"label": args.label, "adapters": args.adapters, "temperature": T,
              "fit": {"T=1": metrics(fit_raw, fit_y, 1.0), f"T={T:.3f}": metrics(fit_raw, fit_y, T)}}
    for pattern in args.eval:
        files, recs = load([pattern], args.state_key, args.label, args.max_n, 0)
        raws, ys = raw_scores(recs), [y for _, y in recs]
        report[pattern] = {"files": [os.path.basename(f) for f in files],
                           "T=1": metrics(raws, ys, 1.0), f"T={T:.3f}": metrics(raws, ys, T)}
    print(json.dumps(report, indent=1))
    out = args.out or (args.adapters[-1] if args.adapters else None)
    if out:
        os.makedirs(out, exist_ok=True)
        with open(os.path.join(out, "calib.json"), "w") as f:
            json.dump(report, f, indent=1)
        print("saved", os.path.join(out, "calib.json"))


if __name__ == "__main__":
    main()
