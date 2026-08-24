#!/bin/bash
# S4-EV 드라이버 — S4 자체 melt-quench 망의 0 K 평형밀도/체적탄성률
#
# ─ 2단계 구조인 이유 (2026-08-24 재설계) ──────────────────────────────────────
#  E-V 스캔은 **평형부피 V0 를 중심으로 대칭**으로 점을 찍는 것이 원칙이다.
#  V0 가 창 끝에 걸리면 BM3 의 곡률(K0)과 곡률의 곡률(K0')을 한쪽 가지로만 결정하게 되고,
#  RESULTS 2절이 "끝점이 곡률의 곡률을 결정한다"고 경고한 상황이 그대로 재현된다.
#
#  그런데 이번 구조의 V0 를 **모른다.** 300 K 에서 P = +0.80 GPa 이고 K ~ 43 GPa 이니
#  rho0 ~ 2.16 이겠거니 하는 선형 외삽은 있지만, 실리카는 K0' < 0(이상 압축거동)이라
#  선형 외삽이 계통적으로 치우친다. 추정값으로 창을 잡으면 대칭인 척만 하게 된다.
#
#  -> 1단계에서 3점만 찍어 **P = 0 을 실측으로 괄호친 뒤**, 2단계에서 그 V0 를 중심으로
#     대칭 격자를 생성한다. 1단계 비용은 3점 x ~5분 = 15분뿐이다.
#
# ─ 창 폭을 ±6 % 로 잡는 근거 ─────────────────────────────────────────────────
#  비교 대상인 기존 7net 스캔(s2_relax/ev220_scan.txt)은 자기 V0 기준 -5.2 % ~ +6.9 %
#  (3압축/4팽창)다. BM3 의 K0 는 피팅 창에 의존하므로 창이 다르면 "위상 형성 효과"에
#  창 효과가 섞인다. 다만 실측으로 확인한 결과 그 영향은 **7net 에서는 무시할 수준**이다:
#      ev220 전 7점      : rho0 2.2185, K0 43.23, K0' -2.02
#      V0 대칭 부분집합  : rho0 2.2186, K0 43.17, K0' -1.93   -> K0 이동 -0.2 %
#  (BKS 는 -3.4 % 로 크게 움직이는데, 그건 창 때문이 아니라 절단 꼬리 artifact 다.
#   RESULTS 2절 "BKS 잔차가 - + + + - - + 로 구조를 갖는다" 참조.)
#  -> 창 폭은 기존 스캔과 같은 자릿수(±6 %)로 맞추되, 중심만 대칭으로 바로잡는다.
#
# 비용: 1단계 3점 + 2단계 7점 = 10점 x <=150 eval x 1.99 s ≈ 50분 (7net).
# 실행:
#   cd ~/projects/lammps_tutorial/SiO2-MLIP/02_run/s4_mq7net
#   setsid nohup bash run_ev_s4.sh > ev_s4_chain.log 2>&1 < /dev/null &
#   (BKS 짝:  bash run_ev_s4.sh prod_bks_2e13.data bks2e13   — 단 in.ev_s4 는 7net 전용이라
#    BKS 는 in.ev_bks 를 쓴다. 아래 BKS 절 참조.)
set -e
cd "$(dirname "$0")"
ulimit -s 262144
export OMP_NUM_THREADS=6 MKL_NUM_THREADS=6

exec 9>/tmp/.s4_ev_scan.lock
flock -n 9 || { echo "이미 실행 중이다. 중복 실행 차단."; exit 1; }

mkdir -p logs ev

DFILE=${1:-prod_7net_mq.data}
TAG=${2:-7net}
HALFWIDTH=${3:-0.06}        # V0 기준 반폭 (부피비). 기존 스캔과 같은 자릿수.
NMAIN=${4:-7}               # 2단계 점 개수 (홀수여야 V0 자신이 격자에 들어간다)

