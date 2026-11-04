"""Simulated days and weeks for long-term memory / periodic adaptation.

SingleTSCBaselines has one 1000 s route file per demand pattern, not multi-day data. A "day" here is one
episode whose route file is derived from the junction's pattern files:
  * the weekly schedule picks the pattern (weekdays commuter-like, a heavy mid-week day, weekend lighter);
  * a seeded per-day demand scale, vehicle thinning / duplication and departure jitter make every day differ,
    while the same (junction, day) is always the same day.
"""
from __future__ import annotations

import copy
import os
import random
import xml.etree.ElementTree as ET

from .sumo_env import scenario_paths

WEEK = ["fluctuating_commuter", "fluctuating_commuter", "high_density", "fluctuating_commuter",
        "increasing_demand", "random_perturbation", "low_density"]  # Mon..Sun
SCALE = {"weekday": (0.9, 1.15), "weekend": (0.75, 0.95)}


def day_pattern(day: int) -> str:
    return WEEK[day % 7]


def make_day(junction: str, net: str, day: int, out_dir: str, num_seconds: int = 1000, jitter: float = 30.0,
             seed: int = 0) -> dict:
    """Write the route file of `day` and return {env_name, route_file, pattern, scale}."""
    pattern = day_pattern(day)
    env_name = f"{net}_{pattern}"
    rng = random.Random(f"{junction}|{net}|{day}|{seed}")
    lo, hi = SCALE["weekend" if day % 7 >= 5 else "weekday"]
    scale = rng.uniform(lo, hi)
    src = scenario_paths(junction, env_name)["route_file"]
    tree = ET.parse(src)
    root = tree.getroot()
    vehicles = [v for v in root if v.tag == "vehicle"]
    for v in vehicles:
        root.remove(v)
    out = []
    for v in vehicles:
        copies = int(scale) + (1 if rng.random() < scale - int(scale) else 0)
        for c in range(copies):
            w = copy.deepcopy(v) if c else v
            dep = float(v.get("depart")) + rng.uniform(-jitter, jitter) + (rng.uniform(0, 5) if c else 0)
            w.set("depart", f"{min(max(dep, 0.0), num_seconds - 1):.2f}")
            if c:
                w.set("id", f'{v.get("id")}__d{c}')
            out.append(w)
    out.sort(key=lambda v: float(v.get("depart")))  # SUMO needs departures in order
    for v in out:
        root.append(v)
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{junction}_{net}_day{day:03d}.rou.xml")
    tree.write(path, encoding="utf-8", xml_declaration=True)
    return {"day": day, "env_name": env_name, "route_file": path, "pattern": pattern, "scale": round(scale, 3),
            "vehicles": len(out)}
