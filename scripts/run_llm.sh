#!/usr/bin/env bash
# LLM controllers (Jev-style typed decider variants + generative System-Two baseline) on every traffic file.
# Jobs (models x variants x files) are spread round-robin over GPUS; each GPU runs its share sequentially,
# one job at a time. Finished runs are skipped, failed ones retried once (the GPUs are shared with other users).
#   MODELS="$HOME/zzy/hf_models/Qwen2.5-7B-Instruct" GPUS="0 1 2 3" bash scripts/run_llm.sh
set -uo pipefail
cd "$(dirname "$0")/.."
MODELS=${MODELS:-$HOME/zzy/hf_models/Qwen2.5-7B-Instruct}
GPUS=(${GPUS:-0 1 2 3 4 5 6})
VARIANTS=${VARIANTS:-"jev-raw jev-typed jev-typed-perm2 jev-raw-gate jev-typed-gate llm-gen"}
FILES=${FILES:-"hangzhou:anon_4_4_hangzhou_real.json hangzhou:anon_4_4_hangzhou_real_5816.json jinan:anon_3_4_jinan_real.json jinan:anon_3_4_jinan_real_2000.json jinan:anon_3_4_jinan_real_2500.json"}
TAU=${TAU:-0.6}
mkdir -p logs

variant_args() {
  case $1 in
    jev-raw)          echo "--agent jev --state_format raw --batch_size 8" ;;
    jev-typed)        echo "--agent jev --state_format typed" ;;
    jev-typed-perm2)  echo "--agent jev --state_format typed --permutations 2 --tag perm2" ;;
    jev-typed-perm4)  echo "--agent jev --state_format typed --permutations 4 --tag perm4" ;;
    jev-raw-perm4)    echo "--agent jev --state_format raw --permutations 4 --batch_size 8 --tag perm4" ;;
    jev-score-typed)  echo "--agent jev-score --state_format typed --batch_size 32" ;;
    jev-score-raw)    echo "--agent jev-score --state_format raw --batch_size 8" ;;
    jev-raw-gate)     echo "--agent jev --state_format raw --batch_size 8 --gate_tau $TAU" ;;
    jev-typed-gate)   echo "--agent jev --state_format typed --gate_tau $TAU" ;;
    llm-gen)          echo "--agent llm-gen" ;;
    *) echo "unknown variant $1" >&2; exit 2 ;;
  esac
}

jobs=()
for m in $MODELS; do
  for v in $VARIANTS; do
    for f in $FILES; do
      jobs+=("${f%%:*} ${f#*:} $v $m")
    done
  done
done

for g in "${!GPUS[@]}"; do
  (
    for k in "${!jobs[@]}"; do
      [ $((k % ${#GPUS[@]})) -eq "$g" ] || continue
      set -- ${jobs[$k]}
      log="logs/llm_${1}_${2%.json}_${3}_$(basename "$4").log"
      for attempt in 1 2; do
        CUDA_VISIBLE_DEVICES=${GPUS[$g]} .venv/bin/python run_tsc.py --dataset "$1" --traffic_file "$2" --model "$4" \
          --save_steps --skip_existing $(variant_args "$3") > "$log" 2>&1 && { echo "done $1 $2 $3 $(basename "$4")"; break; }
        echo "FAILED (attempt $attempt) $1 $2 $3 $(basename "$4") ($log)"
        sleep 60
      done
    done
  ) &
done
wait
