"""Aggregate results/sumo/runs/*.json (and results/sumo/days/*.json) into results/sumo/summary.md.

Scenario groups (generalisation):
  seen        train junctions x the 4 training patterns
  pattern     train junctions x held-out pattern random_perturbation
  junction    held-out junctions (France_Massy, SouthKorea_Songdo, Hongkong_YMT) x all patterns
ATT ratios are per scenario (same junction / env / events / seed) relative to the benchmark MaxPressure, then averaged.
"""
from __future__ import annotations

import glob
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jevtraffic.sumo_env import HELDOUT_JUNCTIONS, HELDOUT_PATTERN  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNS = os.path.join(ROOT, "results", "sumo", "runs")
GROUPS = ["seen", "pattern", "junction"]


def group(r) -> str:
    if r["junction"] in HELDOUT_JUNCTIONS:
        return "junction"
    return "pattern" if r["env_name"].endswith(HELDOUT_PATTERN) else "seen"


def ev_kind(e: str) -> str:
    return "none" if e == "none" else ("event_1" if e == "event_1" else "random")


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def fmt(x, d=1, pct=False):
    if x is None:
        return "-"
    return f"{100 * x:+.1f}%" if pct else f"{x:.{d}f}"


def load_runs():
    return [json.load(open(f)) for f in sorted(glob.glob(os.path.join(RUNS, "*.json")))]


def ratio_table(runs, agents, events_kind, title):
    agents = list(dict.fromkeys(agents))
    ref = {}  # benchmark MaxPressure in the same scenario; our identical "mp" where the benchmark was not run
    for a in ("mp", "maxpressure"):
        ref.update({(r["junction"], r["env_name"], r["events"], r["seed"]): r["metrics"]["ATT"] for r in runs
                    if r["agent"] == a and r["metrics"].get("ATT")})
    cell = defaultdict(list)
    att = defaultdict(list)
    for r in runs:
        if r["agent"] not in agents or ev_kind(r["events"]) != events_kind or not r["metrics"].get("ATT"):
            continue
        base = ref.get((r["junction"], r["env_name"], r["events"], r["seed"]))
        g = group(r)
        att[(r["agent"], g)].append(r["metrics"]["ATT"])
        if base:
            cell[(r["agent"], g)].append(r["metrics"]["ATT"] / base - 1)
    lines = [f"### {title}", "", "| controller | " + " | ".join(f"{g}: ATT / vs MP" for g in GROUPS) + " | runs |",
             "|---|" + "---|" * (len(GROUPS) + 1)]
    for a in agents:
        n = sum(len(att[(a, g)]) for g in GROUPS)
        if not n:
            continue
        cols = [f"{fmt(mean(att[(a, g)]))} / {fmt(mean(cell[(a, g)]), pct=True)}" for g in GROUPS]
        lines.append(f"| {a} | " + " | ".join(cols) + f" | {n} |")
    return lines + [""]


def per_junction_table(runs, agents):
    att = defaultdict(list)
    for r in runs:
        if r["agent"] in agents and r["events"] == "none" and r["metrics"].get("ATT"):
            att[(r["junction"], r["agent"])].append(r["metrics"]["ATT"])
    js = sorted({j for j, _ in att}, key=lambda j: (j in HELDOUT_JUNCTIONS, j))
    present = [a for a in agents if any((j, a) in att for j in js)]
    lines = ["### ATT per junction (mean over 10 envs x seeds, no events)", "",
             "| junction | " + " | ".join(present) + " |", "|---|" + "---|" * len(present)]
    for j in js:
        vals = {a: mean(att[(j, a)]) for a in present}
        best = min(v for v in vals.values() if v is not None)
        cells = [("**" + fmt(vals[a]) + "**") if vals[a] == best else fmt(vals[a]) for a in present]
        lines.append(f"| {j}{' (held-out)' if j in HELDOUT_JUNCTIONS else ''} | " + " | ".join(cells) + " |")
    return lines + [""]


