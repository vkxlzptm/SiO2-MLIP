#!/bin/bash
# BKS 통제런 3종 — 급랭률 5e12 / 2e13 / 5e13 K/s
# 총 약 33분. 7net 본런을 시작하기 '전에' 끝내라 (동시 실행 시 대역폭 포화로 양쪽이 느려짐).
set -e
cd "$(dirname "$0")"

export OMP_NUM_THREADS=1

#        ns      tag     예상 시간
#     20000     5e12     ~22 min   (기존 BKS 220 런과 동일 급랭률)
#      5000     2e13     ~6 min    (★ 7net 본런의 짝)
#      2000     5e13     ~2 min

run() {
  local ns=$1 tag=$2
  echo "=== BKS control: ${tag} K/s  (ns=${ns}) ==="
  mpirun -np 6 lmp_7net -in in.mqbks -var ns "${ns}" -var tag "${tag}" \
      > "mqbks_${tag}.log" 2>&1
  tail -3 "mqbks_${tag}.log"
}

run 20000 5e12
run  5000 2e13
run  2000 5e13

echo "=== ALL BKS CONTROLS DONE ==="
ls -la mqbks_*_profile.dat rdf_bks_*.dat traj_bks_*.lammpstrj
