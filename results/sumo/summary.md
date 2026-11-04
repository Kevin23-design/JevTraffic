# SingleTSCBaselines results (v2)

12600 runs. Groups: seen, pattern, junction (see scripts/analyze_sumo.py).

### E1/E2: no events

| controller | seen: ATT / vs MP | pattern: ATT / vs MP | junction: ATT / vs MP | runs |
|---|---|---|---|---|
| fixtime | 41.6 / +7.9% | 42.1 / +8.5% | 52.5 / +0.3% | 360 |
| webster | 48.5 / +26.0% | 48.8 / +25.9% | 59.7 / +16.3% | 360 |
| sotl | 74.6 / +90.3% | 74.2 / +89.7% | 97.4 / +86.0% | 360 |
| maxpressure | 39.2 / +0.0% | 39.2 / +0.0% | 53.9 / +0.0% | 360 |
| unitsa[universal] | 38.0 / -1.9% | 38.5 / -0.8% | 50.1 / -5.1% | 360 |
| jev[Qwen2.5-7B-Instruct] | 45.8 / +16.5% | 48.4 / +23.7% | 58.5 / +7.3% | 120 |
| jev[distill-typed+sumo-distill-fromcf] | 39.5 / +0.3% | 39.8 / +1.3% | 51.5 / -4.1% | 120 |
| jev[sumo-distill] | 39.5 / +0.4% | 39.9 / +1.7% | 52.3 / -2.9% | 120 |

### Official event_1

| controller | seen: ATT / vs MP | pattern: ATT / vs MP | junction: ATT / vs MP | runs |
|---|---|---|---|---|
| fixtime | 43.6 / +6.6% | 44.0 / +6.2% | 54.9 / -0.6% | 360 |
| webster | 51.3 / +25.6% | 52.1 / +26.0% | 63.0 / +16.4% | 360 |
| sotl | 74.3 / +79.3% | 73.8 / +76.3% | 98.2 / +78.9% | 360 |
| maxpressure | 41.7 / +0.0% | 42.0 / +0.0% | 57.2 / +0.0% | 360 |
| mp | 41.7 / +0.0% | 42.0 / +0.0% | 57.2 / +0.0% | 360 |
| mp-triggered-rule | 41.6 / +0.4% | 42.5 / +1.7% | 57.5 / +0.6% | 360 |
| unitsa[universal] | 41.0 / -0.5% | 41.3 / -0.5% | 53.1 / -4.3% | 360 |
| jev-always-jev[sumo-distill] | 42.2 / +1.4% | 43.3 / +3.8% | 54.8 / -4.0% | 120 |
| jev-ns-compact-triggered-jev[Qwen2.5-0.5B-Instruct+unitsa-jev-0.5B-compact] | 40.3 / -2.0% | 41.5 / +0.5% | 52.8 / -6.4% | 120 |
| jev-ns-compact-triggered-jev[Qwen2.5-1.5B-Instruct+unitsa-jev-1.5B-compact] | 40.2 / -2.1% | 41.6 / +0.4% | 53.0 / -5.6% | 120 |
| jev-ns-compact[Qwen2.5-0.5B-Instruct+unitsa-jev-0.5B-compact] | 40.2 / -2.1% | 41.2 / -0.3% | 53.4 / -5.6% | 120 |
| jev-ns-compact[Qwen2.5-1.5B-Instruct+unitsa-jev-1.5B-compact] | 41.1 / -0.1% | 42.9 / +3.7% | 53.3 / -4.8% | 120 |
| jev-ns-triggered-jev[Qwen2.5-0.5B-Instruct+unitsa-jev-0.5B-full] | 40.1 / -2.4% | 41.3 / -0.2% | 52.7 / -6.2% | 120 |
| jev-ns[Qwen2.5-0.5B-Instruct+unitsa-jev-0.5B-full] | 40.9 / -0.5% | 43.2 / +4.3% | 53.0 / -5.2% | 120 |
| jev-triggered-jev[sumo-distill] | 42.2 / +1.3% | 42.8 / +2.1% | 55.0 / -3.4% | 120 |
| jev-triggered-rule[sumo-distill] | 42.3 / +1.5% | 42.9 / +2.3% | 54.9 / -3.6% | 120 |
| jev[sumo-distill] | 42.1 / +0.7% | 42.0 / -0.0% | 54.4 / -4.7% | 120 |

