#!/bin/bash
# S2'-3  BKS E-V 스캔 드라이버 — 7net(run_ev220.sh) 과 동일한 부피점.
# 비용: 7점 × 수 초 ≈ 1분 미만 (6랭크)

set -e
cd "$(dirname "$0")"
export OMP_NUM_THREADS=1

OUT=ev_bks_scan.txt
echo "# scale volume(A^3) density(g/cc) PE(eV) epa(eV) press(bar) maxf(eV/A)" > $OUT

for f in 0.94 0.96 0.98 1.00 1.02 1.04 1.06; do
  s=$(python3 -c "print(f'{$f**(1/3):.8f}')")
  echo "=============== f=$f  s=$s ==============="
  mpirun -np 6 lmp_7net -var s $s -in in.ev_bks -log ev_bks_f${f}.log 2>&1 | tail -2
  grep "^EVPOINT" ev_bks_f${f}.log | awk '{$1="";print}' >> $OUT
done

echo ""
echo "================= ev_bks_scan.txt ================="
cat $OUT
