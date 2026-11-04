#!/usr/bin/env bash
# v3 UniTSA models: SUMO workers on CPU, PPO update on GPU 6 (universal) / 7 (per junction); ~2 GB GPU memory each.
#   universal (9 training junctions, 2M steps), from scratch on each held-out junction (300k), then per-junction
#   fine-tunes from the universal model (300k) -> ckpt/unitsa/{universal,scratch_<J>,ft_<J>}
set -uo pipefail
ulimit -c 0
cd "$(dirname "$0")/.."
T=scripts/train_unitsa.py; P=.venv/bin/python
mkdir -p logs/unitsa
CUDA_VISIBLE_DEVICES=6 $P $T --junctions train --copies 2 --total_timesteps 2000000 --device cuda --out ckpt/unitsa/universal > logs/unitsa/universal.log 2>&1 &
for j in France_Massy SouthKorea_Songdo Hongkong_YMT; do
  CUDA_VISIBLE_DEVICES=7 $P $T --junctions $j --copies 4 --total_timesteps 300000 --device cuda --out ckpt/unitsa/scratch_$j > logs/unitsa/scratch_$j.log 2>&1 &
done
wait; echo SCRATCH_AND_UNIVERSAL_DONE
for j in France_Massy SouthKorea_Songdo Hongkong_YMT Beijing_Beihuan Beijing_Changjianglu Chengdu_Guanghua; do
  CUDA_VISIBLE_DEVICES=7 $P $T --junctions $j --copies 4 --total_timesteps 300000 --device cuda --init ckpt/unitsa/universal/model.zip --out ckpt/unitsa/ft_$j > logs/unitsa/ft_$j.log 2>&1 &
done
wait; echo ALL_TRAIN_DONE
