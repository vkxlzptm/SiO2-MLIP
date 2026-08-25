#!/bin/bash
# S4-EV — **특정 점만** eval cap 을 올려 재실행한다 (전체 체인 재실행 금지용).
#
# ─ 왜 필요한가 (2026-08-25, 2차 진단) ────────────────────────────────────────
#  400-cap 으로 완주한 7net 자기망 스캔에서 main 격자 7점 중 2점이 아직
#  "max force evaluations" 로 잘려 있다:
#     f = 0.9577   최종 전역 힘 2-norm 0.0957 eV/A   <- 잡음 바닥의 3~5 배. 진짜 덜 풀림.
#     f = 0.9781   최종 전역 힘 2-norm 0.0202 eV/A   <- 이미 바닥. cap 에만 걸렸다.
#  규칙(feedback memory): "max force evaluations 면 그 점은 못 쓴다". 그래서 다시 돌린다.
#
# ─ "수렴"의 판정선이 ftol 이 아닌 이유 (중요) ────────────────────────────────
#  같은 실행에서 정상 종료("linesearch alpha is zero")한 9 점의 최종 2-norm 이
#  0.016 ~ 0.035 eV/A 였다. ftol = 1.0e-3 보다 20~35 배 크다.
#  즉 **CG 가 ftol 을 만족해서 멈춘 적은 한 번도 없다** — 항상 수치 잡음 바닥에
#  닿아 라인서치가 죽으면서 멈췄다. 2160 원자 MLIP 힘의 바닥이 거기다.
#  -> 판정선은 (a) 종료 사유 = linesearch alpha is zero
#              (b) 최종 2-norm 이 0.02~0.035 대역 안
#     둘 다다. cap 상향은 (a) 를 확보하려는 것이지 ftol 을 맞추려는 게 아니다.
#     ftol 을 잡음 바닥 위로 완화하지는 않는다 — 점마다 다른 깊이에서 멈추면
#     P(V) 곡률이 다시 계통적으로 휜다(분석 12 와 같은 실패 모드).
#
# ─ 사용법 ────────────────────────────────────────────────────────────────────
#   bash rerun_ev_points.sh <TAG> <phase> <cap> <f1> [f2 ...]
#
#   예) 7net 자기망 미수렴 2점을 cap 1200 으로:
#       bash rerun_ev_points.sh 7net main 1200 0.9577 0.9781
#
#   읽는 구조는 relaxed_<TAG>.data — run_ev_s4.sh 의 Stage-0 산물이다.
#   (원래 스캔과 **같은 출발 구조**여야 같은 자로 비교된다. prod_*.data 를 직접
#    읽으면 안 된다 — 그게 분석 12 의 원인이었다.)
#
# ─ 산출 ──────────────────────────────────────────────────────────────────────
#   logs/ev_s4_<TAG>_<phase>_f<f>.log        덮어씀 (직전 판은 .prev 로 밀어둔다)
#   ev/ev_s4_<TAG>_scan.txt                  해당 줄만 제자리 교체
#   ev/ev_s4_<TAG>_scan.txt.bak_<타임스탬프> 교체 전 원본 (인용 중인 수치를
#                                            말없이 바꾸지 않기 위한 관례)
set -e
cd "$(dirname "$0")"
ulimit -s 262144
export OMP_NUM_THREADS=6 MKL_NUM_THREADS=6

