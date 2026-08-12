#!/bin/bash
# S2'-2  E-V 스캔 드라이버 (새 ρ=2.20 네트워크)
#   f = 부피비, s = f^(1/3).  ρ = 2.20/f 이므로
#   f = 0.94 0.96 0.98 1.00 1.02 1.04 1.06  →  ρ = 2.340 2.292 2.245 2.200 2.157 2.115 2.075
#   예상 ρ0 ≈ 2.21~2.22 (f ≈ 0.995)로 구간 한가운데.
# 비용: 7점 × 최대 150 eval × 1.99 s ≈ 35분

set -e
cd "$(dirname "$0")"
ulimit -s 262144
export OMP_NUM_THREADS=6 MKL_NUM_THREADS=6

OUT=ev220_scan.txt
echo "# scale volume(A^3) density(g/cc) PE(eV) epa(eV) press(bar) maxf(eV/A)" > $OUT

for f in 0.94 0.96 0.98 1.00 1.02 1.04 1.06; do
  s=$(python3 -c "print(f'{$f**(1/3):.8f}')")
  echo "=============== f=$f  s=$s ==============="
  lmp_7net -var s $s -in in.ev220 -log ev220_f${f}.log 2>&1 | tail -3
  grep "^EVPOINT" ev220_f${f}.log | awk '{$1="";print}' >> $OUT
done

echo ""
echo "================= ev220_scan.txt ================="
cat $OUT
