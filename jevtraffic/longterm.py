"""Long-term memory per junction and the optional periodic (daily / weekly) fine-tuning policy.

LongTermMemory stores, per junction:
  decisions.jsonl  every Jev phase decision (state, allowed-phase options, Jev's choice and confidence, and the
                   local MaxPressure label; MaxPressure is computable on site from the same detectors);
  days.jsonl       one row per day: demand, ATT of the deployed model and of MaxPressure on the same day, agreement
                   with MaxPressure, mean confidence, which adapter was deployed, adaptation cost;
  adapters/        junction LoRA adapters (only if adaptation is on and a candidate was accepted).

AdaptationPolicy decides when to fine-tune a junction adapter on that junction's own records:
  off      never (one shared model, no per-junction parameters);
  daily    after every day;  weekly  after every 7th day;
  auto     weekly, but only while the shared model looks insufficient on this junction: if its agreement with
           MaxPressure is >= `agree_min` and its ATT is within `att_tol` of MaxPressure's over the last days,
           adaptation is skipped and no parameters are stored (the generalisation is good enough).
A candidate adapter is deployed only if it beats the current model on a re-perturbed replay of the last day.
"""
from __future__ import annotations

import json
import os


class LongTermMemory:
    def __init__(self, root: str, junction: str):
        self.dir = os.path.join(root, junction)
        os.makedirs(os.path.join(self.dir, "adapters"), exist_ok=True)
        self.decisions_path = os.path.join(self.dir, "decisions.jsonl")
        self.days_path = os.path.join(self.dir, "days.jsonl")

    def log_decisions(self, day: int, steps: list[dict]) -> int:
        n = 0
        with open(self.decisions_path, "a") as f:
            for s in steps:
                if "state" not in s:
                    continue  # forced by the min-green rule or an event plan: no decision to learn from
                label = s["phases"].index(s["mp_blocked"]) if s["mp_blocked"] in s["phases"] else None
                if label is None:
                    continue
                f.write(json.dumps({"kind": "phase", "day": day, "t": s["t"], "state": s["state"],
                                    "question": s["question"], "options": s["options"], "label": label,
                                    "jev": s["phases"].index(s["action"]) if s["action"] in s["phases"] else None,
                                    "conf": s.get("conf")}) + "\n")
                n += 1
        return n

    def log_day(self, row: dict) -> None:
        with open(self.days_path, "a") as f:
            f.write(json.dumps(row) + "\n")

    def days(self) -> list[dict]:
        if not os.path.exists(self.days_path):
            return []
        return [json.loads(l) for l in open(self.days_path)]

    def training_file(self, last_day: int, window: int) -> str:
        """Decisions of days (last_day - window, last_day] as a training file for train_lora.py."""
        out = os.path.join(self.dir, f"train_upto_day{last_day:03d}.jsonl")
        with open(out, "w") as f:
            for line in open(self.decisions_path):
                if last_day - window < json.loads(line)["day"] <= last_day:
                    f.write(line)
        return out

    def adapter_dir(self, day: int) -> str:
        return os.path.join(self.dir, "adapters", f"day{day:03d}")

    def storage_bytes(self) -> int:
        total = 0
        for root, _, files in os.walk(os.path.join(self.dir, "adapters")):
            total += sum(os.path.getsize(os.path.join(root, f)) for f in files)
        return total


class AdaptationPolicy:
    def __init__(self, mode: str = "off", window: int = 7, agree_min: float = 0.85, att_tol: float = 0.01,
                 lookback: int = 3):
        assert mode in ("off", "daily", "weekly", "auto")
        self.mode, self.window, self.agree_min, self.att_tol, self.lookback = mode, window, agree_min, att_tol, lookback

    def should_adapt(self, day: int, history: list[dict]) -> tuple[bool, str]:
        if self.mode == "off":
            return False, "off"
        if self.mode == "daily":
            return True, "daily"
        if day % 7 != 6:
            return False, "not end of week"
        if self.mode == "weekly":
            return True, "weekly"
        recent = history[-self.lookback:]
        if not recent:
            return False, "no history"
        agree = sum(r["agree_mp"] for r in recent) / len(recent)
        gap = sum(r["ATT"] / r["mp_ATT"] - 1 for r in recent) / len(recent)
        if agree >= self.agree_min and gap <= self.att_tol:
            return False, f"shared model sufficient (agree {agree:.2f}, ATT gap {gap:+.1%})"
        return True, f"shared model insufficient (agree {agree:.2f}, ATT gap {gap:+.1%})"