runpt() {   # $1 = f (부피비, V0 기준 아님 — V_ref = prod 구조의 부피)
  local f=$1 phase=$2
  local s; s=$(python3 -c "print(f'{$f**(1/3):.8f}')")
  local lg="logs/ev_s4_${TAG}_${phase}_f${f}.log"
  # ★ 진행 메시지는 전부 stderr 로. stdout 은 EVPOINT 한 줄뿐이어야 한다
  #   (호출부가 stdout 을 결과 .txt 로 리다이렉트하므로).
  echo "--- ${TAG} ${phase}  f=${f}  s=${s}" >&2
  lmp_7net -var s "$s" -var dfile "$DFILE" -var tag "$TAG" \
           -in in.ev_s4 -log "$lg" 2>&1 | tail -2 >&2
  grep "^EVPOINT" "$lg" | awk '{$1="";print}'
}

# ================== 1단계: P = 0 괄호치기 ==================
# f = 1.00 (=현재 rho 2.20), 1.03, 1.06 세 점. P300 이 양수(팽창 경향)이므로
# 평형은 f > 1 쪽에 있다. 압축 방향은 이미 P > 0 임이 자명해 점을 아낀다.
PILOT="ev/ev_s4_${TAG}_pilot.txt"
echo "# scale volume(A^3) density(g/cc) PE(eV) epa(eV) press(bar) maxf(eV/A)" > "$PILOT"
echo "=========== STAGE 1: pilot (P=0 bracketing) ==========="
for f in 1.00 1.03 1.06; do runpt "$f" pilot >> "$PILOT"; done
cat "$PILOT"

# ================== V0 결정 + 대칭 격자 생성 ==================
read -r F0 RHO0 KLOC < <(python3 - "$PILOT" <<'PY'
import sys, numpy as np
d = np.atleast_2d(np.loadtxt(sys.argv[1]))
V, rho, P = d[:, 1], d[:, 2], d[:, 5] / 1e4        # GPa
Vref = V[0]                                        # 첫 점(f=1.00)의 부피 = 기준
f = V / Vref
# P(f) 를 2차로 피팅해 P=0 근을 찾는다. 선형 외삽은 K'<0 곡률을 무시해 치우친다.
c = np.polyfit(f, P, 2)
roots = [r.real for r in np.roots(c) if abs(r.imag) < 1e-9 and 0.8 < r.real < 1.4]
f0 = min(roots, key=lambda r: abs(r - 1.0)) if roots else float(np.interp(0, P[::-1], f[::-1]))
dPdf = np.polyval(np.polyder(c), f0)               # 국소 K = -V dP/dV = -f dP/df
print(f"{f0:.5f} {rho[0]/f0:.4f} {-f0*dPdf:.2f}")
PY
)
echo ""
echo "=========== V0 실측: f0 = ${F0}   rho0 = ${RHO0} g/cc   국소 K = ${KLOC} GPa ==========="
echo "    (기존 7net 값 = BKS 위상 위: rho0 2.2185.  차이가 밀도에서의 위상 형성 효과)"

GRID=$(python3 -c "
f0=$F0; hw=$HALFWIDTH; n=$NMAIN
import numpy as np
print(' '.join(f'{f0*x:.4f}' for x in np.linspace(1-hw,1+hw,n)))")
echo "=========== STAGE 2: V0 대칭 격자 (${NMAIN}점, V/V0 = $(python3 -c "print(f'{1-$HALFWIDTH:.2f}')")~$(python3 -c "print(f'{1+$HALFWIDTH:.2f}')")) ==========="
echo "  f = $GRID"
echo ""

OUT="ev/ev_s4_${TAG}_scan.txt"
{ echo "# S4 self-quenched topology E-V scan: ${DFILE}"
  echo "# stage-1 pilot -> f0 = ${F0}, rho0 = ${RHO0} g/cc, local K = ${KLOC} GPa"
  echo "# stage-2 grid symmetric about V0: V/V0 = $(python3 -c "print(f'{1-$HALFWIDTH:.2f}')")~$(python3 -c "print(f'{1+$HALFWIDTH:.2f}')"), n=${NMAIN}"
  echo "# scale volume(A^3) density(g/cc) PE(eV) epa(eV) press(bar) maxf(eV/A)"
} > "$OUT"
for f in $GRID; do runpt "$f" main >> "$OUT"; done

echo ""
echo "================= $OUT ================="
cat "$OUT"
echo ""
echo "다음: BM3 피팅 (fig_density.py 계열, scipy 필요 -> mlip 환경에서)."
echo "     기존 7net 값(BKS 위상): rho0 2.2185, K0 43.23 GPa, K0' -2.02  <- 이것과 뺄셈하면 위상 형성 효과."
