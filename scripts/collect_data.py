"""Collect fine-tuning data: (state text, MaxPressure label, per-phase rollout costs) for every intersection-step.

The behaviour policy is MaxPressure with epsilon-random actions per intersection (DAgger-style state coverage:
the fine-tuned model will visit states MaxPressure itself would not). Labels are always MaxPressure's choice in the
visited state, plus the counterfactual cost of each phase from simulator rollouts (`TSCEnv.rollout_costs`).

    python scripts/collect_data.py --dataset jinan --traffic_file anon_3_4_jinan_real.json --eps 0.2 --seed 1
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jevtraffic.agents import MaxPressureAgent, phase_pressure, phase_queue  # noqa: E402
from jevtraffic.env import PHASES, ROOT, TSCEnv  # noqa: E402
from jevtraffic.prompts import load_task_info, raw_state, typed_state  # noqa: E402


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dataset", required=True)
    p.add_argument("--traffic_file", required=True)
    p.add_argument("--eps", type=float, default=0.0, help="probability of a random action per intersection")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--run_counts", type=int, default=3600)
    p.add_argument("--no_rollouts", action="store_true")
    p.add_argument("--raw", action="store_true", help="also store the (long) USTBench raw observation text")
    p.add_argument("--data_root", default=os.path.join(ROOT, "data", "tsc"))
    p.add_argument("--out_dir", default=os.path.join(ROOT, "data", "finetune"))
    args = p.parse_args()

    name = f"{args.dataset}__{args.traffic_file.removesuffix('.json')}__eps{args.eps:g}__s{args.seed}"
    out = os.path.join(args.out_dir, f"{name}.jsonl")
    os.makedirs(args.out_dir, exist_ok=True)
    task_info = load_task_info(args.data_root) if args.raw else None
    rng = random.Random(args.seed)
    env = TSCEnv(args.dataset, args.traffic_file, os.path.join(ROOT, "records", f"collect__{name}__{os.getpid()}"),
                 seed=args.seed, data_root=args.data_root, run_counts=args.run_counts)
    mp = MaxPressureAgent()
    t0 = time.time()
    n = 0
    with open(out, "w") as f:
        while not env.done:
            obs = env.observe()
            labels = mp.act(obs)
            costs = None if args.no_rollouts else env.rollout_costs()
            actions = []
            for i in range(obs.n):
                rec = {
                    "dataset": args.dataset, "traffic_file": args.traffic_file, "eps": args.eps, "seed": args.seed,
                    "t": obs.time, "inter": i, "current_phase": obs.current_phase[i],
                    "state_typed": typed_state(obs, i),
                    "mp_action": labels[i],
                    "queues": [phase_queue(obs, i, ph) for ph in PHASES],
                    "pressures": [round(phase_pressure(obs, i, ph), 3) for ph in PHASES],
                }
                if costs is not None:
                    rec["rollout_costs"] = costs[i]
                if args.raw:
                    rec["state_raw"] = raw_state(obs, i, task_info)
                f.write(json.dumps(rec) + "\n")
                n += 1
                actions.append(rng.randrange(len(PHASES)) if rng.random() < args.eps else labels[i])
            env.step(actions)
    m = env.metrics()
    print(json.dumps({"file": out, "samples": n, **m, "seconds": round(time.time() - t0, 1)}))


if __name__ == "__main__":
    main()
