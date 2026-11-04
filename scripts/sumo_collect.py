"""Collect v2 fine-tuning data on one SingleTSCBaselines scenario (one episode, one process).

Behaviour: MaxPressure with epsilon-random allowed actions, under random special events. Two kinds of records:
  phase      every decision with >1 allowed phase: typed state, allowed-phase options, label = MaxPressure.
             When a ground-truth blocked lane exists, half of the samples render it as blocked (the event plan's
             view) and the label is MaxPressure with that lane excluded, so the model learns the plan's semantics.
  situation  at steps where the context agent would trigger, where the ground truth is not "normal", and at 5% of
             the other steps: state + 5-step history table, label = ground-truth situation. Blockage steps are only
             kept when a blocked lane had green within the history window (otherwise nothing in the input shows it).
Options are stored in canonical order; train_lora.py shuffles them per sample.

    python scripts/sumo_collect.py --junction Beijing_Beihuan --env_name normal_high_density --eps 0.1 --seed 1
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jevtraffic.memory import ContextAgent  # noqa: E402
from jevtraffic.sumo_agents import mp_action  # noqa: E402
from jevtraffic.sumo_env import ROOT, SITUATIONS, SumoTSCEnv, random_events  # noqa: E402
from jevtraffic.sumo_prompts import (SITUATION_QUESTION, phase_question, render_state,  # noqa: E402
                                     situation_state)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--junction", required=True)
    p.add_argument("--env_name", required=True)
    p.add_argument("--eps", type=float, default=0.0)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--p_accident", type=float, default=0.6)
    p.add_argument("--p_special", type=float, default=0.8)
    p.add_argument("--keep_tie", type=float, default=0.1, help="fraction of all-equal-pressure states to keep")
    p.add_argument("--out_dir", default=os.path.join(ROOT, "data", "sumo_finetune", "train"))
    args = p.parse_args()

    name = f"{args.junction}__{args.env_name}__eps{args.eps:g}__s{args.seed}"
    rng = random.Random(name)
    events = random_events(args.junction, args.env_name, rng, p_accident=args.p_accident, p_special=args.p_special)
    env = SumoTSCEnv(args.junction, args.env_name, os.path.join(ROOT, "records", "collect_sumo", name),
                     events=events, seed=args.seed)
    ctx = ContextAgent("triggered")
    os.makedirs(args.out_dir, exist_ok=True)
    out = os.path.join(args.out_dir, f"{name}.jsonl")
    meta = {"junction": args.junction, "env_name": args.env_name, "eps": args.eps, "seed": args.seed}
    counts = {"phase": 0, "situation": 0}
    t0 = time.time()
    obs = env.reset()
    with open(out, "w") as f:
        while not env.done:
            ctx.observe(obs)
            gt = env.situation_label()
            triggers = ctx.triggers(obs)
            visible = True
            if gt == "blockage":  # only answerable if a blocked lane had green within the history window
                lanes = {l for l in env.blocked_lanes() if l in obs.lane_phases}
                visible = any(h.phase in obs.lane_phases[l] for h in ctx.memory.items() for l in lanes)
            if visible and (triggers or gt != "normal" or rng.random() < 0.05):
                rec = {"kind": "situation", **meta, "t": obs.time, "state": situation_state(obs, ctx.memory.items()),
                       "question": SITUATION_QUESTION.question, "options": list(SITUATION_QUESTION.options),
                       "label": SITUATIONS.index(gt), "triggers": [t.kind for t in triggers]}
                f.write(json.dumps(rec) + "\n")
                counts["situation"] += 1
            action = mp_action(obs)
            if len(obs.allowed) > 1:
                gt_blocked = {l for l in env.blocked_lanes() if l in obs.lane_halting}
                blocked = gt_blocked if gt_blocked and rng.random() < 0.5 else set()
                label = mp_action(obs, env, blocked)
                tie = len({obs.pressures[a] for a in obs.allowed}) == 1 and not blocked
                if not tie or rng.random() < args.keep_tie:
                    q, phases = phase_question(obs)
                    rec = {"kind": "phase", **meta, "t": obs.time, "state": render_state(obs, blocked),
                           "question": q.question, "options": list(q.options), "label": phases.index(label),
                           "pressures": [obs.pressures[a] for a in phases], "blocked": sorted(blocked)}
                    f.write(json.dumps(rec) + "\n")
                    counts["phase"] += 1
                if rng.random() < args.eps:
                    action = rng.choice(obs.allowed)
            obs = env.step(action)
    env.close()
    print(json.dumps({"file": out, **counts, **env.metrics(), "seconds": round(time.time() - t0, 1)}))


if __name__ == "__main__":
    main()
