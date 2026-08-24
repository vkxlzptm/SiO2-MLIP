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
# pilot 점 목록. 기본은 S4 자체 형성 망(f0 ~ 1.019)에 맞춰져 있다.
# **다른 구조를 돌릴 때는 반드시 다시 잡아라** — pilot 이 P=0 을 괄호치지 못하면
# 격자를 만들지 않고 멈춘다(외삽 방지). 예:
#   BKS 가 만든 망을 7net 으로 읽으면 f0 ~ 0.99 이므로
#   PILOT_FS="0.96 0.98 1.00 1.02" bash run_ev_s4.sh prod_bks_2e13.data bksnet2e13
PILOT_FS="${PILOT_FS:-0.98 1.00 1.02 1.04}"
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
# f = 0.98 / 1.00 / 1.02 / 1.04 (rho 2.245 ~ 2.115). 점 하나(5분) 더 써서
# **평형점을 양쪽에서 괄호친다** — 한쪽에만 점을 찍으면 2차 피팅이 외삽이 되고,
# 그 위에 2단계 격자 7점(35분)을 세우므로 빗나가면 손실이 훨씬 크다.
#
# 예상 위치 (2026-08-24 실측 보정):
#   S4 7net 망의 P(300 K) = +8,000 bar. 여기서 열압력을 빼야 0 K virial 이 된다.
#   기존 7net 구조(s3_md/nvt_7net220.log)에서 같은 포텐셜·같은 밀도로 실측한 열압력은
#     300 K NVT -2,950 bar  vs  같은 구조 0 K virial -3,654 bar  ->  +704 bar
#     (운동항 N kB T/V = +2,740, 열 virial -2,036 의 합)
#   -> S4 망의 0 K P ~ +7,300 bar = +0.73 GPa,  K ~ 43 GPa 이므로
#      dV/V ~ 0.017  ->  f0 ~ 1.017,  rho0 ~ 2.163 g/cc.
#   4점 구간(0.98~1.04)이 이를 넉넉히 포함한다.
PILOT="ev/ev_s4_${TAG}_pilot.txt"
echo "# scale volume(A^3) density(g/cc) PE(eV) epa(eV) press(bar) maxf(eV/A)" > "$PILOT"
echo "=========== STAGE 1: pilot (P=0 bracketing) ==========="
for f in $PILOT_FS; do runpt "$f" pilot >> "$PILOT"; done
cat "$PILOT"

# ================== V0 결정 + 대칭 격자 생성 ==================
F_FIRST=$(echo $PILOT_FS | awk '{print $1}')
read -r F0 RHO0 KLOC < <(python3 - "$PILOT" "$F_FIRST" <<'PY'
# ★ numpy 를 쓰지 않는다. dhl-desktop 에서 이 스크립트는 conda 를 활성화하지 않고
#   돌 수 있고(LAMMPS 바이너리만 있으면 된다), 그때 plain python3 에 numpy 가
#   없으면 set -e 가 여기서 죽는다 — pilot 4점(20분)을 버리고 나서.
#   2차 최소제곱은 3x3 정규방정식이라 표준 라이브러리로 충분하다.
import sys
V, rho, P = [], [], []
for line in open(sys.argv[1]):
    if line.lstrip().startswith("#"):
        continue
    c = line.split()
    if len(c) < 6:
        continue
    V.append(float(c[1])); rho.append(float(c[2])); P.append(float(c[5]) / 1e4)  # GPa
if len(V) < 3:
    sys.exit("pilot 점이 3개 미만이다 — LAMMPS 실행 실패를 의심하라")
Vref = V[0] / float(sys.argv[2])   # 첫 pilot 점의 f 로 기준 부피를 되돌린다
f = [v / Vref for v in V]

# P(f) = a f^2 + b f + c  최소제곱 (정규방정식 + Cramer)
S = lambda k: sum(x**k for x in f)
T = lambda k: sum(x**k * y for x, y in zip(f, P))
A = [[S(4), S(3), S(2)], [S(3), S(2), S(1)], [S(2), S(1), float(len(f))]]
rhs = [T(2), T(1), T(0)]
def det3(m):
    return (m[0][0]*(m[1][1]*m[2][2]-m[1][2]*m[2][1])
          - m[0][1]*(m[1][0]*m[2][2]-m[1][2]*m[2][0])
          + m[0][2]*(m[1][0]*m[2][1]-m[1][1]*m[2][0]))
D = det3(A)
sol = []
for j in range(3):
    M = [row[:] for row in A]
    for i in range(3):
        M[i][j] = rhs[i]
    sol.append(det3(M) / D)
a, b, cc = sol

# P = 0 의 근. 실근이 없거나 구간 밖이면 선형 보간으로 후퇴.
f0 = None
disc = b*b - 4*a*cc
if abs(a) > 1e-12 and disc >= 0:
    cand = [(-b + disc**0.5) / (2*a), (-b - disc**0.5) / (2*a)]
    cand = [r for r in cand if min(f) - 0.03 <= r <= max(f) + 0.03]
    if cand:
        f0 = min(cand, key=lambda r: abs(r - 1.0))
if f0 is None:
    for i in range(len(f) - 1):
        if P[i] * P[i+1] <= 0:
            f0 = f[i] + (f[i+1] - f[i]) * P[i] / (P[i] - P[i+1])
            break
if f0 is None:
    sys.stderr.write(
        "!! P=0 이 pilot 구간 안에 없다. P = " + ", ".join(f"{x:+.2f}" for x in P) +
        " GPa (f = " + ", ".join(f"{x:.3f}" for x in f) + ")\n"
        "   구간을 옮겨 pilot 을 다시 돌려라. 2단계 격자를 외삽 위에 세우면 안 된다.\n")
    sys.exit(1)

dPdf = 2*a*f0 + b
rho0 = rho[0] * f[0] / f0          # rho * f 는 상수 (= rho_ref)
print(f"{f0:.5f} {rho0:.4f} {-f0*dPdf:.2f}")
PY
)
echo ""
echo "=========== V0 실측: f0 = ${F0}   rho0 = ${RHO0} g/cc   국소 K = ${KLOC} GPa ==========="
echo "    (기존 7net 값 = BKS 위상 위: rho0 2.2185.  차이가 밀도에서의 위상 형성 효과)"

# 여기도 numpy 없이 (linspace 는 한 줄이면 된다)
GRID=$(python3 -c "
f0=$F0; hw=$HALFWIDTH; n=$NMAIN
print(' '.join(f'{f0*(1-hw+2*hw*i/(n-1)):.4f}' for i in range(n)))")
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
