#!/usr/bin/env bash
# Fetch USTBench (environment code + bundled CityFlow) at a pinned commit and the TSC data.
# Run locally (the experiment server cannot reach GitHub); scripts/sync.sh then copies everything over.
set -euo pipefail
cd "$(dirname "$0")/.."

USTBENCH_COMMIT=ee3978f9846c7e69b0b3608b75ffee551daa8117
HF=${HF_ENDPOINT:-https://huggingface.co}

if [ ! -d third_party/USTBench ]; then
  git clone -q https://github.com/usail-hkust/USTBench third_party/USTBench
fi
git -C third_party/USTBench checkout -q "$USTBENCH_COMMIT"

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
echo "third_party/USTBench @ $USTBENCH_COMMIT and data/tsc ready"
