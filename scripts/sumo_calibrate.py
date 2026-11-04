"""Temperature calibration + offline evaluation for the v2 (SUMO) decider, per question kind.

For each kind (phase, situation) one temperature is fitted on --fit records by NLL (identity option order, as at
inference). Accuracy / NLL / ECE are reported before and after on every --eval group, plus per-class precision /
recall for the situation question. Temperatures go to <last adapter>/calib.json as {"phase": T, "situation": T},
which run_sumo.py loads automatically.

    python scripts/sumo_calibrate.py --adapters ckpt/sumo-distill --fit "data/sumo_finetune/val/*.jsonl" \
        --eval "data/sumo_finetune/test_junction/*.jsonl" "data/sumo_finetune/test_pattern/*.jsonl"
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

from scripts.calibrate import metrics  # noqa: E402
from jevtraffic.decider import Choice, TypedDecider, softmax  # noqa: E402
from jevtraffic.sumo_env import SITUATIONS  # noqa: E402
from jevtraffic.sumo_prompts import SYSTEM_PROMPT  # noqa: E402

KINDS = ["phase", "situation", "switch"]


def load(patterns, kind, max_n, seed=0):
    files = sorted({f for p in patterns for f in glob.glob(p)})
    recs = [r for f in files for r in map(json.loads, open(f)) if r["kind"] == kind]
    random.Random(seed).shuffle(recs)
    return files, recs[:max_n] if max_n else recs


def per_class(raws, ys, T, labels):
    pred = [max(range(len(r)), key=softmax(r, T).__getitem__) for r in raws]
    out = {}
    for c, name in enumerate(labels):
        tp = sum(p == c and y == c for p, y in zip(pred, ys))
        npred, ntrue = sum(p == c for p in pred), sum(y == c for y in ys)
        out[name] = {"n": ntrue, "precision": round(tp / npred, 3) if npred else None,
                     "recall": round(tp / ntrue, 3) if ntrue else None}
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", default=os.path.expanduser("~/zzy/hf_models/Qwen2.5-7B-Instruct"))
    p.add_argument("--adapters", nargs="*", default=[])
    p.add_argument("--fit", nargs="+", required=True)
    p.add_argument("--eval", nargs="*", default=[])
    p.add_argument("--max_n", type=int, default=2000)
    p.add_argument("--batch_size", type=int, default=16)
    p.add_argument("--out", default=None)
    p.add_argument("--state_field", default="state", help="state / state_compact (switch records carry both)")
    args = p.parse_args()

    dec = TypedDecider(args.model, batch_size=args.batch_size, system_prompt=SYSTEM_PROMPT, adapters=args.adapters)
    report_args = {"model": args.model, "state_field": args.state_field}

    def raw_scores(recs):
        items = [(r.get(args.state_field, r["state"]), Choice(r["question"], r["options"], r["kind"])) for r in recs]
        return [d.raw_scores for d in dec.decide_items(items)]

    report = {"adapters": args.adapters, **report_args}
    grid = [math.exp(x / 20) for x in range(-60, 61)]  # T in [0.05, 20]
    for kind in KINDS:
        _, fit = load(args.fit, kind, args.max_n)
        if not fit:
            continue
        raws, ys = raw_scores(fit), [r["label"] for r in fit]
        T = min(grid, key=lambda t: metrics(raws, ys, t)["nll"])
        report[kind] = T
        rep = {"fit": {"T=1": metrics(raws, ys, 1.0), f"T={T:.3f}": metrics(raws, ys, T)}}
        for pattern in args.eval:
            files, recs = load([pattern], kind, args.max_n)
            if not recs:
                continue
            r2, y2 = raw_scores(recs), [r["label"] for r in recs]
            rep[pattern] = {"files": len(files), "T=1": metrics(r2, y2, 1.0), f"T={T:.3f}": metrics(r2, y2, T)}
            if kind == "situation":
                rep[pattern]["per_class"] = per_class(r2, y2, T, SITUATIONS)
            if kind == "switch":
                rep[pattern]["per_class"] = per_class(r2, y2, T, ["keep", "switch"])
        report[f"{kind}_report"] = rep
    print(json.dumps(report, indent=1))
    out = args.out or (args.adapters[-1] if args.adapters else None)
    if out:
        os.makedirs(out, exist_ok=True)
        with open(os.path.join(out, "calib.json"), "w") as f:
            json.dump(report, f, indent=1)
        print("saved", os.path.join(out, "calib.json"))


if __name__ == "__main__":
    main()
