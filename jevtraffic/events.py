"""Special events: detection result -> notification + special signal plan.

Detection is a typed situation question (Jev, calibrated probabilities) or, as a baseline, the trigger rule
itself. Plans are deterministic, because they are safety-relevant:

  * special vehicle (fire engine > ambulance > police, then nearest first): signal preemption. The phase that
    serves the vehicle's movement gets the green whenever the min-green rule allows, until the vehicle has left
    the incoming lane or `max_hold` decisions have passed. Then normal control resumes.
  * blockage: the stalled lanes are marked blocked. The controller no longer sees their queue (Jev's state
    shows them as blocked, MaxPressure ignores them), so green is not wasted on traffic that cannot move.
    The mark is cleared when the lane discharges again or after `blockage_ttl` seconds without confirmation.

Every activation / clearance is a structured notification (JSON lines), e.g. for a traffic management centre.
"""
from __future__ import annotations

import json
import os

from .memory import Trigger
from .sumo_env import SumoObs

PRIORITY = {"fire_engine": 0, "ambulance": 1, "police": 2}


class Notifier:
    def __init__(self, path: str | None = None, junction: str = ""):
        self.path, self.junction = path, junction
        self.events: list[dict] = []
        if path:
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            open(path, "w").close()

    def send(self, time: float, kind: str, action: str, confidence: float | None = None, **where) -> dict:
        ev = {"time": round(time, 1), "junction": self.junction, "type": kind, "action": action,
              "confidence": None if confidence is None else round(confidence, 3), **where}
        self.events.append(ev)
        if self.path:
            with open(self.path, "a") as f:
                f.write(json.dumps(ev) + "\n")
        return ev


class EventManager:
    def __init__(self, notifier: Notifier, tau: float = 0.5, max_hold: int = 6, blockage_ttl: float = 120.0):
        self.notifier = notifier
        self.tau = tau
        self.max_hold = max_hold
        self.blockage_ttl = blockage_ttl
        self.preempt: dict[str, dict] = {}   # vehicle id -> {kind, held}
        self.blocked: dict[str, dict] = {}   # lane -> {since, confirmed}
        self.stats = {"preemptions": 0, "blockages": 0, "dismissed": 0}

    # ---------------------------------------------------------------- detection result
    def on_situation(self, obs: SumoObs, trigger: list[Trigger], label: str, confidence: float, source: str) -> None:
        if confidence < self.tau or label == "normal":
            self.stats["dismissed"] += 1  # triggered, but judged normal (or unsure): keep normal control
            return
        if label in PRIORITY:
            seen = {v for t in trigger for v in t.vehicles} or {s["id"] for s in obs.special}
            for s in obs.special:
                if s["id"] in seen and s["id"] not in self.preempt:
                    self.preempt[s["id"]] = {"kind": s["kind"], "held": 0, "label": label}
                    self.stats["preemptions"] += 1
                    m = obs.movements[s["movement"]]
                    self.notifier.send(obs.time, s["kind"], "preemption_start", confidence, source=source,
                                       vehicle=s["id"], movement=f"{m.approach} {m.turn}", lanes=m.lanes,
                                       dist=s["dist"], jev_label=label)
        elif label == "blockage":
            lanes = [l for t in trigger for l in t.lanes] or self._stall_candidates(obs)
            for lane in lanes:
                if lane not in self.blocked:
                    self.blocked[lane] = {"since": obs.time, "confirmed": obs.time}
                    self.stats["blockages"] += 1
                    self.notifier.send(obs.time, "blockage", "lane_excluded", confidence, source=source, lane=lane,
                                       halting=obs.lane_halting.get(lane))
                else:
                    self.blocked[lane]["confirmed"] = obs.time

    @staticmethod
    def _stall_candidates(obs: SumoObs) -> list[str]:
        cands = [l for l, ph in obs.lane_phases.items() if obs.current_phase in ph and obs.lane_halting.get(l, 0) >= 2
                 and obs.lane_discharged.get(l, 0) == 0]
        return cands[:2]

    # ---------------------------------------------------------------- every step
    def update(self, obs: SumoObs) -> None:
        present = {s["id"] for s in obs.special}
        for vid in list(self.preempt):
            p = self.preempt[vid]
            if vid not in present or p["held"] >= self.max_hold:
                self.notifier.send(obs.time, p["kind"], "preemption_end", vehicle=vid,
                                   reason="passed" if vid not in present else "max_hold")
                del self.preempt[vid]
        for lane in list(self.blocked):
            b = self.blocked[lane]
            green = obs.current_phase in obs.lane_phases.get(lane, [])
            if (green and obs.lane_discharged.get(lane, 0) > 0) or obs.time - b["confirmed"] > self.blockage_ttl:
                self.notifier.send(obs.time, "blockage", "lane_restored", lane=lane,
                                   reason="discharging" if green and obs.lane_discharged.get(lane, 0) > 0 else "ttl")
                del self.blocked[lane]

    def override(self, obs: SumoObs) -> int | None:
        """Preemption action, if a special vehicle is being served and the safety layer allows it."""
        live = [s for s in obs.special if s["id"] in self.preempt and s["phase"] is not None]
        if not live:
            return None
        live.sort(key=lambda s: (PRIORITY.get(s["kind"], 9), s["dist"]))
        target = live[0]
        self.preempt[target["id"]]["held"] += 1
        return target["phase"] if target["phase"] in obs.allowed else None

    def blocked_lanes(self) -> set[str]:
        return set(self.blocked)


def rule_situation(obs: SumoObs, triggers: list[Trigger]) -> tuple[str, float]:
    """Baseline detector: believe the triggers (special vehicle -> its type, stall -> blockage)."""
    vids = {v for t in triggers for v in t.vehicles}
    specials = [s for s in obs.special if s["id"] in vids] or (obs.special if triggers else [])
    if specials:
        best = min(specials, key=lambda s: (PRIORITY.get(s["kind"], 9), s["dist"]))
        return best["kind"], 1.0
    if any(t.kind == "stall" for t in triggers):
        return "blockage", 1.0
    return "normal", 1.0
