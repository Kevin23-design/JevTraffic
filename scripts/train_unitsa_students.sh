#!/usr/bin/env bash
# v3: distil the UniTSA teacher into small Jev students (keep/switch, soft targets) + the situation question.
#   GPU=6 STUDENTS="0.5B:compact 0.5B:full 1.5B:compact" bash scripts/train_unitsa_students.sh
# Each student trains on one GPU (all in parallel), then its temperatures are calibrated on the val split.
set -uo pipefail
ulimit -c 0
cd "$(dirname "$0")/.."
GPU=${GPU:-6}
STUDENTS=${STUDENTS:-"0.5B:compact 0.5B:full 1.5B:compact"}
LR=${LR:-2e-4}
mkdir -p logs/v3
for s in $STUDENTS; do
  size=${s%%:*}; fmt=${s#*:}
  field=state; [ "$fmt" = compact ] && field=state_compact
  model=$HOME/zzy/hf_models/Qwen2.5-$size-Instruct
  out=ckpt/unitsa-jev-$size-$fmt
  (
    CUDA_VISIBLE_DEVICES=$GPU .venv/bin/python scripts/train_lora.py --model "$model" \
      --train "data/sumo_unitsa/train/*.jsonl" "data/sumo_finetune/train/*.jsonl" --kinds switch situation \
      --loss soft --state_field $field --lr $LR --batch_size 16 --save_every 1000 --out $out \
      > logs/v3/train_$size-$fmt.log 2>&1 &&
    CUDA_VISIBLE_DEVICES=$GPU .venv/bin/python scripts/sumo_calibrate.py --model "$model" --adapters $out \
      --fit "data/sumo_unitsa/val/*.jsonl" "data/sumo_finetune/val/*.jsonl" --state_field $field \
      --eval "data/sumo_unitsa/test_junction/*.jsonl" "data/sumo_unitsa/test_pattern/*.jsonl" \
      > logs/v3/calib_$size-$fmt.log 2>&1 && echo "done $s" || echo "FAILED $s"
  ) &
done
wait
echo STUDENTS_DONE
