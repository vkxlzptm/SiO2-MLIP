#!/bin/bash
# S4-EV 드라이버 — S4 자체 melt-quench 망의 0 K 평형밀도/체적탄성률
#
#   f = 부피비, s = f^(1/3).  rho = 2.20/f
#   f = 0.94 .. 1.10  ->  rho = 2.340 .. 2.000
#   ★ in.ev220(f=0.94~1.06) 보다 팽창쪽으로 두 점 넓혔다. 7net 자체 망의 P300 이
#     +0.80 GPa(팽창 경향)라 rho0 가 2.16 근처로 예상되는데, 원래 창(2.157 이 하한)
#     이면 평형점이 창 끝에 걸린다. RESULTS 2절이 "끝점이 곡률의 곡률을 정한다"고
#     경고한 그 상황이다. 평형점이 창 한가운데 오도록 넓힌다.
#   ※ 비교 대상인 기존 7net 스캔(ev220_scan.txt)은 f=0.94~1.06 이므로, 겹치는
#     구간만으로도 BM3 피팅은 비교 가능하다. 창이 다른 점은 보고할 때 병기할 것.
#
# 비용: 9점 x 최대 150 eval x 1.99 s ≈ 45분 (7net). BKS 대조는 별도 (in.ev_bks, 수 분).
# 실행:
#   cd ~/projects/lammps_tutorial/SiO2-MLIP/02_run/s4_mq7net
#   setsid nohup bash run_ev_s4.sh > ev_s4_chain.log 2>&1 < /dev/null &
set -e
cd "$(dirname "$0")"
ulimit -s 262144
export OMP_NUM_THREADS=6 MKL_NUM_THREADS=6

exec 9>/tmp/.s4_ev_scan.lock
flock -n 9 || { echo "이미 실행 중이다. 중복 실행 차단."; exit 1; }

mkdir -p logs ev

DFILE=${1:-prod_7net_mq.data}
TAG=${2:-7net}

OUT="ev/ev_s4_${TAG}_scan.txt"
echo "# S4 self-quenched topology E-V scan: ${DFILE}" > "$OUT"
echo "# scale volume(A^3) density(g/cc) PE(eV) epa(eV) press(bar) maxf(eV/A)" >> "$OUT"

for f in 0.94 0.96 0.98 1.00 1.02 1.04 1.06 1.08 1.10; do
  s=$(python3 -c "print(f'{$f**(1/3):.8f}')")
  echo "=============== ${TAG}  f=$f  s=$s ==============="
  lmp_7net -var s "$s" -var dfile "$DFILE" -var tag "$TAG" \
           -in in.ev_s4 -log "logs/ev_s4_${TAG}_f${f}.log" 2>&1 | tail -3
  grep "^EVPOINT" "logs/ev_s4_${TAG}_f${f}.log" | awk '{$1="";print}' >> "$OUT"
done

echo ""
echo "================= $OUT ================="
cat "$OUT"
echo ""
echo "다음: python3 ../../04_analysis/src/fig_density.py 계열로 BM3 피팅"
