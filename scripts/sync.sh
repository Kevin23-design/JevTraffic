#!/usr/bin/env bash
# Push the working tree (code, third_party, data) to the experiment server; pull results back with --pull.
# Server-only outputs (results/, logs/, records/, ckpt/, data/finetune/) are excluded, so --delete never touches them.
set -euo pipefail
cd "$(dirname "$0")/.."

REMOTE=${REMOTE:-root@202.120.87.207}
PORT=${PORT:-50030}
DIR=${DIR:-zzy/JevTraffic}

if [ "${1:-}" = "--pull" ]; then
  rsync -az -e "ssh -p $PORT" "$REMOTE:$DIR/results/" results/
  exit 0
fi
rsync -az --delete -e "ssh -p $PORT" \
  --exclude .git/ --exclude .venv/ --exclude __pycache__/ --exclude records/ --exclude results/ --exclude logs/ \
  --exclude /ckpt/ --exclude /data/finetune/ --exclude /data/sumo_finetune/ \
  --exclude 'third_party/USTBench/CityFlow/build/' --exclude '*.egg-info/' \
  --exclude /third_party/TransSimHub/docs/ --exclude /third_party/TransSimHub/examples/ \
  --exclude /third_party/TransSimHub/benchmark/ --exclude /third_party/TransSimHub/assets/ \
  ./ "$REMOTE:$DIR/"
echo "synced to $REMOTE:$DIR"
