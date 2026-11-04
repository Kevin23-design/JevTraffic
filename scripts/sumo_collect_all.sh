#!/usr/bin/env bash
# v2 fine-tuning data on SingleTSCBaselines (one episode per process; tshub cannot switch junctions in-process).
#   train:          9 train junctions x {easy,normal} x 4 patterns x eps {0,.1,.3} x seeds {0,1}
#   val:            same junctions/patterns, eps .1, seed 100            (temperature calibration)
#   test_pattern:   train junctions, held-out pattern random_perturbation (offline accuracy)
#   test_junction:  held-out junctions France_Massy / SouthKorea_Songdo / Hongkong_YMT, all patterns
set -uo pipefail
ulimit -c 0  # no core dumps (a crashed 7B process writes several GB)
cd "$(dirname "$0")/.."
JOBS=${JOBS:-64}
mkdir -p logs/sumo_collect
TRAIN="Beijing_Beihuan Beijing_Beishahe Beijing_Changjianglu Beijing_Gaojiaoyuan Beijing_Pinganli Beijing_Yongrunlu Chengdu_Chenghannanlu Chengdu_Guanghua Tianjin_zhijingdao"
HELDOUT="France_Massy SouthKorea_Songdo Hongkong_YMT"
PATTERNS="low_density high_density fluctuating_commuter increasing_demand"
{
  for j in $TRAIN; do for net in easy normal; do
    for pat in $PATTERNS; do
      for eps in 0 0.1 0.3; do for seed in 0 1; do echo "$j ${net}_$pat $eps $seed train"; done; done
      echo "$j ${net}_$pat 0.1 100 val"
    done
    echo "$j ${net}_random_perturbation 0.1 100 test_pattern"
  done; done
  for j in $HELDOUT; do for net in easy normal; do for pat in $PATTERNS random_perturbation; do
    echo "$j ${net}_$pat 0.1 100 test_junction"
  done; done; done
} | xargs -P "$JOBS" -L 1 bash -c \
  'log=logs/sumo_collect/$4__$0__$1__eps$2__s$3.log; .venv/bin/python scripts/sumo_collect.py --junction $0 --env_name $1 --eps $2 --seed $3 --out_dir data/sumo_finetune/$4 > $log 2>&1 && tail -1 $log | cut -c1-160 || echo "FAILED $*"'