### Random events (1 accident set + 1-3 special vehicles)

| controller | seen: ATT / vs MP | pattern: ATT / vs MP | junction: ATT / vs MP | runs |
|---|---|---|---|---|
| mp | 40.5 / +0.0% | 40.2 / +0.0% | 54.2 / +0.0% | 720 |
| mp-triggered-rule | 40.3 / -0.4% | 40.3 / +0.2% | 54.3 / +0.1% | 720 |
| unitsa[universal] | 39.0 / -2.3% | 39.2 / -1.5% | 50.3 / -5.0% | 720 |
| jev-always-jev[sumo-distill] | 40.1 / -1.1% | 41.1 / +2.1% | 52.6 / -2.8% | 240 |
| jev-ns-compact-triggered-jev[Qwen2.5-0.5B-Instruct+unitsa-jev-0.5B-compact] | 39.0 / -2.4% | 39.4 / -0.9% | 50.7 / -5.8% | 240 |
| jev-ns-compact-triggered-jev[Qwen2.5-1.5B-Instruct+unitsa-jev-1.5B-compact] | 38.7 / -2.8% | 40.5 / +1.4% | 49.9 / -6.7% | 240 |
| jev-ns-compact[Qwen2.5-0.5B-Instruct+unitsa-jev-0.5B-compact] | 38.9 / -2.6% | 39.6 / -0.6% | 50.6 / -5.8% | 240 |
| jev-ns-compact[Qwen2.5-1.5B-Instruct+unitsa-jev-1.5B-compact] | 38.9 / -2.5% | 39.3 / -1.4% | 49.5 / -7.4% | 240 |
| jev-ns-triggered-jev[Qwen2.5-0.5B-Instruct+unitsa-jev-0.5B-full] | 38.9 / -2.5% | 39.2 / -1.5% | 50.0 / -6.4% | 240 |
| jev-ns[Qwen2.5-0.5B-Instruct+unitsa-jev-0.5B-full] | 39.2 / -2.0% | 39.1 / -1.9% | 49.8 / -6.7% | 240 |
| jev-triggered-jev[sumo-distill] | 40.2 / -0.8% | 41.0 / +1.9% | 52.6 / -2.9% | 240 |
| jev-triggered-rule[sumo-distill] | 40.2 / -0.8% | 41.1 / +2.1% | 52.6 / -2.9% | 240 |
| jev[sumo-distill] | 40.5 / -0.4% | 41.0 / +1.9% | 52.4 / -3.2% | 240 |

### ATT per junction (mean over 10 envs x seeds, no events)

| junction | fixtime | webster | sotl | maxpressure | unitsa[universal] | jev[Qwen2.5-7B-Instruct] | jev[distill-typed+sumo-distill-fromcf] | jev[sumo-distill] |
|---|---|---|---|---|---|---|---|---|
| Beijing_Beihuan | 37.9 | 42.9 | 51.8 | 33.8 | 35.2 | 35.0 | **33.4** | 34.0 |
| Beijing_Beishahe | 36.9 | 44.9 | 80.8 | 38.1 | **35.7** | 37.1 | 38.7 | 37.7 |
| Beijing_Changjianglu | 41.9 | 48.4 | 79.4 | 46.3 | **40.2** | 46.8 | 49.6 | 49.9 |
| Beijing_Gaojiaoyuan | 42.8 | 49.2 | 77.7 | 36.8 | 37.8 | 46.4 | **36.8** | 36.8 |
| Beijing_Pinganli | 44.9 | 51.4 | 86.1 | 43.3 | **40.8** | 52.5 | 43.1 | 42.9 |
| Beijing_Yongrunlu | 44.8 | 51.9 | 83.1 | 42.5 | **40.8** | 58.1 | 42.1 | 41.9 |
| Chengdu_Chenghannanlu | 38.9 | 46.8 | 58.3 | 36.5 | **35.9** | 36.8 | 36.7 | 37.6 |
| Chengdu_Guanghua | 44.2 | 51.2 | 76.3 | 38.3 | 38.0 | 42.6 | 38.0 | **37.6** |
| Tianjin_zhijingdao | 43.2 | 50.1 | 77.4 | **37.1** | 38.6 | 61.3 | 37.2 | 37.5 |
| France_Massy (held-out) | 57.3 | 62.5 | 75.4 | 57.1 | **53.5** | 57.7 | 56.2 | 56.9 |
| Hongkong_YMT (held-out) | 42.2 | 51.5 | 80.4 | 39.0 | 41.6 | 40.3 | 37.4 | **36.5** |
| SouthKorea_Songdo (held-out) | 57.9 | 65.2 | 136.2 | 65.8 | **55.1** | 77.6 | 61.0 | 63.6 |

