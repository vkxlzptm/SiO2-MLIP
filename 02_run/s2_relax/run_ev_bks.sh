#!/bin/bash
# S2'-3  BKS E-V 스캔 드라이버
#
# [1차 실패 → 수정]  7net 과 같은 부피점(f = 0.94~1.06)을 그대로 썼더니
#   BKS 의 E 최소가 f = 0.94 (구간 끝)에 걸렸다. 최소보다 조밀한 쪽 점이 1개뿐이라
#   BM3 피팅이 한쪽으로 쏠려 K0' = -10.4, RMS 29 meV 로 망가졌고
#   BM3(rho0 2.329) 와 virial(2.313) 이 0.69 % 어긋났다 (7net 은 0.007 %).
#   원인: BKS 의 평형밀도는 2.31 인데 스캔을 2.20 중심으로 잡았다.
#         → f 구간을 BKS 자기 최소 주위로 옮긴다 (rho 2.16 ~ 2.44).
#
# [2차도 실패 → 3차]  창을 옮겨도 RMS 86 meV, BM3 vs virial 0.70 % 로 여전했다.
#   PPPM 정밀도를 의심해 1.0e-4 -> 1.0e-6 으로 조였다.
#
# [3차: PPPM 가설 기각]  거의 안 변했다 (RMS 86->56 meV, 불일치 0.70->0.64 %).
#   원자료를 직접 중앙차분해 보니 (-dE/dV) - P_virial 이 모든 부피에서 -2100~-2800 bar 의
#   **거의 일정한 오프셋**이었다. 잡음이 아니라 계통오차다.
#   → 원인은 10 A 에서 뚝 잘린 Buckingham -C/r^6 꼬리. in.ev_bks 주석에 정량 검증.
#   → 포텐셜은 그대로 두고, K0 를 virial P(V) 의 BM3 피팅으로 뽑는다 (fig_density.py).
#
# 사용법:
#   ./run_ev_bks.sh          # 생산 (tail 0, MD 와 같은 포텐셜)
#   ./run_ev_bks.sh 1        # 대조군 (tail yes). 진단이 맞다면 불일치가 크게 줄어야 한다.
#
# ※ f 는 항상 sio2_bks220.data(rho=2.20, V=32652.49 A^3) 기준 부피비다.
#   1차 실행이 남긴 ev_bks_f1.04.log / f1.06.log 는 정의는 같지만 지금 스캔 목록 밖이라
#   혼동을 피하려면 지울 것.
# 비용: 7점 × 수 초 ≈ 1분 미만 (6랭크)

set -e
cd "$(dirname "$0")"
export OMP_NUM_THREADS=1

TAIL=${1:-0}
SUF=""; [ "$TAIL" = "1" ] && SUF="_tail"

OUT=ev_bks_scan${SUF}.txt
echo "# scale volume(A^3) density(g/cc) PE(eV) epa(eV) press(bar) maxf(eV/A)" > $OUT

for f in 0.90 0.92 0.94 0.96 0.98 1.00 1.02; do
  s=$(python3 -c "print(f'{$f**(1/3):.8f}')")
  echo "=============== f=$f  s=$s  tail=$TAIL ==============="
  mpirun -np 6 lmp_7net -var s $s -var tail $TAIL \
         -in in.ev_bks -log ev_bks_f${f}${SUF}.log 2>&1 | tail -2
  grep "^EVPOINT" ev_bks_f${f}${SUF}.log | awk '{$1="";print}' >> $OUT
done

echo ""
echo "================= ev_bks_scan.txt ================="
cat $OUT
