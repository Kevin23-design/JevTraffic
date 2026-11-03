#!/usr/bin/env bash
# Evaluate fine-tuned adapters online on all traffic files (train files + held-out hangzhou_5816 / jinan_2500).
#   ADAPTERS="ckpt/distill-typed" GPUS="4 6" bash scripts/run_finetuned.sh
#   ADAPTERS="ckpt/distill-typed ckpt/reward-soft" ...        (stage-2 adapter on top of stage 1)
# The calibrated temperature in <last adapter>/calib.json is used automatically when present.
set -uo pipefail
cd "$(dirname "$0")/.."
MODEL=${MODEL:-$HOME/zzy/hf_models/Qwen2.5-7B-Instruct}
ADAPTERS=${ADAPTERS:?set ADAPTERS}
GPUS=(${GPUS:-0})
TAUS=${TAUS:-"0 0.6"}
FILES=${FILES:-"hangzhou:anon_4_4_hangzhou_real.json hangzhou:anon_4_4_hangzhou_real_5816.json jinan:anon_3_4_jinan_real.json jinan:anon_3_4_jinan_real_2000.json jinan:anon_3_4_jinan_real_2500.json"}
mkdir -p logs
tagname=$(for a in $ADAPTERS; do basename "$a"; done | paste -sd+)

jobs=()
for tau in $TAUS; do for f in $FILES; do jobs+=("${f%%:*} ${f#*:} $tau"); done; done
for g in "${!GPUS[@]}"; do
  (
    for k in "${!jobs[@]}"; do
      [ $((k % ${#GPUS[@]})) -eq "$g" ] || continue
      set -- ${jobs[$k]}
      log="logs/ft_${tagname}_${2%.json}_gate$3.log"
      CUDA_VISIBLE_DEVICES=${GPUS[$g]} .venv/bin/python run_tsc.py --dataset "$1" --traffic_file "$2" --model "$MODEL" \
        --adapters $ADAPTERS --agent jev --state_format typed --gate_tau "$3" --batch_size 32 --save_steps --skip_existing \
        > "$log" 2>&1 && echo "done $* $tagname" || echo "FAILED $* $tagname ($log)"
    done
  ) &
done
wait
