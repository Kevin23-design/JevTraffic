"""Thin wrapper around the USTBench traffic-signal-control environment (CityFlow).

We reuse USTBench's `TrafficSignalEnvironment` for the simulator, the per-lane observation and the
observation text, so states and metrics (ATT / AWT / AQL) are computed exactly as in the benchmark.
What we replace is the agent loop: USTBench hard-wires its generative LLM pipeline into `env.step`,
here any controller returns one phase index per intersection.

Phase indices follow the roadnet's `lightphases` (checked against roadnet_4_4.json / roadnet_3_4.json):
    0 = ETWT (east/west through), 1 = NTST (north/south through),
    2 = ELWL (east/west left),    3 = NLSL (north/south left).
Note: USTBench's `_selection_to_signal_code` uses ['ETWT', 'ELWL', 'NTST', 'NLSL'], which swaps
ELWL and NTST relative to the roadnet. We use the roadnet order.
"""
from __future__ import annotations

import contextlib
import io
import os
import random
import re
import sys
import time
from dataclasses import dataclass, field

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USTBENCH_DIR = os.environ.get("USTBENCH_DIR", os.path.join(ROOT, "third_party", "USTBench"))
if USTBENCH_DIR not in sys.path:
    sys.path.insert(0, USTBENCH_DIR)

PHASES = ["ETWT", "NTST", "ELWL", "NLSL"]
PHASE_MOVEMENTS = {"ETWT": ("ET", "WT"), "NTST": ("NT", "ST"), "ELWL": ("EL", "WL"), "NLSL": ("NL", "SL")}
LANES = ["NT", "NL", "NR", "ST", "SL", "SR", "ET", "EL", "ER", "WT", "WL", "WR"]

DATASETS = {
    "hangzhou": dict(template="Hangzhou", road_net="4_4",
                     traffic_files=["anon_4_4_hangzhou_real.json", "anon_4_4_hangzhou_real_5816.json"]),
    "jinan": dict(template="Jinan", road_net="3_4",
                  traffic_files=["anon_3_4_jinan_real.json", "anon_3_4_jinan_real_2000.json",
                                 "anon_3_4_jinan_real_2500.json"]),
}


@dataclass
class Observation:
    texts: list[str]                     # USTBench observation text per intersection (the benchmark's LLM input)
    lanes: list[dict]                    # per intersection: lane -> {queue_num, moving_num, occupancy, avg_wait_time}
    downstream: list[dict]               # per intersection: lane -> [(neighbor_id, lane), ...]
    current_phase: list[int]             # per intersection: 0..3, or -1 during yellow
    time: float = 0.0
    extra: dict = field(default_factory=dict)

    @property
    def n(self) -> int:
        return len(self.lanes)


_EDGE = re.compile(r"^(\w+) of (\d+)$")


