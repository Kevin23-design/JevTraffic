"""Collect keep/switch distillation data from a UniTSA teacher (one episode, one process).

Behaviour: the teacher with epsilon-random keep/switch actions (its 45 s max-green guard always applies), under
random special events, in `SumoTSCEnv(action_type="next_or_not")`. One "switch" record per decision the student
will actually face (forced switches are skipped, as the controller skips them):
  state      render_state / render_compact (both stored, so one collection serves both prompt formats)
  label      the teacher's deterministic action as an option index (0 keep, 1 switch)
  probs      the teacher's action distribution in option order (soft distillation target)
Blocked lanes are never rendered as excluded here: UniTSA has no notion of them, so its label would not match.
The situation records of scripts/sumo_collect.py are reused for the event question.

    python scripts/sumo_collect_unitsa.py --teacher ckpt/unitsa/universal/model.zip \
        --junction Beijing_Beihuan --env_name normal_high_density --eps 0.1 --seed 1
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jevtraffic.sumo_env import ROOT, SumoTSCEnv, random_events  # noqa: E402
from jevtraffic.sumo_prompts import (KEEP, SWITCH, action_to_option, render_compact, render_state,  # noqa: E402
                                     switch_question)
from jevtraffic.unitsa import MAX_GREEN, UniTSAAgent  # noqa: E402


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--teacher", required=True, help="UniTSA model.zip")
    p.add_argument("--junction", required=True)
    p.add_argument("--env_name", required=True)
    p.add_argument("--eps", type=float, default=0.0)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--p_accident", type=float, default=0.6)
    p.add_argument("--p_special", type=float, default=0.8)
    p.add_argument("--keep_confident", type=float, default=1.0,
                   help="fraction of states kept where the teacher's keep-probability is > 0.99 (long greens)")
    p.add_argument("--out_dir", default=os.path.join(ROOT, "data", "sumo_unitsa", "train"))
    args = p.parse_args()

    name = f"{args.junction}__{args.env_name}__eps{args.eps:g}__s{args.seed}"
    rng = random.Random(name)
    events = random_events(args.junction, args.env_name, rng, p_accident=args.p_accident, p_special=args.p_special)
    env = SumoTSCEnv(args.junction, args.env_name, os.path.join(ROOT, "records", "collect_unitsa", name),
                     events=events, seed=args.seed, action_type="next_or_not")
    teacher = UniTSAAgent(env, args.teacher)
    os.makedirs(args.out_dir, exist_ok=True)
    out = os.path.join(args.out_dir, f"{name}.jsonl")
    meta = {"kind": "switch", "junction": args.junction, "env_name": args.env_name, "eps": args.eps,
            "seed": args.seed}
    n, forced, switches, t0 = 0, 0, 0, time.time()
    obs = env.reset()
    with open(out, "w") as f:
        while not env.done:
            action = teacher.act(obs)  # updates the teacher's timer every step, so call it exactly once
            if obs.green_seconds >= MAX_GREEN:
                forced += 1  # guard: the controller switches without asking the model
            else:
                p_switch, p_keep = teacher.last_probs
                probs = [0.0, 0.0]
                probs[KEEP], probs[SWITCH] = p_keep, p_switch
                if probs[KEEP] <= 0.99 or rng.random() < args.keep_confident:
                    q = switch_question(obs)
                    rec = {**meta, "t": obs.time, "state": render_state(obs), "state_compact": render_compact(obs),
                           "question": q.question, "options": list(q.options), "label": action_to_option(action),
                           "probs": [round(x, 5) for x in probs], "green_seconds": obs.green_seconds}
                    f.write(json.dumps(rec) + "\n")
                    n += 1
                if rng.random() < args.eps:
                    action = rng.choice([0, 1])
            switches += action == 0
            obs = env.step(action)
    env.close()
    print(json.dumps({"file": out, "records": n, "forced": forced, "switches": switches, **env.metrics(),
                      "seconds": round(time.time() - t0, 1)}), flush=True)


if __name__ == "__main__":
    main()
    os._exit(0)