TAG=${1:?TAG 를 달라 (예: 7net)}
PHASE=${2:?phase 를 달라 (main | pilot)}
CAP=${3:?eval cap 을 달라 (예: 1200)}
shift 3
[ $# -ge 1 ] || { echo "재실행할 f 값을 최소 하나 달라"; exit 1; }

exec 9>"/tmp/.s4_ev_rerun_${TAG}.lock"
flock -n 9 || { echo "TAG=${TAG} 재실행이 이미 돌고 있다. 중복 차단."; exit 1; }

RELAXED="relaxed_${TAG}.data"
[ -f "$RELAXED" ] || { echo "!! ${RELAXED} 가 없다. run_ev_s4.sh 의 Stage-0 를 먼저 돌려라."; exit 1; }

if [ "$PHASE" = "pilot" ]; then
  SCAN="ev/ev_s4_${TAG}_pilot.txt"
else
  SCAN="ev/ev_s4_${TAG}_scan.txt"
fi
[ -f "$SCAN" ] || { echo "!! ${SCAN} 이 없다."; exit 1; }

STAMP=$(date +%Y%m%d_%H%M%S)
cp "$SCAN" "${SCAN}.bak_${STAMP}"
echo "원본 백업: ${SCAN}.bak_${STAMP}"
echo ""

for f in "$@"; do
  s=$(python3 -c "print(f'{$f**(1/3):.8f}')")
  lg="logs/ev_s4_${TAG}_${PHASE}_f${f}.log"
  [ -f "$lg" ] && mv "$lg" "${lg}.prev"

  echo "=== ${TAG} ${PHASE}  f=${f}  s=${s}  cap=${CAP} ==="
  lmp_7net -var s "$s" -var dfile "$RELAXED" -var tag "$TAG" -var cap "$CAP" \
           -in in.ev_s4 -log "$lg" 2>&1 | tail -2

  crit=$(grep -o "Stopping criterion = .*" "$lg" | sed 's/Stopping criterion = //')
  norm=$(grep -o "Force two-norm initial, final = .*" "$lg" | head -1 | awk '{print $NF}')
  echo "  종료 사유 : ${crit}"
  echo "  최종 2-norm: ${norm}   (잡음 바닥 대역 0.02~0.035)"

  if [ "$crit" != "linesearch alpha is zero" ]; then
    echo "  !! 아직 cap 에 걸린다. cap 을 더 올려서 다시 돌려라. scan.txt 는 건드리지 않는다."
    continue
  fi

  newline=$(grep "^EVPOINT" "$lg" | awk '{$1="";print}')
  [ -n "$newline" ] || { echo "  !! EVPOINT 를 못 찾았다. scan.txt 유지."; continue; }

  # scan.txt 의 첫 컬럼(scale)이 s 와 같은 줄을 새 결과로 교체
  python3 - "$SCAN" "$s" "$newline" <<'PY'
import sys
path, s, newline = sys.argv[1], sys.argv[2], sys.argv[3]
lines = open(path).read().splitlines()
hit = 0
for i, ln in enumerate(lines):
    c = ln.split()
    if not c or ln.lstrip().startswith("#"):
        continue
    if c[0] == s:
        lines[i] = newline
        hit += 1
if hit != 1:
    sys.exit(f"  !! scale={s} 인 줄이 {hit} 개다 (1 개여야 한다). 수동 확인이 필요하다.")
open(path, "w").write("\n".join(lines) + "\n")
print(f"  -> {path} 의 scale={s} 줄 교체 완료")
PY
  echo ""
done

echo ""
echo "================= ${SCAN} ================="
cat "$SCAN"
echo ""
echo "=== 이 TAG 전체 점의 종료 사유 재확인 ==="
for lg in logs/ev_s4_${TAG}_pilot_f*.log logs/ev_s4_${TAG}_main_f*.log; do
  [ -f "$lg" ] || continue
  case "$lg" in *.prev) continue;; esac
  crit=$(grep -o "Stopping criterion = .*" "$lg" | sed 's/Stopping criterion = //')
  norm=$(grep -o "Force two-norm initial, final = .*" "$lg" | head -1 | awk '{print $NF}')
  printf "%-45s %-25s %s\n" "$(basename "$lg")" "$crit" "$norm"
done
echo ""
echo "다음: 전 점이 'linesearch alpha is zero' 인지 확인 후 ev_s4_summary.py / bm3.py 재피팅."
