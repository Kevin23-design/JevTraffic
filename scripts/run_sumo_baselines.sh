#!/usr/bin/env bash
# E1 + rule references on SingleTSCBaselines (CPU only, one episode per process).
#   benchmark controllers fixtime / webster / sotl / maxpressure on all 12 junctions x 10 envs, 3 SUMO seeds,
#   without events and with the junction's official event_1;
#   our MaxPressure + rule detector + event plans (mp-triggered-rule), and plain MaxPressure, under event_1 and
#   two random event sets (accident + special vehicle each).
set -uo pipefail
ulimit -c 0  # no core dumps (a crashed 7B process writes several GB)
cd "$(dirname "$0")/.."
JOBS=${JOBS:-64}
SEEDS=${SEEDS:-"0 1 2"}
mkdir -p logs/sumo_runs
J="Beijing_Beihuan Beijing_Beishahe Beijing_Changjianglu Beijing_Gaojiaoyuan Beijing_Pinganli Beijing_Yongrunlu Chengdu_Chenghannanlu Chengdu_Guanghua Tianjin_zhijingdao France_Massy SouthKorea_Songdo Hongkong_YMT"
ENVS=""; for net in easy normal; do for pat in low_density high_density fluctuating_commuter increasing_demand random_perturbation; do ENVS="$ENVS ${net}_$pat"; done; done
{
  for j in $J; do for e in $ENVS; do for s in $SEEDS; do
    for a in fixtime webster sotl maxpressure; do
      echo "$j $e $s --agent $a --events none"
      echo "$j $e $s --agent $a --events event_1"
    done
    for ev in event_1 random:1 random:2; do
      echo "$j $e $s --agent mp --events $ev"
      echo "$j $e $s --agent mp --detector rule --memory triggered --events $ev"
    done
  done; done; done
} | xargs -P "$JOBS" -L 1 bash -c \
  'log=logs/sumo_runs/$(echo "$*" | tr " :/" "___").log; .venv/bin/python run_sumo.py --junction $0 --env_name $1 --seed $2 "${@:3}" --skip_existing > $log 2>&1 || echo "FAILED $*"'
echo done
