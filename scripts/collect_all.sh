#!/usr/bin/env bash
# Fine-tuning data. Train / val episodes come from the TRAIN traffic files; the TEST files are held out
# entirely (only an offline test set is collected from them, never trained on).
#   train: hangzhou_real, jinan_real, jinan_real_2000   eps in {0, .1, .25, .5}, 3 seeds (eps=0 is deterministic)
#   val:   same files, eps=.1, seed 100                  (temperature calibration)
#   test:  hangzhou_real_5816, jinan_real_2500, eps=.1, seed 100 (offline accuracy / calibration check)
set -uo pipefail
cd "$(dirname "$0")/.."
JOBS=${JOBS:-48}
EXTRA=${EXTRA:-}   # e.g. --raw to also store the raw USTBench text
mkdir -p logs

TRAIN=("hangzhou anon_4_4_hangzhou_real.json" "jinan anon_3_4_jinan_real.json" "jinan anon_3_4_jinan_real_2000.json")
TEST=("hangzhou anon_4_4_hangzhou_real_5816.json" "jinan anon_3_4_jinan_real_2500.json")
{
  for c in "${TRAIN[@]}"; do
    echo "$c 0 0 train"
    for eps in 0.1 0.25 0.5; do for seed in 0 1 2; do echo "$c $eps $seed train"; done; done
    echo "$c 0.1 100 val"
  done
  for c in "${TEST[@]}"; do echo "$c 0.1 100 test"; done
} | xargs -P "$JOBS" -L 1 bash -c \
  '.venv/bin/python scripts/collect_data.py --dataset $0 --traffic_file $1 --eps $2 --seed $3 --out_dir data/finetune/$4 '"$EXTRA"' \
     > logs/collect_$4_$1_eps$2_s$3.log 2>&1 && tail -1 logs/collect_$4_$1_eps$2_s$3.log || echo "FAILED $0 $1 $2 $3"'
