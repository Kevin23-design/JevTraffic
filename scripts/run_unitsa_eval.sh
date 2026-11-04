#!/usr/bin/env bash
# v3: evaluate UniTSA models in our harness (CPU, one episode per process), same scenarios / seeds / events as E1-E4.
#   MODELS="universal" bash scripts/run_unitsa_eval.sh                       # all 12 junctions
#   MODELS="scratch ft" JUNCTIONS="France_Massy ..." bash scripts/run_unitsa_eval.sh   # per-junction models
# A model name "scratch"/"ft" resolves to ckpt/unitsa/<name>_<junction>/model.zip.
set -uo pipefail
ulimit -c 0
cd "$(dirname "$0")/.."
export CUDA_VISIBLE_DEVICES=
JOBS=${JOBS:-40}
SEEDS=${SEEDS:-"0 1 2"}
MODELS=${MODELS:-universal}
EVENTS=${EVENTS:-"none event_1 random:1 random:2"}
J=${JUNCTIONS:-"Beijing_Beihuan Beijing_Beishahe Beijing_Changjianglu Beijing_Gaojiaoyuan Beijing_Pinganli Beijing_Yongrunlu Chengdu_Chenghannanlu Chengdu_Guanghua Tianjin_zhijingdao France_Massy SouthKorea_Songdo Hongkong_YMT"}
ENVS=""; for net in easy normal; do for pat in low_density high_density fluctuating_commuter increasing_demand random_perturbation; do ENVS="$ENVS ${net}_$pat"; done; done
mkdir -p logs/sumo_unitsa
{
  for m in $MODELS; do for j in $J; do
    path=ckpt/unitsa/$m/model.zip; [ "$m" = universal ] || path=ckpt/unitsa/${m}_$j/model.zip
    [ -f "$path" ] || { echo "missing $path" >&2; continue; }
    for e in $ENVS; do for s in $SEEDS; do for ev in $EVENTS; do
      echo "$j $e $s $ev $path"
    done; done; done
  done; done
} | xargs -P "$JOBS" -L 1 bash -c \
  'log=logs/sumo_unitsa/$(echo "$*" | tr " :/" "___").log; .venv/bin/python run_sumo.py --junction $0 --env_name $1 --seed $2 --events $3 --agent unitsa --unitsa_model $4 --skip_existing > $log 2>&1 || echo "FAILED $*"'
echo done
