#!/usr/bin/env bash
# E5: 14 simulated days on the held-out junctions under each adaptation policy (one process per job, one GPU each;
# a process frees its decider while it fine-tunes a junction adapter).
#   SHARED=ckpt/sumo-distill GPUS="6 7" bash scripts/run_days_all.sh
set -uo pipefail
ulimit -c 0
cd "$(dirname "$0")/.."
SHARED=${SHARED:-ckpt/sumo-distill}
GPUS=(${GPUS:-6 7})  # our allocation on the shared server: GPUs 6 and 7
DAYS=${DAYS:-14}
mkdir -p logs/days
jobs=()
for mode in daily weekly auto off; do for j in France_Massy SouthKorea_Songdo Hongkong_YMT; do jobs+=("$j $mode"); done; done
for g in "${!GPUS[@]}"; do
  (
    for k in "${!jobs[@]}"; do
      [ $(( k % ${#GPUS[@]} )) -eq "$g" ] || continue
      set -- ${jobs[$k]}
      CUDA_VISIBLE_DEVICES=${GPUS[$g]} .venv/bin/python scripts/run_days.py --junction "$1" --adapt "$2" \
        --shared "$SHARED" --days "$DAYS" > "logs/days/$1_$2.log" 2>&1 && echo "done $1 $2" || echo "FAILED $1 $2"
    done
  ) &
done
wait
echo ALLDONE