def context_table(runs, agents):
    rows = defaultdict(list)
    for r in runs:
        if r["agent"] in agents:
            rows[(r["agent"], ev_kind(r["events"]))].append(r)
    lines = ["### Context agent cost (all scenarios)", "",
             "| controller | events | runs | ATT | extra calls / step | model calls / step | ms / step | ms / call |",
             "|---|---|---|---|---|---|---|---|"]
    for (a, e), rs in sorted(rows.items()):
        s = [r["summary"] for r in rs]
        lines.append(f"| {a} | {e} | {len(rs)} | {fmt(mean([r['metrics']['ATT'] for r in rs]))} | "
                     f"{fmt(mean([x['context']['extra_call_rate'] for x in s]), 3)} | "
                     f"{fmt(mean([x.get('calls_per_step') for x in s]), 3)} | {fmt(mean([x.get('ms_per_step') for x in s]))} | "
                     f"{fmt(mean([x.get('ms_per_call') for x in s]))} |")
    return lines + [""]


def detection_table(runs, agents):
    rows = defaultdict(list)
    for r in runs:
        if r["agent"] in agents and r["events"] != "none":
            rows[(r["agent"], ev_kind(r["events"]))].append(r)
    lines = ["### Special events (sums over runs; latency in s; special-vehicle metrics over their trips)", "",
             "| controller | events | runs | ATT | special ATT | special timeLoss | special detected | latency | "
             "blockages detected | observable detected | latency | false alarms |", "|---|" + "---|" * 11]
    for (a, e), rs in sorted(rows.items()):
        d = [r.get("detection") or {} for r in rs]
        m = [r["metrics"] for r in rs]
        se, sd = sum(x.get("special_events", 0) for x in d), sum(x.get("special_detected", 0) for x in d)
        be, bd = sum(x.get("blockage_events", 0) for x in d), sum(x.get("blockage_detected", 0) for x in d)
        fa = sum(x.get("blockage_false_alarms", 0) for x in d)
        oe, od = sum(x.get("blockage_observable", 0) for x in d), sum(x.get("blockage_observable_detected", 0) for x in d)
        det = bool(d[0])
        lines.append(
            f"| {a} | {e} | {len(rs)} | {fmt(mean([x['ATT'] for x in m]))} | {fmt(mean([x.get('special_ATT') for x in m]))} | "
            f"{fmt(mean([x.get('special_timeLoss') for x in m]))} | "
            f"{f'{sd}/{se}' if det else '-'} | {fmt(mean([x.get('special_latency') for x in d]))} | "
            f"{f'{bd}/{be}' if det else '-'} | {f'{od}/{oe}' if det else '-'} | "
            f"{fmt(mean([x.get('blockage_latency') for x in d]))} | "
            f"{fa if det else '-'} |")
    return lines + [""]


def family(agent: str) -> str:
    """unitsa[ft_<J>] / unitsa[scratch_<J>] -> one row per kind of per-junction UniTSA model."""
    for kind in ("ft", "scratch"):
        if agent.startswith(f"unitsa[{kind}_"):
            return f"unitsa[{kind}]"
    return agent