class TSCEnv:
    """USTBench TSC environment driven by an external controller.

    Args mirror USTBench's `traffic_signal_control/main.py` (MIN_ACTION_TIME=30s, YELLOW_TIME=5s,
    RUN_COUNTS=3600s -> 120 decisions per episode, 4-phase action space).
    """

    def __init__(self, dataset: str, traffic_file: str, work_dir: str, seed: int = 0,
                 data_root: str | None = None, run_counts: int = 3600, quiet: bool = True):
        from UST_tasks.traffic_signal_control.env import TrafficSignalEnvironment
        from UST_tasks.traffic_signal_control.env_utils import dic_traffic_env_conf, merge

        cfg = DATASETS[dataset]
        if traffic_file not in cfg["traffic_files"]:
            raise ValueError(f"{traffic_file} is not a {dataset} traffic file: {cfg['traffic_files']}")
        rows, cols = map(int, cfg["road_net"].split("_"))
        data_root = data_root or os.path.join(ROOT, "data", "tsc")
        self.quiet = quiet
        self.seed = seed
        np.random.seed(seed)  # CityFlowEnv.reset draws the engine seed from np.random
        random.seed(seed)

        env_conf = merge(dic_traffic_env_conf, {
            "NUM_AGENTS": rows * cols, "NUM_INTERSECTIONS": rows * cols, "RUN_COUNTS": run_counts,
            "NUM_ROUNDS": 1, "NUM_ROW": rows, "NUM_COL": cols, "TRAFFIC_FILE": traffic_file,
            "ROADNET_FILE": f"roadnet_{cfg['road_net']}.json", "MODEL_NAME": "JevTraffic",
            "LIST_STATE_FEATURE": ["cur_phase", "traffic_movement_pressure_queue"],
            "DIC_REWARD_INFO": {"queue_length": -0.25},
        })
        work_dir = os.path.abspath(work_dir)
        dic_path = {"PATH_TO_MODEL": os.path.join(work_dir, "model"),
                    "PATH_TO_WORK_DIRECTORY": os.path.join(work_dir, "sim"),
                    "PATH_TO_DATA": os.path.join(data_root, cfg["template"], cfg["road_net"])}
        with self._silence():
            self.inner = TrafficSignalEnvironment(dic_path=dic_path, dic_agent_conf={"FIXED_TIME": [30] * 4},
                                                  dic_traffic_env_conf=env_conf)
        self.end_step = self.inner.end_step
        self.step_count = 0
        self.sim_seconds = 0.0  # wall-clock spent inside the simulator

    @contextlib.contextmanager
    def _silence(self):
        if not self.quiet:
            yield
            return
        with contextlib.redirect_stdout(io.StringIO()):
            yield

    @property
    def num_intersections(self) -> int:
        return len(self.inner.env.list_intersection)

    @property
    def done(self) -> bool:
        return self.step_count >= self.end_step

    def observe(self) -> Observation:
        inner = self.inner
        feats = inner._get_observation()
        texts = inner._observations_to_text(feats)
        downstream = []
        for i in range(self.num_intersections):
            ds: dict[str, list] = {lane: [] for lane in LANES}
            for src, dst, _ in inner._get_connectivity_of_inter(i)["edges"]:
                ms, md = _EDGE.match(src), _EDGE.match(dst)
                if ms and md and int(ms.group(2)) == i:
                    ds[ms.group(1)].append((int(md.group(2)), md.group(1)))
            downstream.append(ds)
        phases = [inter.current_phase_index - 1 if inter.current_phase_index > 0 else -1
                  for inter in inner.env.list_intersection]
        return Observation(texts=texts, lanes=feats["traffic_conditions"], downstream=downstream,
                           current_phase=phases, time=inner.env.get_current_time())

    def step(self, actions: list[int]) -> None:
        if len(actions) != self.num_intersections:
            raise ValueError(f"expected {self.num_intersections} actions, got {len(actions)}")
        actions = [int(a) if 0 <= int(a) < len(PHASES) else 0 for a in actions]
        t0 = time.time()
        with self._silence():
            next_states, _, _, _ = self.inner.env.step(actions)
            self.inner.current_states, _ = self.inner._process_state(next_states)
            self.inner._update_metrics()
        self.sim_seconds += time.time() - t0
        self.step_count += 1

    def rollout_costs(self, horizon: int | None = None) -> list[list[float]]:
        """Counterfactual cost of each phase at each intersection, from short simulator rollouts.

        For phase k, snapshot the engine, set phase k at every intersection (with the 5 s yellow when it
        differs from the current phase, as the env does), run `horizon` seconds (default: one action
        interval) and accumulate vehicle-seconds of waiting on that intersection's entering lanes; then
        restore the snapshot. Intersections are scored together in one rollout per phase: within 30 s,
        vehicles released by a neighbour have not yet reached the target's stop line (links are 600-800 m),
        so the cost is driven by the intersection's own phase. Returns costs[intersection][phase].
        """
        conf = self.inner.dic_traffic_env_conf
        horizon = horizon or conf["MIN_ACTION_TIME"]
        yellow = conf["YELLOW_TIME"]
        env = self.inner.env
        eng = env.eng
        inters = env.list_intersection
        entering = [inter.list_entering_lanes for inter in inters]
        costs = [[0.0] * len(PHASES) for _ in inters]
        t0 = time.time()
        snap = eng.snapshot()
        for k in range(len(PHASES)):
            if k:
                eng.load(snap)
            switching = [inter.current_phase_index != k + 1 for inter in inters]
            for inter, sw in zip(inters, switching):
                eng.set_tl_phase(inter.inter_name, 0 if sw else k + 1)
            for s in range(horizon):
                if s == yellow:
                    for inter, sw in zip(inters, switching):
                        if sw:
                            eng.set_tl_phase(inter.inter_name, k + 1)
                eng.next_step()
                counts = eng.get_lane_waiting_vehicle_count()
                for i, lanes in enumerate(entering):
                    costs[i][k] += sum(counts.get(l, 0) for l in lanes)
        eng.load(snap)
        self.sim_seconds += time.time() - t0
        return costs

    def metrics(self) -> dict:
        att, awt, aql = self.inner.get_metrics()
        return {"ATT": float(att), "AWT": float(awt), "AQL": float(aql)}