### Context agent cost (all scenarios)

| controller | events | runs | ATT | extra calls / step | model calls / step | ms / step | ms / call |
|---|---|---|---|---|---|---|---|
| jev-always-jev[sumo-distill] | event_1 | 120 | 45.5 | 1.000 | 1.704 | 339.6 | 199.8 |
| jev-always-jev[sumo-distill] | none | 120 | 42.7 | 1.000 | 1.719 | 258.2 | 150.6 |
| jev-always-jev[sumo-distill] | random | 240 | 43.4 | 1.000 | 1.709 | 287.8 | 168.7 |
| jev-ns-compact-triggered-jev[Qwen2.5-0.5B-Instruct+unitsa-jev-0.5B-compact] | event_1 | 120 | 43.6 | 0.021 | 0.957 | 31.3 | 32.8 |
| jev-ns-compact-triggered-jev[Qwen2.5-0.5B-Instruct+unitsa-jev-0.5B-compact] | none | 120 | 41.3 | 0.000 | 0.965 | 31.6 | 32.7 |
| jev-ns-compact-triggered-jev[Qwen2.5-0.5B-Instruct+unitsa-jev-0.5B-compact] | random | 240 | 42.0 | 0.013 | 0.961 | 31.4 | 32.7 |
| jev-ns-compact-triggered-jev[Qwen2.5-1.5B-Instruct+unitsa-jev-1.5B-compact] | event_1 | 120 | 43.6 | 0.022 | 0.955 | 34.9 | 36.6 |
| jev-ns-compact-triggered-jev[Qwen2.5-1.5B-Instruct+unitsa-jev-1.5B-compact] | none | 120 | 40.9 | 0.000 | 0.964 | 34.6 | 36.0 |
| jev-ns-compact-triggered-jev[Qwen2.5-1.5B-Instruct+unitsa-jev-1.5B-compact] | random | 240 | 41.8 | 0.014 | 0.960 | 35.0 | 36.5 |
| jev-ns-compact[Qwen2.5-0.5B-Instruct+unitsa-jev-0.5B-compact] | event_1 | 120 | 43.7 | 0.000 | 0.965 | 32.2 | 33.3 |
| jev-ns-compact[Qwen2.5-0.5B-Instruct+unitsa-jev-0.5B-compact] | none | 120 | 41.3 | 0.000 | 0.965 | 32.2 | 33.4 |
| jev-ns-compact[Qwen2.5-0.5B-Instruct+unitsa-jev-0.5B-compact] | random | 240 | 41.9 | 0.000 | 0.966 | 32.0 | 33.2 |
| jev-ns-compact[Qwen2.5-1.5B-Instruct+unitsa-jev-1.5B-compact] | event_1 | 120 | 44.4 | 0.000 | 0.961 | 35.3 | 36.7 |
| jev-ns-compact[Qwen2.5-1.5B-Instruct+unitsa-jev-1.5B-compact] | none | 120 | 40.9 | 0.000 | 0.964 | 35.5 | 36.9 |
| jev-ns-compact[Qwen2.5-1.5B-Instruct+unitsa-jev-1.5B-compact] | random | 240 | 41.6 | 0.000 | 0.965 | 35.5 | 36.8 |
| jev-ns-triggered-jev[Qwen2.5-0.5B-Instruct+unitsa-jev-0.5B-full] | event_1 | 120 | 43.4 | 0.021 | 0.955 | 31.5 | 33.0 |
| jev-ns-triggered-jev[Qwen2.5-0.5B-Instruct+unitsa-jev-0.5B-full] | none | 120 | 41.0 | 0.000 | 0.967 | 31.6 | 32.7 |
| jev-ns-triggered-jev[Qwen2.5-0.5B-Instruct+unitsa-jev-0.5B-full] | random | 240 | 41.7 | 0.013 | 0.963 | 31.8 | 33.1 |
| jev-ns[Qwen2.5-0.5B-Instruct+unitsa-jev-0.5B-full] | event_1 | 120 | 44.3 | 0.000 | 0.964 | 32.5 | 33.7 |
| jev-ns[Qwen2.5-0.5B-Instruct+unitsa-jev-0.5B-full] | none | 120 | 41.0 | 0.000 | 0.967 | 32.1 | 33.2 |
| jev-ns[Qwen2.5-0.5B-Instruct+unitsa-jev-0.5B-full] | random | 240 | 41.8 | 0.000 | 0.967 | 32.2 | 33.3 |
| jev-triggered-jev[sumo-distill] | event_1 | 120 | 45.5 | 0.019 | 0.725 | 103.3 | 143.2 |
| jev-triggered-jev[sumo-distill] | none | 120 | 42.7 | 0.000 | 0.719 | 73.3 | 102.4 |
| jev-triggered-jev[sumo-distill] | random | 240 | 43.4 | 0.012 | 0.722 | 84.6 | 117.7 |
| jev-triggered-rule[sumo-distill] | event_1 | 120 | 45.5 | 0.019 | 0.706 | 96.6 | 137.6 |
| jev-triggered-rule[sumo-distill] | none | 120 | 42.7 | 0.000 | 0.719 | 73.2 | 102.2 |
| jev-triggered-rule[sumo-distill] | random | 240 | 43.4 | 0.012 | 0.710 | 81.8 | 115.7 |
| jev[Qwen2.5-7B-Instruct] | none | 120 | 49.4 | 0.000 | 0.660 | 31.7 | 47.9 |
| jev[distill-typed+sumo-distill-fromcf] | none | 120 | 42.5 | 0.000 | 0.714 | 79.8 | 112.4 |
| jev[sumo-distill] | event_1 | 120 | 45.1 | 0.000 | 0.718 | 99.0 | 138.6 |
| jev[sumo-distill] | none | 120 | 42.7 | 0.000 | 0.719 | 68.1 | 95.5 |
| jev[sumo-distill] | random | 240 | 43.5 | 0.000 | 0.718 | 83.9 | 117.5 |
| mp-triggered-rule | event_1 | 360 | 45.7 | 0.019 | 0.000 | 0.0 | - |
| mp-triggered-rule | random | 720 | 43.8 | 0.012 | 0.000 | 0.0 | - |