def vs_unitsa_table(runs, ref_agent="unitsa[universal]"):
    """v3: ATT relative to the universal UniTSA on matched scenarios (junction, env, events, seed)."""
    ref = {(r["junction"], r["env_name"], r["events"], r["seed"]): r["metrics"]["ATT"] for r in runs
           if r["agent"] == ref_agent and r["metrics"].get("ATT")}
    cell = defaultdict(list)
    agree, ms = defaultdict(list), defaultdict(list)
    for r in runs:
        a = family(r["agent"])
        base = ref.get((r["junction"], r["env_name"], r["events"], r["seed"]))
        if a == ref_agent or not base or not r["metrics"].get("ATT"):
            continue
        cell[(a, group(r), ev_kind(r["events"]))].append(r["metrics"]["ATT"] / base - 1)
        s = r.get("summary") or {}
        if s.get("agree_teacher") is not None:
            agree[a].append(s["agree_teacher"])
        if s.get("ms_per_call") is not None:
            ms[a].append(s["ms_per_call"])
    agents = sorted({a for a, _, _ in cell}, key=lambda a: (not a.startswith(("mp", "maxpressure", "unitsa")), a))
    cols = [(g, e) for e in ("none", "event_1", "random") for g in GROUPS]
    lines = [f"### ATT vs {ref_agent} on matched scenarios (negative = better than UniTSA)", "",
             "| controller | " + " | ".join(f"{e}: {g}" for g, e in cols) + " | agree UniTSA | ms / call |",
             "|---|" + "---|" * (len(cols) + 2)]
    for a in agents:
        vals = [cell[(a, g, e)] for g, e in cols]
        if not any(vals):
            continue
        lines.append(f"| {a} | " + " | ".join(f"{fmt(mean(v), pct=True)} ({len(v)})" if v else "-" for v in vals)
                     + f" | {fmt(mean(agree[a]), 3)} | {fmt(mean(ms[a]))} |")
    return lines + [""]


def days_table():
    files = sorted(glob.glob(os.path.join(ROOT, "results", "sumo", "days", "*.json")))
    if not files:
        return []
    lines = ["### Long-term adaptation over simulated days", "",
             "| junction | policy | days | ATT | MP ATT | vs MP (all days) | vs MP (week 2) | agree MP | adaptations "
             "(accepted) | train s | storage MB |", "|---|" + "---|" * 10]
    for f in files:
        d = json.load(open(f))
        rows = d["days"]
        gap = [r["ATT"] / r["mp_ATT"] - 1 for r in rows]
        w2 = gap[7:] or gap
        ad = [r for r in rows if r.get("adapted")]
        lines.append(f"| {d['junction']} | {d['adapt']} | {len(rows)} | {fmt(mean([r['ATT'] for r in rows]))} | "
                     f"{fmt(mean([r['mp_ATT'] for r in rows]))} | {fmt(mean(gap), pct=True)} | {fmt(mean(w2), pct=True)} | "
                     f"{fmt(mean([r['agree_mp'] for r in rows]), 3)} | {len(ad)} ({sum(r['accepted'] for r in ad)}) | "
                     f"{fmt(sum(r['train_s'] for r in ad), 0)} | {rows[-1]['storage_MB']} |")
    return lines + [""]


def main():
    runs = load_runs()
    agents = sorted({r["agent"] for r in runs})
    bench = [a for a in ["fixtime", "webster", "sotl", "maxpressure", "mp"] if a in agents]
    jev = [a for a in agents if a.startswith("jev")]
    uni = [a for a in agents if a == "unitsa[universal]"]  # per-junction UniTSA models: see vs_unitsa_table
    plain = bench + uni + [a for a in jev if "-" not in a.split("[")[0]]
    ctx = [a for a in agents if a.startswith(("mp-", "jev-"))]
    out = ["# SingleTSCBaselines results (v2)", "", f"{len(runs)} runs. Groups: " + ", ".join(GROUPS) +
           " (see scripts/analyze_sumo.py).", ""]
    out += ratio_table(runs, plain, "none", "E1/E2: no events")
    out += ratio_table(runs, bench + ["mp", "mp-triggered-rule"] + uni + jev, "event_1", "Official event_1")
    out += ratio_table(runs, ["mp", "mp-triggered-rule"] + uni + jev, "random", "Random events (1 accident set + 1-3 special vehicles)")
    out += per_junction_table(runs, plain)
    out += context_table(runs, ctx + [a for a in jev if a not in ctx])
    out += detection_table(runs, ["mp", "mp-triggered-rule"] + uni + jev)
    if "unitsa[universal]" in agents:
        out += vs_unitsa_table(runs)
    out += days_table()
    path = os.path.join(ROOT, "results", "sumo", "summary.md")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w").write("\n".join(out))
    print("\n".join(out))


if __name__ == "__main__":
    main()
