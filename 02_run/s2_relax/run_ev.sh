#!/bin/bash
# S2-2  E-V 스캔 드라이버
# 기준 V0 = 28552.472 A^3 (relaxed_final.data). 부피비 f 에 대해 선형 스케일 s = f^(1/3).
#   f = 0.96 0.98 1.00 1.02 1.04 1.06 1.08  →  ρ = 2.621 ~ 2.330 g/cm^3
# 예상 부피점당 40~150 eval × 2.44 s = 2~6분, 7점 총 15~43분.

set -e
cd "$(dirname "$0")"
ulimit -s 262144
export OMP_NUM_THREADS=6 MKL_NUM_THREADS=6

OUT=ev_scan.txt
echo "# scale volume(A^3) density(g/cc) PE(eV) epa(eV) press(bar) maxf(eV/A)" > $OUT

for f in 0.96 0.98 1.00 1.02 1.04 1.06 1.08; do
  s=$(python3 -c "print(f'{$f**(1/3):.8f}')")
  echo "=============== f=$f  s=$s ==============="
  lmp_7net -var s $s -in in.ev -log ev_f${f}.log 2>&1 | tail -3
  grep "^EVPOINT" ev_f${f}.log | awk '{$1="";print}' >> $OUT
done

echo ""
echo "================= ev_scan.txt ================="
cat $OUT
