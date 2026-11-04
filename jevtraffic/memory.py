"""Short-term traffic context, managed outside Jev.

Jev answers one typed question from one state in one forward pass; it has no conversation and is not good at
long context. So the context lives here, in a small rule-based agent that runs every step at O(1) cost and
involves Jev only when something looks off:

  * `ShortTermMemory` keeps the last K decisions (per-movement / per-lane queue and discharge, green phase,
    Jev's confidence).
  * `ContextAgent.triggers` checks cheap numeric triggers every step:
      - v2x:     a special vehicle (not yet assessed) is reported on an incoming lane;
      - stall:   an incoming lane served by the green for >= `stall_steps` decisions keeps a queue but
                 discharges nothing (the signature of a blockage);
      - lowconf: Jev's phase decision was unsure for `lowconf_steps` decisions in a row.
    Each trigger kind has a cooldown, and there is a global budget on the fraction of steps with an extra call.
  * Only then is Jev asked the situation question, with the history rendered as a compact table.

mode = "none" (no context, no events), "always" (situation question at every step), "triggered" (ours).
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from .sumo_env import SumoObs


@dataclass
class Snapshot:
    time: float
    phase: int
    queues: list[float]
    discharged: list[float]
    lane_halting: dict
    lane_discharged: dict
    confidence: float | None = None


class ShortTermMemory:
    def __init__(self, k: int = 5):
        self.k = k
        self.buf: deque[Snapshot] = deque(maxlen=k)

    def push(self, obs: SumoObs, confidence: float | None = None) -> None:
        self.buf.append(Snapshot(obs.time, obs.current_phase, [m.queue for m in obs.movements], list(obs.discharged),
                                 dict(obs.lane_halting), dict(obs.lane_discharged), confidence))

    def set_confidence(self, confidence: float) -> None:
        if self.buf:
            self.buf[-1].confidence = confidence

    def items(self) -> list[Snapshot]:
        return list(self.buf)

    def __len__(self) -> int:
        return len(self.buf)


@dataclass
class TriggerConfig:
    stall_steps: int = 2          # consecutive green decisions without discharge
    stall_min_queue: float = 2    # halting vehicles on the lane at each of those decisions
    lowconf: float = 0.5
    lowconf_steps: int = 2
    cooldown: float = 30.0        # s, per trigger kind (v2x is per vehicle instead)
    budget: float = 0.25          # max fraction of steps with an extra (situation) call


@dataclass
class Trigger:
    kind: str                     # v2x / stall / lowconf / always
    lanes: list[str] = field(default_factory=list)
    vehicles: list[str] = field(default_factory=list)


class ContextAgent:
    def __init__(self, mode: str = "triggered", k: int = 5, config: TriggerConfig | None = None):
        assert mode in ("none", "always", "triggered")
        self.mode = mode
        self.memory = ShortTermMemory(k)
        self.cfg = config or TriggerConfig()
        self.last_fired: dict[str, float] = {}
        self.assessed_vehicles: set[str] = set()
        self.steps = 0
        self.calls = 0
        self.fired: dict[str, int] = {}

    def observe(self, obs: SumoObs) -> None:
        self.memory.push(obs)
        self.steps += 1

    def _stalled_lanes(self, obs: SumoObs) -> list[str]:
        hist = self.memory.items()[-self.cfg.stall_steps:]
        if len(hist) < self.cfg.stall_steps or any(h.phase != obs.current_phase for h in hist):
            return []
        if obs.green_steps < self.cfg.stall_steps:
            return []
        out = []
        for lane, phases in obs.lane_phases.items():
            if obs.current_phase not in phases:
                continue
            if all(h.lane_halting.get(lane, 0) >= self.cfg.stall_min_queue and h.lane_discharged.get(lane, 0) == 0
                   for h in hist):
                out.append(lane)
        return out

    def triggers(self, obs: SumoObs) -> list[Trigger]:
        """Cheap checks, every step. Returns the triggers that fired (after cooldown and budget)."""
        if self.mode == "none":
            return []
        if self.mode == "always":
            self.calls += 1
            return [Trigger("always", vehicles=[s["id"] for s in obs.special])]
        out = []
        new = [s["id"] for s in obs.special if s["id"] not in self.assessed_vehicles]
        if new:
            out.append(Trigger("v2x", vehicles=new))
        stalled = self._stalled_lanes(obs)
        if stalled and self._cool("stall", obs.time):
            out.append(Trigger("stall", lanes=stalled))
        conf = [h.confidence for h in self.memory.items()[-self.cfg.lowconf_steps:]]
        if (len(conf) == self.cfg.lowconf_steps and all(c is not None and c < self.cfg.lowconf for c in conf)
                and self._cool("lowconf", obs.time)):
            out.append(Trigger("lowconf"))
        if out and self.calls >= self.cfg.budget * max(self.steps, 1) and not new:
            return []  # over budget; special vehicles are always assessed
        if out:
            self.calls += 1
            for t in out:
                self.last_fired[t.kind] = obs.time
                self.fired[t.kind] = self.fired.get(t.kind, 0) + 1
            self.assessed_vehicles.update(new)
        return out

    def _cool(self, kind: str, t: float) -> bool:
        return t - self.last_fired.get(kind, -1e9) >= self.cfg.cooldown

    def summary(self) -> dict:
        return {"mode": self.mode, "steps": self.steps, "extra_calls": self.calls,
                "extra_call_rate": round(self.calls / max(self.steps, 1), 4), "fired": dict(self.fired)}
