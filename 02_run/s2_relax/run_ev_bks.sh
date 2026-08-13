#!/bin/bash
# S2'-3  BKS E-V 스캔 드라이버
#
# [1차 실패 → 수정]  7net 과 같은 부피점(f = 0.94~1.06)을 그대로 썼더니
#   BKS 의 E 최소가 f = 0.94 (구간 끝)에 걸렸다. 최소보다 조밀한 쪽 점이 1개뿐이라
#   BM3 피팅이 한쪽으로 쏠려 K0' = -10.4, RMS 29 meV 로 망가졌고
#   BM3(rho0 2.329) 와 virial(2.313) 이 0.69 % 어긋났다 (7net 은 0.007 %).
#   원인: BKS 의 평형밀도는 2.31 인데 스캔을 2.20 중심으로 잡았다.
#         → f 구간을 BKS 자기 최소 주위로 옮긴다 (rho 2.16 ~ 2.44).
# 비용: 7점 × 수 초 ≈ 1분 미만 (6랭크)

set -e
cd "$(dirname "$0")"
export OMP_NUM_THREADS=1

OUT=ev_bks_scan.txt
echo "# scale volume(A^3) density(g/cc) PE(eV) epa(eV) press(bar) maxf(eV/A)" > $OUT

for f in 0.90 0.92 0.94 0.96 0.98 1.00 1.02; do
  s=$(python3 -c "print(f'{$f**(1/3):.8f}')")
  echo "=============== f=$f  s=$s ==============="
  mpirun -np 6 lmp_7net -var s $s -in in.ev_bks -log ev_bks_f${f}.log 2>&1 | tail -2
  grep "^EVPOINT" ev_bks_f${f}.log | awk '{$1="";print}' >> $OUT
done

echo ""
echo "================= ev_bks_scan.txt ================="
cat $OUT
