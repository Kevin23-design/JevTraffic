"""Aggregate results/runs/*.json into results/summary.md (+ summary.csv): mean ± std over seeds."""
from __future__ import annotations

import glob
import json
import os
import statistics as st
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORDER = ["fixedtime", "random", "maxqueue", "maxpressure", "rollout-greedy"]
HELD_OUT = {"anon_4_4_hangzhou_real_5816", "anon_3_4_jinan_real_2500"}  # never used for fine-tuning


def fmt(xs):
    if not xs:
        return "-"
    m = st.mean(xs)
    return f"{m:.1f} ± {st.stdev(xs):.1f}" if len(xs) > 1 else f"{m:.1f}"


def main():
    runs = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(ROOT, "results", "runs", "*.json")))]
    groups = defaultdict(list)
    for r in runs:
        if r.get("decisions", 0) < 120:
            continue
        label = r["agent"] + (f"-perm{r['permutations']}" if r.get("permutations", 1) > 1 else "")
        label += f" T={r['temperature']:.2f}" if r.get("adapters") and r.get("temperature", 1.0) != 1.0 else ""
        label += f" [{r['model']}]" if r.get("model") else ""
        groups[(r["dataset"], r["traffic_file"].removesuffix(".json"), label)].append(r)

    def sort_key(k):
        agent = k[2].split(" ")[0]
        return (k[0], k[1], ORDER.index(agent) if agent in ORDER else len(ORDER), k[2])

    lines = ["| dataset | traffic | controller | seeds | ATT (s) | AWT (s) | AQL | ms / decision | extra |",
             "|---|---|---|---|---|---|---|---|---|"]
    csv = ["dataset,traffic,controller,seeds,ATT,AWT,AQL,ms_per_decision"]
    for key in sorted(groups, key=sort_key):
        rs = groups[key]
        summ = [r.get("agent_summary", {}) for r in rs]
        lat = [s["latency_per_decision_ms"] for s in summ if "latency_per_decision_ms" in s]
        extra = []
        for k, name in [("agreement_with_maxpressure", "agree-MP"), ("fallback_rate", "fallback"),
                        ("mean_confidence", "conf"), ("invalid_rate", "invalid"), ("gen_tokens_per_decision", "gen-tok")]:
            vals = [s[k] for s in summ if k in s]
            if vals:
                extra.append(f"{name}={st.mean(vals):.2f}" if k != "gen_tokens_per_decision" else f"{name}={st.mean(vals):.0f}")
        att, awt, aql = ([r[m] for r in rs] for m in ("ATT", "AWT", "AQL"))
        traffic = key[1] + (" (held-out)" if key[1] in HELD_OUT else "")
        lines.append(f"| {key[0]} | {traffic} | {key[2]} | {len(rs)} | {fmt(att)} | {fmt(awt)} | {fmt(aql)} | "
                     f"{fmt(lat) if lat else '-'} | {', '.join(extra)} |")
        csv.append(f"{key[0]},{key[1]},{key[2]},{len(rs)},{st.mean(att):.2f},{st.mean(awt):.2f},{st.mean(aql):.2f},"
                   f"{st.mean(lat) if lat else ''}")
    table = "\n".join(lines)
    with open(os.path.join(ROOT, "results", "summary.md"), "w") as f:
        f.write(table + "\n")
    with open(os.path.join(ROOT, "results", "summary.csv"), "w") as f:
        f.write("\n".join(csv) + "\n")
    print(table)


if __name__ == "__main__":
    main()
