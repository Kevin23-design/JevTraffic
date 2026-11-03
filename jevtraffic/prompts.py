"""State rendering and the typed question for the TSC task.

Two state formats are offered to the Jev-style decider:
  * "raw":   the exact USTBench observation text (target + neighbouring intersections + lane connectivity),
             prefixed by the USTBench task description. Same input the benchmark gives to generative LLMs.
  * "typed": a compact per-signal table of the target intersection (queue / moving / wait per movement,
             downstream occupancy, current phase). Jev's input is "program state", so we also test a
             structured state that a controller would naturally expose.
"""
from __future__ import annotations

import json
import os

from .decider import Choice, Score
from .env import PHASES, PHASE_MOVEMENTS, Observation

PHASE_DESCRIPTIONS = {
    "ETWT": "ETWT (east and west through traffic: lanes ET + WT)",
    "NTST": "NTST (north and south through traffic: lanes NT + ST)",
    "ELWL": "ELWL (east and west left-turn traffic: lanes EL + WL)",
    "NLSL": "NLSL (north and south left-turn traffic: lanes NL + SL)",
}

PHASE_QUESTION = Choice(
    "Which traffic signal should be activated at the target intersection for the next 30 seconds "
    "to most significantly reduce overall queue length and waiting time?",
    [PHASE_DESCRIPTIONS[p] for p in PHASES],  # option i <-> phase index i
    name="phase",
)

def phase_urgency_question(phase: str) -> Score:
    return Score(
        f"How urgent is it to give green to signal {PHASE_DESCRIPTIONS[phase]} at the target intersection for the "
        "next 30 seconds? 0 = no vehicles would benefit, 9 = extremely urgent (long queue, long waiting time, "
        "free downstream lanes).",
        0, 9, name=f"urgency_{phase}",
    )


SYSTEM_PROMPT ="You are a traffic signal control agent. You make fast, decisive signal timing decisions."


def load_task_info(data_root: str) -> dict:
    with open(os.path.join(data_root, "task_info.json")) as f:
        return json.load(f)


def raw_state(obs: Observation, i: int, task_info: dict) -> str:
    return "\n\n".join([
        task_info["task_description"],
        "Data schema:\n" + task_info["data_schema"],
        "Domain knowledge:\n" + task_info["domain_knowledge"],
        "Traffic data:\n" + obs.texts[i],
    ])


def _lane(obs: Observation, i: int, lane: str) -> dict:
    return obs.lanes[i].get(lane, {"queue_num": 0, "moving_num": 0, "occupancy": 0.0, "avg_wait_time": 0.0})


def downstream_occupancy(obs: Observation, i: int, lane: str) -> float | None:
    targets = obs.downstream[i].get(lane, [])
    if not targets:
        return None
    return sum(_lane(obs, j, l)["occupancy"] for j, l in targets) / len(targets)


def typed_state(obs: Observation, i: int) -> str:
    cur = obs.current_phase[i]
    lines = [
        f"Target intersection {i}. Current signal: {PHASES[cur] if cur >= 0 else 'yellow (switching)'}.",
        "Each signal gives green to two lanes. Per signal: queue = vehicles waiting, move = vehicles moving "
        "towards the stop line, wait = average waiting time of queued vehicles (minutes), "
        "downstream = average occupancy of the lanes the traffic will enter (high means spillback risk).",
        "",
    ]
    for p in PHASES:
        q = m = 0
        wait = 0.0
        ds = []
        for lane in PHASE_MOVEMENTS[p]:
            info = _lane(obs, i, lane)
            q += info["queue_num"]
            m += info["moving_num"]
            wait = max(wait, info["avg_wait_time"] / 60)
            occ = downstream_occupancy(obs, i, lane)
            if occ is not None:
                ds.append(occ)
        ds_text = f"{100 * sum(ds) / len(ds):.0f}%" if ds else "n/a (network boundary)"
        lanes = " + ".join(PHASE_MOVEMENTS[p])
        lines.append(f"- {p} ({lanes}): queue={q}, move={m}, wait={wait:.2f} min, downstream={ds_text}")
    right = sum(_lane(obs, i, l)["queue_num"] for l in ("NR", "SR", "ER", "WR"))
    lines.append(f"Right-turn lanes (always green): queue={right}.")
    return "\n".join(lines)


def render_state(obs: Observation, i: int, fmt: str, task_info: dict) -> str:
    if fmt == "raw":
        return raw_state(obs, i, task_info)
    if fmt == "typed":
        return typed_state(obs, i)
    raise ValueError(f"unknown state format {fmt!r}")
