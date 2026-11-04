#!/usr/bin/env bash
# Fetch USTBench (environment code + bundled CityFlow) at a pinned commit and the TSC data.
# Run locally (the experiment server cannot reach GitHub); scripts/sync.sh then copies everything over.
set -euo pipefail
cd "$(dirname "$0")/.."

USTBENCH_COMMIT=ee3978f9846c7e69b0b3608b75ffee551daa8117
SINGLETSC_COMMIT=3147aa9aef16e5c78f83a557d2935a41c1fde079   # SUMO single-intersection benchmark (v2 experiments)
TSHUB_COMMIT=bc1c814f3ee0fe04aa95938bd3bf727cbe7adf2a       # TransSimHub as of SingleTSCBaselines' date (later commits rename obs["lane"])
HF=${HF_ENDPOINT:-https://huggingface.co}

if [ ! -d third_party/USTBench ]; then
  git clone -q https://github.com/usail-hkust/USTBench third_party/USTBench
fi
git -C third_party/USTBench checkout -q "$USTBENCH_COMMIT"
for spec in "SingleTSCBaselines Traffic-Alpha/SingleTSCBaselines $SINGLETSC_COMMIT" "TransSimHub Traffic-Alpha/TransSimHub $TSHUB_COMMIT"; do
  set -- $spec
  [ -d "third_party/$1" ] || git clone -q "https://github.com/$2" "third_party/$1"
  git -C "third_party/$1" fetch -q --depth 1 origin "$3" 2>/dev/null || true
  git -C "third_party/$1" checkout -q "$3"
done

files=(
  Hangzhou/4_4/roadnet_4_4.json Hangzhou/4_4/anon_4_4_hangzhou_real.json Hangzhou/4_4/anon_4_4_hangzhou_real_5816.json
  Jinan/3_4/roadnet_3_4.json Jinan/3_4/anon_3_4_jinan_real.json Jinan/3_4/anon_3_4_jinan_real_2000.json
  Jinan/3_4/anon_3_4_jinan_real_2500.json task_info.json
)
for f in "${files[@]}"; do
  [ -s "data/tsc/$f" ] && continue
  mkdir -p "data/tsc/$(dirname "$f")"
  curl -sfL -o "data/tsc/$f" "$HF/datasets/Haruto2099/USTBench-Dataset/resolve/main/traffic_signal_control/Data/$f"
done
echo "third_party/{USTBench,SingleTSCBaselines,TransSimHub} and data/tsc ready"
