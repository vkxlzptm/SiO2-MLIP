#!/bin/bash
# S4-EV(BKS) 드라이버 — 매칭 냉각률(2e13) BKS 망의 0 K E-V.
#
# 7net 쪽(run_ev_s4.sh)은 1스텝 2초라 pilot 으로 V0 를 먼저 찾아 점을 아꼈지만,
# BKS 는 **점당 수 초**라 그럴 이유가 없다. 넉넉한 격자를 한 번에 훑고
# 피팅이 V0 를 찾게 한다.
#
# 격자: f = 0.86 ~ 1.02 (9점), rho = 2.558 ~ 2.157.
#   BKS 평형밀도는 2.34 근처(s0 에서 2.3442)이므로 f0 ~ 0.94 -> **격자 정중앙**.
#   V/V0 = 0.915 ~ 1.085 로 대칭. 기존 ev_bks_scan_tail(2압축/5팽창) 보다 낫다.
#   비교용으로 창을 좁히고 싶으면 피팅 단계에서 부분집합을 쓰면 된다(점이 이미 있으므로).
#
# 비용: 9점 × 수 초 ≈ 1분
# 실행:
#   cd ~/projects/lammps_tutorial/SiO2-MLIP/02_run/s4_mq7net
#   bash run_ev_bks_s4.sh                      # prod_bks_2e13.data, tail on
#   bash run_ev_bks_s4.sh prod_bks_5e12.data bks5e12    # 다른 구조도 가능
set -e
cd "$(dirname "$0")"
export OMP_NUM_THREADS=1

mkdir -p logs ev

DFILE=${1:-prod_bks_2e13.data}
TAG=${2:-bks2e13}
TAIL=${3:-1}

OUT="ev/ev_s4_${TAG}_scan.txt"
{ echo "# S4 E-V scan (BKS potential): ${DFILE}   tail=${TAIL}"
  echo "# grid f = 0.86..1.02 (9 pts), symmetric about expected V0 (f0 ~ 0.94)"
  echo "# scale volume(A^3) density(g/cc) PE(eV) epa(eV) press(bar) maxf(eV/A)"
} > "$OUT"

for f in 0.86 0.88 0.90 0.92 0.94 0.96 0.98 1.00 1.02; do
  s=$(python3 -c "print(f'{$f**(1/3):.8f}')")
  lg="logs/ev_s4_${TAG}_f${f}.log"
  echo "--- ${TAG}  f=${f}  s=${s}" >&2
  mpirun -np 6 lmp_7net -var s "$s" -var dfile "$DFILE" -var tag "$TAG" -var tail "$TAIL" \
         -in in.ev_bks_s4 -log "$lg" 2>&1 | tail -2 >&2
  grep "^EVPOINT" "$lg" | awk '{$1="";print}' >> "$OUT"
done

echo ""
echo "================= $OUT ================="
cat "$OUT"
echo ""
echo "다음: python3 ../../04_analysis/src/ev_s4_summary.py"