### Special events (sums over runs; latency in s; special-vehicle metrics over their trips)

| controller | events | runs | ATT | special ATT | special timeLoss | special detected | latency | blockages detected | observable detected | latency | false alarms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| jev-always-jev[sumo-distill] | event_1 | 120 | 45.5 | 36.0 | 14.5 | 250/250 | 1.9 | 148/280 | 148/195 | 28.7 | 0 |
| jev-always-jev[sumo-distill] | random | 240 | 43.4 | 34.6 | 13.8 | 458/458 | 0.4 | 22/445 | 21/23 | 67.9 | 23 |
| jev-ns-compact-triggered-jev[Qwen2.5-0.5B-Instruct+unitsa-jev-0.5B-compact] | event_1 | 120 | 43.6 | 40.3 | 19.0 | 250/250 | 0.8 | 73/280 | 73/221 | 31.8 | 0 |
| jev-ns-compact-triggered-jev[Qwen2.5-0.5B-Instruct+unitsa-jev-0.5B-compact] | random | 240 | 42.0 | 36.0 | 15.2 | 465/465 | 0.2 | 5/445 | 5/24 | 69.0 | 10 |
| jev-ns-compact-triggered-jev[Qwen2.5-1.5B-Instruct+unitsa-jev-1.5B-compact] | event_1 | 120 | 43.6 | 40.9 | 19.7 | 249/249 | 2.4 | 115/280 | 115/206 | 33.9 | 0 |
| jev-ns-compact-triggered-jev[Qwen2.5-1.5B-Instruct+unitsa-jev-1.5B-compact] | random | 240 | 41.8 | 36.6 | 15.8 | 461/461 | 1.1 | 9/445 | 9/29 | 83.7 | 9 |
| jev-ns-compact[Qwen2.5-0.5B-Instruct+unitsa-jev-0.5B-compact] | event_1 | 120 | 43.7 | 50.7 | 30.0 | - | - | - | - | - | - |
| jev-ns-compact[Qwen2.5-0.5B-Instruct+unitsa-jev-0.5B-compact] | random | 240 | 41.9 | 42.1 | 21.3 | - | - | - | - | - | - |
| jev-ns-compact[Qwen2.5-1.5B-Instruct+unitsa-jev-1.5B-compact] | event_1 | 120 | 44.4 | 55.3 | 34.7 | - | - | - | - | - | - |
| jev-ns-compact[Qwen2.5-1.5B-Instruct+unitsa-jev-1.5B-compact] | random | 240 | 41.6 | 42.4 | 21.6 | - | - | - | - | - | - |
| jev-ns-triggered-jev[Qwen2.5-0.5B-Instruct+unitsa-jev-0.5B-full] | event_1 | 120 | 43.4 | 40.7 | 19.6 | 247/247 | 3.1 | 168/280 | 168/218 | 35.9 | 0 |
| jev-ns-triggered-jev[Qwen2.5-0.5B-Instruct+unitsa-jev-0.5B-full] | random | 240 | 41.7 | 35.8 | 15.0 | 458/458 | 0.2 | 6/445 | 6/23 | 115.5 | 18 |
| jev-ns[Qwen2.5-0.5B-Instruct+unitsa-jev-0.5B-full] | event_1 | 120 | 44.3 | 55.6 | 35.0 | - | - | - | - | - | - |
| jev-ns[Qwen2.5-0.5B-Instruct+unitsa-jev-0.5B-full] | random | 240 | 41.8 | 41.7 | 20.9 | - | - | - | - | - | - |
| jev-triggered-jev[sumo-distill] | event_1 | 120 | 45.5 | 36.7 | 15.3 | 250/250 | 1.0 | 123/280 | 123/194 | 33.6 | 0 |
| jev-triggered-jev[sumo-distill] | random | 240 | 43.4 | 34.5 | 13.8 | 458/458 | 0.2 | 13/445 | 13/25 | 87.8 | 14 |
| jev-triggered-rule[sumo-distill] | event_1 | 120 | 45.5 | 36.9 | 15.4 | 250/250 | 1.0 | 160/280 | 160/198 | 34.9 | 0 |
| jev-triggered-rule[sumo-distill] | random | 240 | 43.4 | 34.5 | 13.8 | 458/458 | 0.2 | 13/445 | 13/25 | 83.2 | 15 |
| jev[sumo-distill] | event_1 | 120 | 45.1 | 51.2 | 30.1 | - | - | - | - | - | - |
| jev[sumo-distill] | random | 240 | 43.5 | 44.6 | 23.8 | - | - | - | - | - | - |
| mp | event_1 | 360 | 45.6 | 52.5 | 31.5 | - | - | - | - | - | - |
| mp | random | 720 | 43.9 | 45.9 | 25.1 | - | - | - | - | - | - |
| mp-triggered-rule | event_1 | 360 | 45.7 | 36.8 | 15.4 | 750/750 | 1.5 | 468/840 | 468/594 | 34.9 | 0 |
| mp-triggered-rule | random | 720 | 43.8 | 35.2 | 14.4 | 1386/1386 | 0.2 | 39/1335 | 39/87 | 71.6 | 45 |
| unitsa[universal] | event_1 | 360 | 44.1 | 51.6 | 30.8 | - | - | - | - | - | - |
| unitsa[universal] | random | 720 | 41.9 | 42.5 | 21.7 | - | - | - | - | - | - |

