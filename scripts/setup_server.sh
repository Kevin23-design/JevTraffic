#!/usr/bin/env bash
# One-time server setup: a venv layered on the existing vLLM conda env (torch / transformers / vLLM),
# plus CityFlow built from USTBench's bundled source. Models are downloaded through hf-mirror.
set -euo pipefail
cd "$(dirname "$0")/.."

BASE_PY=${BASE_PY:-/opt/conda/envs/vllm_qwen3_cu124/bin/python}
MODELS=${MODELS:-$HOME/zzy/hf_models}

if [ ! -x .venv/bin/python ]; then
  "$BASE_PY" -m venv --system-site-packages .venv
fi
.venv/bin/python -c "import cityflow" 2>/dev/null || LDFLAGS="-static-libstdc++ -static-libgcc" .venv/bin/pip install -q ./third_party/USTBench/CityFlow  # conda libstdc++ is older than the system g++
.venv/bin/python -c "import cityflow, torch, transformers, vllm; print('cityflow ok | torch', torch.__version__, '| transformers', transformers.__version__, '| vllm', vllm.__version__)"

mkdir -p "$MODELS"
for m in ${DOWNLOAD_MODELS:-Qwen/Qwen2.5-7B-Instruct}; do
  [ -f "$MODELS/$(basename "$m")/config.json" ] && [ -z "$(ls "$MODELS/$(basename "$m")"/*.incomplete 2>/dev/null)" ] && continue
  HF_ENDPOINT=${HF_ENDPOINT:-https://hf-mirror.com} "$(dirname "$BASE_PY")/huggingface-cli" download "$m" --local-dir "$MODELS/$(basename "$m")"
done
