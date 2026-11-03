#!/usr/bin/env bash
# Rule-based baselines on every Hangzhou / Jinan traffic file, several simulator seeds, in parallel (CPU only).
set -uo pipefail
cd "$(dirname "$0")/.."
SEEDS=${SEEDS:-"0 1 2"}
JOBS=${JOBS:-32}
mkdir -p logs

cases=(
  "hangzhou anon_4_4_hangzhou_real.json" "hangzhou anon_4_4_hangzhou_real_5816.json"
  "jinan anon_3_4_jinan_real.json" "jinan anon_3_4_jinan_real_2000.json" "jinan anon_3_4_jinan_real_2500.json"
)
for c in "${cases[@]}"; do
  set -- $c
  for agent in fixedtime random maxqueue maxpressure; do
    for seed in $SEEDS; do
      echo "$1 $2 $agent $seed"
    done
  done
done | xargs -P "$JOBS" -L 1 bash -c \
  '.venv/bin/python run_tsc.py --dataset $0 --traffic_file $1 --agent $2 --seed $3 > logs/$0_$1_$2_s$3.log 2>&1 && echo "done $0 $1 $2 s$3" || echo "FAILED $0 $1 $2 s$3"'