### ATT vs unitsa[universal] on matched scenarios (negative = better than UniTSA)

| controller | none: seen | none: pattern | none: junction | event_1: seen | event_1: pattern | event_1: junction | random: seen | random: pattern | random: junction | agree UniTSA | ms / call |
|---|---|---|---|---|---|---|---|---|---|---|---|
| maxpressure | +2.9% (216) | +1.5% (54) | +7.0% (90) | +1.7% (216) | +1.7% (54) | +7.3% (90) | - | - | - | - | - |
| mp | - | - | - | +1.7% (216) | +1.7% (54) | +7.3% (90) | +3.8% (432) | +2.3% (108) | +7.1% (180) | - | - |
| mp-triggered-rule | - | - | - | +1.8% (216) | +3.0% (54) | +7.9% (90) | +3.1% (432) | +2.5% (108) | +7.1% (180) | - | - |
| unitsa[ft] | -3.8% (72) | -2.5% (18) | -2.7% (90) | -4.7% (72) | -3.9% (18) | -1.0% (90) | -3.6% (144) | -0.5% (36) | -2.4% (180) | - | 8.6 |
| unitsa[scratch] | - | - | +0.4% (90) | - | - | +0.9% (90) | - | - | +0.8% (180) | - | 7.1 |
| fixtime | +9.9% (216) | +9.2% (54) | +6.2% (90) | +7.4% (216) | +6.8% (54) | +4.9% (90) | - | - | - | - | - |
| jev-always-jev[sumo-distill] | +3.4% (72) | +3.4% (18) | +3.8% (30) | +3.0% (72) | +5.3% (18) | +2.6% (30) | +2.6% (144) | +4.6% (36) | +3.9% (60) | - | 172.0 |
| jev-ns-compact-triggered-jev[Qwen2.5-0.5B-Instruct+unitsa-jev-0.5B-compact] | +0.1% (72) | +1.2% (18) | +0.4% (30) | -1.4% (72) | +0.9% (18) | -0.8% (30) | +0.1% (144) | +0.6% (36) | +0.3% (60) | 0.827 | 32.7 |
| jev-ns-compact-triggered-jev[Qwen2.5-1.5B-Instruct+unitsa-jev-1.5B-compact] | -0.2% (72) | +0.4% (18) | -1.5% (30) | -1.5% (72) | +1.0% (18) | +0.1% (30) | -0.5% (144) | +3.5% (36) | -1.0% (60) | 0.831 | 36.4 |
| jev-ns-compact[Qwen2.5-0.5B-Instruct+unitsa-jev-0.5B-compact] | +0.1% (72) | +1.2% (18) | +0.4% (30) | -1.6% (72) | +0.1% (18) | +0.3% (30) | -0.1% (144) | +1.0% (36) | +0.2% (60) | 0.825 | 33.3 |
| jev-ns-compact[Qwen2.5-1.5B-Instruct+unitsa-jev-1.5B-compact] | -0.2% (72) | +0.4% (18) | -1.5% (30) | +0.6% (72) | +4.2% (18) | +0.7% (30) | -0.2% (144) | +0.2% (36) | -1.6% (60) | 0.830 | 36.8 |
| jev-ns-triggered-jev[Qwen2.5-0.5B-Instruct+unitsa-jev-0.5B-full] | +0.1% (72) | +0.1% (18) | -1.4% (30) | -1.7% (72) | +0.5% (18) | -0.8% (30) | -0.0% (144) | +0.1% (36) | -0.8% (60) | 0.825 | 32.9 |
| jev-ns[Qwen2.5-0.5B-Instruct+unitsa-jev-0.5B-full] | +0.1% (72) | +0.1% (18) | -1.4% (30) | +0.2% (72) | +4.9% (18) | -0.1% (30) | +0.6% (144) | -0.3% (36) | -1.1% (60) | 0.825 | 33.4 |
| jev-triggered-jev[sumo-distill] | +3.4% (72) | +3.4% (18) | +3.8% (30) | +3.0% (72) | +3.8% (18) | +3.1% (30) | +2.9% (144) | +4.4% (36) | +3.8% (60) | - | 120.2 |
| jev-triggered-rule[sumo-distill] | +3.4% (72) | +3.4% (18) | +3.8% (30) | +3.1% (72) | +4.1% (18) | +2.9% (30) | +2.9% (144) | +4.6% (36) | +3.8% (60) | - | 117.8 |
| jev[Qwen2.5-7B-Instruct] | +19.4% (72) | +24.8% (18) | +15.4% (30) | - | - | - | - | - | - | - | 47.9 |
| jev[distill-typed+sumo-distill-fromcf] | +3.4% (72) | +3.1% (18) | +2.3% (30) | - | - | - | - | - | - | - | 112.4 |
| jev[sumo-distill] | +3.4% (72) | +3.4% (18) | +3.8% (30) | +2.5% (72) | +1.7% (18) | +1.7% (30) | +3.5% (144) | +4.5% (36) | +3.5% (60) | - | 117.3 |
| sotl | +96.0% (216) | +92.0% (54) | +98.7% (90) | +82.6% (216) | +79.1% (54) | +90.3% (90) | - | - | - | - | - |
| webster | +28.3% (216) | +26.8% (54) | +22.7% (90) | +26.4% (216) | +26.6% (54) | +22.5% (90) | - | - | - | - | - |

