| dataset | traffic | controller | seeds | ATT (s) | AWT (s) | AQL | ms / decision | extra |
|---|---|---|---|---|---|---|---|---|
| hangzhou | anon_4_4_hangzhou_real | fixedtime | 3 | 497.0 ± 0.0 | 37.3 ± 0.0 | 203.7 ± 0.0 | - |  |
| hangzhou | anon_4_4_hangzhou_real | random | 3 | 607.8 ± 16.2 | 93.1 ± 1.1 | 285.3 ± 8.9 | - |  |
| hangzhou | anon_4_4_hangzhou_real | maxqueue | 3 | 312.6 ± 0.0 | 42.0 ± 0.0 | 58.9 ± 0.0 | - |  |
| hangzhou | anon_4_4_hangzhou_real | maxpressure | 3 | 317.0 ± 0.0 | 42.5 ± 0.0 | 62.6 ± 0.0 | - |  |
| hangzhou | anon_4_4_hangzhou_real | rollout-greedy | 1 | 308.1 | 69.2 | 55.4 | - |  |
| hangzhou | anon_4_4_hangzhou_real | jev-raw [Qwen2.5-0.5B-Instruct] | 1 | 948.4 | 683.0 | 637.8 | 98.6 | agree-MP=0.10, fallback=0.00, conf=0.35 |
| hangzhou | anon_4_4_hangzhou_real | jev-raw [Qwen2.5-7B-Instruct] | 1 | 747.3 | 594.5 | 457.6 | 619.8 | agree-MP=0.11, fallback=0.00, conf=0.86 |
| hangzhou | anon_4_4_hangzhou_real | jev-raw-gate0.6 [Qwen2.5-0.5B-Instruct] | 1 | 317.0 | 42.5 | 62.6 | 86.7 | agree-MP=0.45, fallback=1.00, conf=0.35 |
| hangzhou | anon_4_4_hangzhou_real | jev-raw-gate0.6 [Qwen2.5-7B-Instruct] | 1 | 634.5 | 535.5 | 354.5 | 631.1 | agree-MP=0.15, fallback=0.07, conf=0.87 |
| hangzhou | anon_4_4_hangzhou_real | jev-score-raw [Qwen2.5-7B-Instruct] | 1 | 784.9 | 644.6 | 420.7 | 1905.4 | agree-MP=0.33 |
| hangzhou | anon_4_4_hangzhou_real | jev-score-typed [Qwen2.5-7B-Instruct] | 1 | 574.5 | 107.5 | 265.5 | 190.3 | agree-MP=0.43 |
| hangzhou | anon_4_4_hangzhou_real | jev-typed T=0.52 [Qwen2.5-7B-Instruct+distill-typed+reward-soft] | 1 | 316.9 | 58.4 | 63.1 | 55.3 | agree-MP=0.77, fallback=0.00, conf=0.84 |
| hangzhou | anon_4_4_hangzhou_real | jev-typed T=0.95 [Qwen2.5-7B-Instruct+distill-typed] | 1 | 313.1 | 39.5 | 58.1 | 55.7 | agree-MP=0.90, fallback=0.00, conf=0.89 |
| hangzhou | anon_4_4_hangzhou_real | jev-typed T=3.86 [Qwen2.5-7B-Instruct+distill-typed+reward-dpo] | 1 | 313.8 | 45.3 | 59.9 | 55.1 | agree-MP=0.86, fallback=0.00, conf=0.82 |
| hangzhou | anon_4_4_hangzhou_real | jev-typed [Qwen2.5-0.5B-Instruct] | 1 | 1124.8 | 880.8 | 798.4 | 10.2 | agree-MP=0.10, fallback=0.00, conf=0.48 |
| hangzhou | anon_4_4_hangzhou_real | jev-typed [Qwen2.5-7B-Instruct] | 1 | 1061.6 | 776.2 | 636.2 | 55.3 | agree-MP=0.17, fallback=0.00, conf=0.97 |
| hangzhou | anon_4_4_hangzhou_real | jev-typed-gate0.6 T=0.52 [Qwen2.5-7B-Instruct+distill-typed+reward-soft] | 1 | 317.5 | 54.2 | 63.1 | 58.8 | agree-MP=0.78, fallback=0.12, conf=0.85 |
| hangzhou | anon_4_4_hangzhou_real | jev-typed-gate0.6 T=0.95 [Qwen2.5-7B-Instruct+distill-typed] | 1 | 313.8 | 40.8 | 59.2 | 55.7 | agree-MP=0.90, fallback=0.07, conf=0.89 |
| hangzhou | anon_4_4_hangzhou_real | jev-typed-gate0.6 T=3.86 [Qwen2.5-7B-Instruct+distill-typed+reward-dpo] | 1 | 311.9 | 43.8 | 58.5 | 55.5 | agree-MP=0.86, fallback=0.13, conf=0.82 |
| hangzhou | anon_4_4_hangzhou_real | jev-typed-gate0.6 [Qwen2.5-0.5B-Instruct] | 1 | 317.0 | 42.5 | 62.6 | 7.7 | agree-MP=0.25, fallback=1.00, conf=0.47 |
| hangzhou | anon_4_4_hangzhou_real | jev-typed-gate0.6 [Qwen2.5-7B-Instruct] | 1 | 934.7 | 843.8 | 552.0 | 55.4 | agree-MP=0.23, fallback=0.03, conf=0.96 |
| hangzhou | anon_4_4_hangzhou_real | jev-typed-perm2 [Qwen2.5-0.5B-Instruct] | 1 | 1286.4 | 1006.1 | 745.0 | 15.0 | agree-MP=0.07, fallback=0.00, conf=0.47 |
| hangzhou | anon_4_4_hangzhou_real | jev-typed-perm2 [Qwen2.5-7B-Instruct] | 1 | 1135.6 | 867.1 | 656.4 | 109.5 | agree-MP=0.20, fallback=0.00, conf=0.89 |
| hangzhou | anon_4_4_hangzhou_real | jev-typed-perm4 [Qwen2.5-7B-Instruct] | 1 | 1195.9 | 932.9 | 676.4 | 215.0 | agree-MP=0.15, fallback=0.00, conf=0.88 |
| hangzhou | anon_4_4_hangzhou_real | llm-gen [Qwen2.5-0.5B-Instruct] | 1 | 1064.5 | 754.8 | 729.7 | 699.4 | invalid=0.86, gen-tok=988 |
| hangzhou | anon_4_4_hangzhou_real | llm-gen [Qwen2.5-7B-Instruct] | 1 | 322.8 | 38.4 | 66.3 | 1937.0 | invalid=0.03, gen-tok=498 |
| hangzhou | anon_4_4_hangzhou_real_5816 (held-out) | fixedtime | 3 | 408.7 ± 0.0 | 37.2 ± 0.0 | 303.4 ± 0.0 | - |  |
| hangzhou | anon_4_4_hangzhou_real_5816 (held-out) | random | 3 | 490.3 ± 17.3 | 91.6 ± 3.9 | 426.3 ± 21.5 | - |  |
| hangzhou | anon_4_4_hangzhou_real_5816 (held-out) | maxqueue | 3 | 331.3 ± 0.0 | 57.2 ± 0.0 | 185.2 ± 0.0 | - |  |
| hangzhou | anon_4_4_hangzhou_real_5816 (held-out) | maxpressure | 3 | 335.1 ± 0.0 | 57.2 ± 0.0 | 191.7 ± 0.0 | - |  |
| hangzhou | anon_4_4_hangzhou_real_5816 (held-out) | rollout-greedy | 1 | 327.5 | 139.3 | 187.6 | - |  |
| hangzhou | anon_4_4_hangzhou_real_5816 (held-out) | jev-raw [Qwen2.5-0.5B-Instruct] | 1 | 623.2 | 528.2 | 785.0 | 109.8 | agree-MP=0.11, fallback=0.00, conf=0.33 |
| hangzhou | anon_4_4_hangzhou_real_5816 (held-out) | jev-raw [Qwen2.5-7B-Instruct] | 1 | 587.7 | 478.4 | 693.9 | 636.9 | agree-MP=0.12, fallback=0.00, conf=0.85 |
| hangzhou | anon_4_4_hangzhou_real_5816 (held-out) | jev-raw-gate0.6 [Qwen2.5-0.5B-Instruct] | 1 | 335.1 | 57.2 | 191.7 | 93.4 | agree-MP=0.46, fallback=1.00, conf=0.34 |
| hangzhou | anon_4_4_hangzhou_real_5816 (held-out) | jev-raw-gate0.6 [Qwen2.5-7B-Instruct] | 1 | 490.2 | 336.4 | 511.6 | 644.8 | agree-MP=0.15, fallback=0.09, conf=0.86 |
| hangzhou | anon_4_4_hangzhou_real_5816 (held-out) | jev-score-raw [Qwen2.5-7B-Instruct] | 1 | 614.4 | 345.1 | 610.1 | 2028.3 | agree-MP=0.30 |
| hangzhou | anon_4_4_hangzhou_real_5816 (held-out) | jev-score-typed [Qwen2.5-7B-Instruct] | 1 | 464.2 | 96.7 | 394.9 | 191.9 | agree-MP=0.42 |
| hangzhou | anon_4_4_hangzhou_real_5816 (held-out) | jev-typed T=0.52 [Qwen2.5-7B-Instruct+distill-typed+reward-soft] | 1 | 333.6 | 98.2 | 195.6 | 59.1 | agree-MP=0.72, fallback=0.00, conf=0.82 |
| hangzhou | anon_4_4_hangzhou_real_5816 (held-out) | jev-typed T=0.95 [Qwen2.5-7B-Instruct+distill-typed] | 1 | 333.1 | 53.6 | 186.4 | 56.1 | agree-MP=0.89, fallback=0.00, conf=0.89 |
| hangzhou | anon_4_4_hangzhou_real_5816 (held-out) | jev-typed T=3.86 [Qwen2.5-7B-Instruct+distill-typed+reward-dpo] | 1 | 333.7 | 70.6 | 193.7 | 56.1 | agree-MP=0.84, fallback=0.00, conf=0.82 |
| hangzhou | anon_4_4_hangzhou_real_5816 (held-out) | jev-typed [Qwen2.5-0.5B-Instruct] | 1 | 743.0 | 732.7 | 950.4 | 7.7 | agree-MP=0.07, fallback=0.00, conf=0.48 |
| hangzhou | anon_4_4_hangzhou_real_5816 (held-out) | jev-typed [Qwen2.5-7B-Instruct] | 1 | 740.6 | 697.2 | 738.0 | 55.2 | agree-MP=0.16, fallback=0.00, conf=0.97 |
| hangzhou | anon_4_4_hangzhou_real_5816 (held-out) | jev-typed-gate0.6 T=0.52 [Qwen2.5-7B-Instruct+distill-typed+reward-soft] | 1 | 333.2 | 89.8 | 194.6 | 55.7 | agree-MP=0.71, fallback=0.13, conf=0.83 |
| hangzhou | anon_4_4_hangzhou_real_5816 (held-out) | jev-typed-gate0.6 T=0.95 [Qwen2.5-7B-Instruct+distill-typed] | 1 | 332.1 | 56.0 | 186.4 | 55.8 | agree-MP=0.89, fallback=0.07, conf=0.89 |
| hangzhou | anon_4_4_hangzhou_real_5816 (held-out) | jev-typed-gate0.6 T=3.86 [Qwen2.5-7B-Instruct+distill-typed+reward-dpo] | 1 | 331.2 | 61.6 | 187.2 | 55.5 | agree-MP=0.84, fallback=0.15, conf=0.83 |
| hangzhou | anon_4_4_hangzhou_real_5816 (held-out) | jev-typed-gate0.6 [Qwen2.5-0.5B-Instruct] | 1 | 335.1 | 57.2 | 191.7 | 7.7 | agree-MP=0.28, fallback=1.00, conf=0.47 |
| hangzhou | anon_4_4_hangzhou_real_5816 (held-out) | jev-typed-gate0.6 [Qwen2.5-7B-Instruct] | 1 | 753.9 | 717.0 | 750.0 | 55.1 | agree-MP=0.18, fallback=0.01, conf=0.97 |
| hangzhou | anon_4_4_hangzhou_real_5816 (held-out) | jev-typed-perm2 [Qwen2.5-0.5B-Instruct] | 1 | 925.2 | 824.8 | 927.3 | 14.8 | agree-MP=0.18, fallback=0.00, conf=0.48 |
| hangzhou | anon_4_4_hangzhou_real_5816 (held-out) | jev-typed-perm2 [Qwen2.5-7B-Instruct] | 1 | 758.5 | 758.6 | 746.0 | 109.4 | agree-MP=0.18, fallback=0.00, conf=0.87 |
| hangzhou | anon_4_4_hangzhou_real_5816 (held-out) | jev-typed-perm4 [Qwen2.5-7B-Instruct] | 1 | 782.9 | 814.3 | 763.1 | 214.3 | agree-MP=0.14, fallback=0.00, conf=0.88 |
| hangzhou | anon_4_4_hangzhou_real_5816 (held-out) | llm-gen [Qwen2.5-0.5B-Instruct] | 1 | 703.3 | 559.5 | 872.0 | 700.7 | invalid=0.85, gen-tok=986 |
| hangzhou | anon_4_4_hangzhou_real_5816 (held-out) | llm-gen [Qwen2.5-7B-Instruct] | 1 | 341.4 | 51.3 | 198.1 | 1825.9 | invalid=0.02, gen-tok=488 |
| jinan | anon_3_4_jinan_real | fixedtime | 3 | 434.8 ± 0.0 | 42.8 ± 0.0 | 418.9 ± 0.0 | - |  |
| jinan | anon_3_4_jinan_real | random | 3 | 556.2 ± 6.7 | 102.0 ± 5.1 | 605.5 ± 20.6 | - |  |
| jinan | anon_3_4_jinan_real | maxqueue | 3 | 274.9 ± 0.0 | 43.2 ± 0.0 | 159.9 ± 0.0 | - |  |
| jinan | anon_3_4_jinan_real | maxpressure | 3 | 275.9 ± 0.0 | 43.8 ± 0.0 | 162.9 ± 0.0 | - |  |
| jinan | anon_3_4_jinan_real | rollout-greedy | 1 | 272.5 | 57.9 | 157.7 | - |  |
| jinan | anon_3_4_jinan_real | jev-raw [Qwen2.5-0.5B-Instruct] | 1 | 1235.7 | 851.1 | 1699.8 | 105.8 | agree-MP=0.04, fallback=0.00, conf=0.36 |
| jinan | anon_3_4_jinan_real | jev-raw [Qwen2.5-7B-Instruct] | 1 | 760.0 | 500.9 | 1026.2 | 673.6 | agree-MP=0.10, fallback=0.00, conf=0.78 |
| jinan | anon_3_4_jinan_real | jev-raw-gate0.6 [Qwen2.5-0.5B-Instruct] | 1 | 275.9 | 43.8 | 162.9 | 102.9 | agree-MP=0.38, fallback=1.00, conf=0.33 |
| jinan | anon_3_4_jinan_real | jev-raw-gate0.6 [Qwen2.5-7B-Instruct] | 1 | 489.4 | 216.7 | 533.1 | 685.6 | agree-MP=0.17, fallback=0.13, conf=0.79 |
| jinan | anon_3_4_jinan_real | jev-score-raw [Qwen2.5-7B-Instruct] | 1 | 963.9 | 417.9 | 1200.8 | 2230.9 | agree-MP=0.23 |
| jinan | anon_3_4_jinan_real | jev-score-typed [Qwen2.5-7B-Instruct] | 1 | 468.7 | 74.5 | 456.7 | 196.7 | agree-MP=0.42 |
| jinan | anon_3_4_jinan_real | jev-typed T=0.52 [Qwen2.5-7B-Instruct+distill-typed+reward-soft] | 1 | 274.6 | 58.1 | 161.4 | 57.6 | agree-MP=0.80, fallback=0.00, conf=0.83 |
| jinan | anon_3_4_jinan_real | jev-typed T=0.95 [Qwen2.5-7B-Instruct+distill-typed] | 1 | 274.9 | 43.3 | 160.5 | 57.8 | agree-MP=0.90, fallback=0.00, conf=0.90 |
| jinan | anon_3_4_jinan_real | jev-typed T=3.86 [Qwen2.5-7B-Instruct+distill-typed+reward-dpo] | 1 | 273.9 | 47.7 | 159.5 | 57.4 | agree-MP=0.87, fallback=0.00, conf=0.86 |
| jinan | anon_3_4_jinan_real | jev-typed [Qwen2.5-0.5B-Instruct] | 1 | 1303.7 | 959.0 | 1772.6 | 8.6 | agree-MP=0.02, fallback=0.00, conf=0.49 |
| jinan | anon_3_4_jinan_real | jev-typed [Qwen2.5-7B-Instruct] | 1 | 1135.4 | 923.8 | 1444.8 | 56.9 | agree-MP=0.03, fallback=0.00, conf=0.99 |
| jinan | anon_3_4_jinan_real | jev-typed-gate0.6 T=0.52 [Qwen2.5-7B-Instruct+distill-typed+reward-soft] | 1 | 275.7 | 52.1 | 163.1 | 61.7 | agree-MP=0.81, fallback=0.11, conf=0.84 |
| jinan | anon_3_4_jinan_real | jev-typed-gate0.6 T=0.95 [Qwen2.5-7B-Instruct+distill-typed] | 1 | 276.4 | 43.1 | 162.7 | 57.9 | agree-MP=0.90, fallback=0.08, conf=0.90 |
| jinan | anon_3_4_jinan_real | jev-typed-gate0.6 T=3.86 [Qwen2.5-7B-Instruct+distill-typed+reward-dpo] | 1 | 275.2 | 46.5 | 161.6 | 58.0 | agree-MP=0.88, fallback=0.10, conf=0.87 |
| jinan | anon_3_4_jinan_real | jev-typed-gate0.6 [Qwen2.5-0.5B-Instruct] | 1 | 275.9 | 43.8 | 162.9 | 8.6 | agree-MP=0.19, fallback=1.00, conf=0.46 |
| jinan | anon_3_4_jinan_real | jev-typed-gate0.6 [Qwen2.5-7B-Instruct] | 1 | 1141.7 | 939.2 | 1456.1 | 56.9 | agree-MP=0.03, fallback=0.00, conf=1.00 |
| jinan | anon_3_4_jinan_real | jev-typed-perm2 [Qwen2.5-0.5B-Instruct] | 1 | 1142.3 | 943.3 | 1446.1 | 16.1 | agree-MP=0.03, fallback=0.00, conf=0.49 |
| jinan | anon_3_4_jinan_real | jev-typed-perm2 [Qwen2.5-7B-Instruct] | 1 | 1241.6 | 881.3 | 1568.6 | 111.6 | agree-MP=0.04, fallback=0.00, conf=0.95 |
| jinan | anon_3_4_jinan_real | jev-typed-perm4 [Qwen2.5-7B-Instruct] | 1 | 1159.8 | 940.7 | 1467.0 | 218.4 | agree-MP=0.03, fallback=0.00, conf=0.93 |
| jinan | anon_3_4_jinan_real | llm-gen [Qwen2.5-0.5B-Instruct] | 1 | 1189.2 | 681.0 | 1673.2 | 914.6 | invalid=0.85, gen-tok=987 |
| jinan | anon_3_4_jinan_real | llm-gen [Qwen2.5-7B-Instruct] | 1 | 289.3 | 43.9 | 181.8 | 2110.2 | invalid=0.01, gen-tok=462 |
| jinan | anon_3_4_jinan_real_2000 | fixedtime | 3 | 369.6 ± 0.0 | 36.0 ± 0.0 | 214.2 ± 0.0 | - |  |
| jinan | anon_3_4_jinan_real_2000 | random | 3 | 531.1 ± 16.5 | 95.5 ± 9.9 | 396.7 ± 22.1 | - |  |
| jinan | anon_3_4_jinan_real_2000 | maxqueue | 3 | 266.9 ± 0.0 | 40.3 ± 0.0 | 101.3 ± 0.0 | - |  |
| jinan | anon_3_4_jinan_real_2000 | maxpressure | 3 | 267.9 ± 0.0 | 37.1 ± 0.0 | 102.4 ± 0.0 | - |  |
| jinan | anon_3_4_jinan_real_2000 | rollout-greedy | 1 | 268.3 | 53.3 | 102.2 | - |  |
| jinan | anon_3_4_jinan_real_2000 | jev-raw [Qwen2.5-0.5B-Instruct] | 1 | 1189.6 | 713.2 | 1276.2 | 106.7 | agree-MP=0.05, fallback=0.00, conf=0.33 |
| jinan | anon_3_4_jinan_real_2000 | jev-raw [Qwen2.5-7B-Instruct] | 1 | 721.9 | 504.3 | 681.7 | 656.5 | agree-MP=0.10, fallback=0.00, conf=0.78 |
| jinan | anon_3_4_jinan_real_2000 | jev-raw-gate0.6 [Qwen2.5-0.5B-Instruct] | 1 | 267.9 | 37.1 | 102.4 | 95.6 | agree-MP=0.37, fallback=1.00, conf=0.34 |
| jinan | anon_3_4_jinan_real_2000 | jev-raw-gate0.6 [Qwen2.5-7B-Instruct] | 1 | 450.2 | 197.9 | 316.1 | 653.8 | agree-MP=0.18, fallback=0.13, conf=0.81 |
| jinan | anon_3_4_jinan_real_2000 | jev-score-raw [Qwen2.5-7B-Instruct] | 1 | 796.4 | 337.9 | 692.0 | 2180.5 | agree-MP=0.31 |
| jinan | anon_3_4_jinan_real_2000 | jev-score-typed [Qwen2.5-7B-Instruct] | 1 | 409.6 | 72.3 | 253.4 | 195.7 | agree-MP=0.42 |
| jinan | anon_3_4_jinan_real_2000 | jev-typed T=0.52 [Qwen2.5-7B-Instruct+distill-typed+reward-soft] | 1 | 271.0 | 51.2 | 105.2 | 61.4 | agree-MP=0.80, fallback=0.00, conf=0.84 |
| jinan | anon_3_4_jinan_real_2000 | jev-typed T=0.95 [Qwen2.5-7B-Instruct+distill-typed] | 1 | 268.8 | 40.2 | 103.2 | 57.8 | agree-MP=0.90, fallback=0.00, conf=0.89 |
| jinan | anon_3_4_jinan_real_2000 | jev-typed T=3.86 [Qwen2.5-7B-Instruct+distill-typed+reward-dpo] | 1 | 267.7 | 42.2 | 102.0 | 57.9 | agree-MP=0.87, fallback=0.00, conf=0.85 |
| jinan | anon_3_4_jinan_real_2000 | jev-typed [Qwen2.5-0.5B-Instruct] | 1 | 1382.3 | 948.1 | 1485.1 | 8.7 | agree-MP=0.03, fallback=0.00, conf=0.49 |
| jinan | anon_3_4_jinan_real_2000 | jev-typed [Qwen2.5-7B-Instruct] | 1 | 1300.1 | 987.2 | 1185.8 | 56.8 | agree-MP=0.04, fallback=0.00, conf=0.99 |
| jinan | anon_3_4_jinan_real_2000 | jev-typed-gate0.6 T=0.52 [Qwen2.5-7B-Instruct+distill-typed+reward-soft] | 1 | 268.4 | 47.2 | 102.0 | 57.5 | agree-MP=0.79, fallback=0.11, conf=0.84 |
| jinan | anon_3_4_jinan_real_2000 | jev-typed-gate0.6 T=0.95 [Qwen2.5-7B-Instruct+distill-typed] | 1 | 268.6 | 37.5 | 101.7 | 58.2 | agree-MP=0.90, fallback=0.09, conf=0.89 |
| jinan | anon_3_4_jinan_real_2000 | jev-typed-gate0.6 T=3.86 [Qwen2.5-7B-Instruct+distill-typed+reward-dpo] | 1 | 266.6 | 41.0 | 99.5 | 57.6 | agree-MP=0.88, fallback=0.11, conf=0.86 |
| jinan | anon_3_4_jinan_real_2000 | jev-typed-gate0.6 [Qwen2.5-0.5B-Instruct] | 1 | 267.9 | 37.1 | 102.4 | 8.6 | agree-MP=0.19, fallback=1.00, conf=0.46 |
| jinan | anon_3_4_jinan_real_2000 | jev-typed-gate0.6 [Qwen2.5-7B-Instruct] | 1 | 1301.2 | 986.6 | 1187.0 | 57.0 | agree-MP=0.04, fallback=0.00, conf=0.99 |
| jinan | anon_3_4_jinan_real_2000 | jev-typed-perm2 [Qwen2.5-0.5B-Instruct] | 1 | 1294.1 | 971.3 | 1198.2 | 16.0 | agree-MP=0.04, fallback=0.00, conf=0.49 |
| jinan | anon_3_4_jinan_real_2000 | jev-typed-perm2 [Qwen2.5-7B-Instruct] | 1 | 1298.2 | 972.9 | 1188.5 | 114.7 | agree-MP=0.03, fallback=0.00, conf=0.96 |
| jinan | anon_3_4_jinan_real_2000 | jev-typed-perm4 [Qwen2.5-7B-Instruct] | 1 | 1308.4 | 996.8 | 1192.0 | 217.3 | agree-MP=0.03, fallback=0.00, conf=0.94 |
| jinan | anon_3_4_jinan_real_2000 | llm-gen [Qwen2.5-0.5B-Instruct] | 1 | 1232.0 | 732.4 | 1328.4 | 911.5 | invalid=0.86, gen-tok=986 |
| jinan | anon_3_4_jinan_real_2000 | llm-gen [Qwen2.5-7B-Instruct] | 1 | 280.3 | 40.8 | 114.2 | 2049.2 | invalid=0.01, gen-tok=461 |
| jinan | anon_3_4_jinan_real_2500 (held-out) | fixedtime | 3 | 384.6 ± 0.0 | 37.5 ± 0.0 | 297.9 ± 0.0 | - |  |
| jinan | anon_3_4_jinan_real_2500 (held-out) | random | 3 | 527.6 ± 12.8 | 104.2 ± 16.9 | 496.5 ± 23.0 | - |  |
| jinan | anon_3_4_jinan_real_2500 (held-out) | maxqueue | 3 | 261.2 ± 0.0 | 41.8 ± 0.0 | 128.3 ± 0.0 | - |  |
| jinan | anon_3_4_jinan_real_2500 (held-out) | maxpressure | 3 | 261.0 ± 0.0 | 39.2 ± 0.0 | 128.2 ± 0.0 | - |  |
| jinan | anon_3_4_jinan_real_2500 (held-out) | rollout-greedy | 1 | 261.6 | 54.6 | 128.9 | - |  |
| jinan | anon_3_4_jinan_real_2500 (held-out) | jev-raw [Qwen2.5-0.5B-Instruct] | 1 | 1103.8 | 718.9 | 1444.0 | 103.6 | agree-MP=0.04, fallback=0.00, conf=0.33 |
| jinan | anon_3_4_jinan_real_2500 (held-out) | jev-raw [Qwen2.5-7B-Instruct] | 1 | 727.9 | 566.4 | 857.3 | 701.8 | agree-MP=0.12, fallback=0.00, conf=0.79 |
| jinan | anon_3_4_jinan_real_2500 (held-out) | jev-raw-gate0.6 [Qwen2.5-0.5B-Instruct] | 1 | 261.0 | 39.2 | 128.2 | 104.9 | agree-MP=0.38, fallback=1.00, conf=0.34 |
| jinan | anon_3_4_jinan_real_2500 (held-out) | jev-raw-gate0.6 [Qwen2.5-7B-Instruct] | 1 | 427.1 | 189.3 | 374.1 | 707.7 | agree-MP=0.18, fallback=0.14, conf=0.80 |
| jinan | anon_3_4_jinan_real_2500 (held-out) | jev-score-raw [Qwen2.5-7B-Instruct] | 1 | 703.3 | 243.0 | 737.5 | 2238.1 | agree-MP=0.31 |
| jinan | anon_3_4_jinan_real_2500 (held-out) | jev-score-typed [Qwen2.5-7B-Instruct] | 1 | 444.9 | 68.8 | 380.0 | 196.3 | agree-MP=0.42 |
| jinan | anon_3_4_jinan_real_2500 (held-out) | jev-typed T=0.52 [Qwen2.5-7B-Instruct+distill-typed+reward-soft] | 1 | 263.2 | 51.6 | 132.2 | 57.5 | agree-MP=0.79, fallback=0.00, conf=0.83 |
| jinan | anon_3_4_jinan_real_2500 (held-out) | jev-typed T=0.95 [Qwen2.5-7B-Instruct+distill-typed] | 1 | 262.5 | 41.1 | 129.7 | 58.3 | agree-MP=0.90, fallback=0.00, conf=0.89 |
| jinan | anon_3_4_jinan_real_2500 (held-out) | jev-typed T=3.86 [Qwen2.5-7B-Instruct+distill-typed+reward-dpo] | 1 | 263.2 | 44.9 | 131.2 | 57.4 | agree-MP=0.88, fallback=0.00, conf=0.86 |
| jinan | anon_3_4_jinan_real_2500 (held-out) | jev-typed [Qwen2.5-0.5B-Instruct] | 1 | 1266.0 | 933.8 | 1597.5 | 8.9 | agree-MP=0.03, fallback=0.00, conf=0.49 |
| jinan | anon_3_4_jinan_real_2500 (held-out) | jev-typed [Qwen2.5-7B-Instruct] | 1 | 1154.9 | 940.3 | 1261.0 | 59.7 | agree-MP=0.03, fallback=0.00, conf=0.99 |
| jinan | anon_3_4_jinan_real_2500 (held-out) | jev-typed-gate0.6 T=0.52 [Qwen2.5-7B-Instruct+distill-typed+reward-soft] | 1 | 261.9 | 48.4 | 129.6 | 61.4 | agree-MP=0.80, fallback=0.11, conf=0.85 |
| jinan | anon_3_4_jinan_real_2500 (held-out) | jev-typed-gate0.6 T=0.95 [Qwen2.5-7B-Instruct+distill-typed] | 1 | 259.2 | 40.1 | 125.0 | 58.0 | agree-MP=0.91, fallback=0.09, conf=0.90 |
| jinan | anon_3_4_jinan_real_2500 (held-out) | jev-typed-gate0.6 T=3.86 [Qwen2.5-7B-Instruct+distill-typed+reward-dpo] | 1 | 262.5 | 44.2 | 130.6 | 58.0 | agree-MP=0.87, fallback=0.11, conf=0.86 |
| jinan | anon_3_4_jinan_real_2500 (held-out) | jev-typed-gate0.6 [Qwen2.5-0.5B-Instruct] | 1 | 261.0 | 39.2 | 128.2 | 8.9 | agree-MP=0.20, fallback=1.00, conf=0.46 |
| jinan | anon_3_4_jinan_real_2500 (held-out) | jev-typed-gate0.6 [Qwen2.5-7B-Instruct] | 1 | 1155.9 | 950.1 | 1256.2 | 60.0 | agree-MP=0.03, fallback=0.00, conf=0.99 |
| jinan | anon_3_4_jinan_real_2500 (held-out) | jev-typed-perm2 [Qwen2.5-0.5B-Instruct] | 1 | 1179.8 | 964.0 | 1283.5 | 16.7 | agree-MP=0.03, fallback=0.00, conf=0.49 |
| jinan | anon_3_4_jinan_real_2500 (held-out) | jev-typed-perm2 [Qwen2.5-7B-Instruct] | 1 | 1175.0 | 959.3 | 1271.3 | 107.9 | agree-MP=0.03, fallback=0.00, conf=0.98 |
| jinan | anon_3_4_jinan_real_2500 (held-out) | jev-typed-perm4 [Qwen2.5-7B-Instruct] | 1 | 1175.9 | 965.6 | 1271.9 | 218.2 | agree-MP=0.03, fallback=0.00, conf=0.95 |
| jinan | anon_3_4_jinan_real_2500 (held-out) | llm-gen [Qwen2.5-0.5B-Instruct] | 1 | 1174.8 | 692.0 | 1496.5 | 926.9 | invalid=0.86, gen-tok=984 |
| jinan | anon_3_4_jinan_real_2500 (held-out) | llm-gen [Qwen2.5-7B-Instruct] | 1 | 275.5 | 45.5 | 146.3 | 2068.8 | invalid=0.00, gen-tok=454 |