### Long-term adaptation over simulated days

| junction | policy | days | ATT | MP ATT | vs MP (all days) | vs MP (week 2) | agree MP | adaptations (accepted) | train s | storage MB |
|---|---|---|---|---|---|---|---|---|---|---|
| France_Massy | auto | 14 | 54.4 | 54.7 | -0.7% | -0.2% | 0.809 | 2 (0) | 404 | 0.0 |
| France_Massy | daily | 14 | 54.4 | 54.7 | -0.7% | -0.2% | 0.809 | 14 (0) | 2241 | 0.0 |
| France_Massy | off | 14 | 54.4 | 54.7 | -0.7% | -0.2% | 0.809 | 0 (0) | 0 | 0.0 |
| France_Massy | weekly | 14 | 54.4 | 54.7 | -0.7% | -0.2% | 0.809 | 2 (0) | 402 | 0.0 |
| Hongkong_YMT | auto | 14 | 29.3 | 31.6 | -7.2% | -7.3% | 0.658 | 2 (0) | 440 | 0.0 |
| Hongkong_YMT | daily | 14 | 29.3 | 31.6 | -7.2% | -7.3% | 0.658 | 14 (0) | 2121 | 0.0 |
| Hongkong_YMT | off | 14 | 29.3 | 31.6 | -7.2% | -7.3% | 0.658 | 0 (0) | 0 | 0.0 |
| Hongkong_YMT | weekly | 14 | 29.3 | 31.6 | -7.2% | -7.3% | 0.658 | 2 (0) | 367 | 0.0 |
| SouthKorea_Songdo | auto | 14 | 65.2 | 71.0 | -8.0% | -9.1% | 0.635 | 2 (0) | 695 | 0.0 |
| SouthKorea_Songdo | daily | 14 | 65.2 | 71.0 | -8.0% | -9.1% | 0.635 | 14 (0) | 3623 | 0.0 |
| SouthKorea_Songdo | off | 14 | 65.2 | 71.0 | -8.0% | -9.1% | 0.635 | 0 (0) | 0 | 0.0 |
| SouthKorea_Songdo | weekly | 14 | 65.2 | 71.0 | -8.0% | -9.1% | 0.635 | 2 (0) | 600 | 0.0 |
