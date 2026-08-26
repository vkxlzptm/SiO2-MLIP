#!/usr/bin/env python
"""Fig. S(q) — 중성자 구조인자. 우리 두 포텐셜 vs 중성자 회절 실험.

★ 이 그림이 말하는 것 — 위치와 진폭이 서로 다른 얘기를 한다
  FSDP(first sharp diffraction peak)는 유리 **중거리 질서**의 표준 지표다.
  · **위치**는 중거리 주기성(2π/q)이 결정 → 망의 위상이 지배.
    BKS 1.593 / 7net 1.590 로 **오차 안에서 같고**, 둘 다 실험(1.492)보다 6.7 % 높다.
    → 7net 이 위상을 못 바꿨다는 것이 ring 통계에 이어 **산란 지표에서도 확인**된다.
    우리 망의 중거리 특성 길이가 실물보다 6 % 짧다.
  · **진폭**은 그 주기성이 얼마나 뚜렷한가 → 국소 구조도 기여.
    BKS 1.462 → 7net 1.360 으로 **실험(1.357)과 사실상 일치**한다.
    Si-O-Si 각 분포가 넓어진 것(σ 12.2 → 13.7)과 방향이 맞는다.
  → **국소는 고치고 위상은 못 고친다**를 한 그림으로 보여준다.

★ FSDP 를 어떻게 재나 — **최댓값을 쓰면 안 된다.**
  잡음 있는 곡선의 최댓값은 **항상 위로 편향**된다(스파이크를 집는다).
  실제로 껍질 폭 0.05 → 0.10 으로 바꾸자 BKS 진폭이 1.58 → 1.43 으로 떨어졌다.
  진짜 값이 변한 게 아니라 잡음이 줄어 편향이 줄어든 것이다.
  → **가우시안 + 선형 배경**을 FSDP 구간에 피팅해 꼭짓점을 얻는다. 편향이 없고
    피팅 공분산에서 불확도도 같이 나온다 (실험 ±0.006, 우리 ±0.015).

  ※ 스플라인으로 하면 안 되나? 종류에 따라 답이 갈린다 (직접 확인):
      보간 스플라인(s=0)  exp 1.510 / BKS 1.606 / 7net 1.616  ← 잡음을 그대로 따라가 편향 잔존
      평활 s=0.3Nσ²      1.501 / 1.617 / 1.620
      평활 s=1.0Nσ²      1.493 / 1.589 / 1.588   ← **가우시안과 일치**
      평활 s=3.0Nσ²      1.502 / 1.607 / 1.609
      가우시안 피팅       1.492 / 1.593 / 1.590
    평활도 s 를 고를 원칙이 없어 0.03(가우시안 불확도의 2배)이나 흔들린다.
    다만 s 를 통계적으로 정당한 값(잔차제곱합 ≈ Nσ²)으로 잡으면 가우시안과 수렴한다
    → 서로 독립인 두 방법이 만나므로 가우시안 결과를 믿을 근거가 된다.
    어느 방법이든 우리 1.59~1.62 / 실험 1.49~1.51 이라 **+6 % 결론은 불변**이다.

★ 왜 sq_direct(절단 없음) 를 쓰나
  g(r)→FT 경로(`sq_analyze.py`)는 박스가 30.4 Å 이라 r 을 15 Å 에서 자르고 Lorch 창을
  곱해야 해서 **피크를 뭉갠다**. 실험 곡선엔 그 처리가 없으니 겹치면 불공정하다.
  두 경로의 FSDP 위치는 0.3 % 안에서 일치했다 → 창은 폭·높이만 건드린다는 확인.

⚠ 한계
  · q 는 원리적으로 2π/L = 0.207 Å⁻¹ 간격으로만 존재한다. 껍질 폭 0.10 은 그 절반이라
    이미 충분히 조밀하다. **더 좁히면 껍질당 표본이 줄어 잡음만 커진다.**
  · 음영 = 껍질 안 q 벡터들의 표준오차. **불확도의 하한**이다 —
    3 ps 안의 31 프레임은 서로 독립이 아니어서 실제 불확도는 이보다 크다.
  · 실험 곡선은 논문 그림 digitize. 고k(>14) 평균 0.985 → 계통오차 약 1.5 %.
    실험 곡선 자체가 원 측정치(오차막대 붙은 점)의 **스플라인 피팅**이라 매끈한 것이지,
    날 데이터가 우리보다 깨끗한 게 아니다.
"""
from pathlib import Path

import numpy as np
from scipy.optimize import curve_fit
from scipy.interpolate import PchipInterpolator
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator

ROOT = Path(__file__).resolve().parents[2]
FIG = ROOT / "04_analysis/fig"; FIG.mkdir(exist_ok=True)

QMAX_PLOT = 12.0        # sq_direct.py 의 qmax 와 맞출 것 (그 이상은 데이터가 없다)

plt.rcParams.update({
    "font.size": 10, "axes.labelsize": 11, "xtick.labelsize": 10, "ytick.labelsize": 10,
    "legend.fontsize": 9, "xtick.direction": "in", "ytick.direction": "in",
    "xtick.top": True, "ytick.right": True,
    "xtick.major.size": 5, "ytick.major.size": 5,
    "xtick.minor.size": 2.8, "ytick.minor.size": 2.8,
    "axes.linewidth": 0.9, "lines.linewidth": 1.4,
})

exp = np.loadtxt(ROOT / "04_analysis/dat/zeidler_sq_ambient.dat")
bks = np.loadtxt(ROOT / "02_run/s0_requench/bks220_sqd.dat")
net = np.loadtxt(ROOT / "02_run/s3_md/7net220_sqd.dat")


FIT_LO, FIT_HI = 1.05, 2.15


def gmodel(x, A, q0, w, c0, c1):
    return A * np.exp(-0.5 * ((x - q0) / w)**2) + c0 + c1 * (x - 1.6)


def peak(q, s, lo=FIT_LO, hi=FIT_HI):
    """가우시안 + 선형 배경 피팅으로 FSDP 위치·높이. 최댓값은 위로 편향돼 못 쓴다.

    반환: (q0, sigma_q0, S(q0), 피팅 파라미터, 잔차 RMS)
    잔차 RMS 는 SEM 과 비교해 **밴드가 정직한 크기인지** 확인하는 데 쓴다
    (실측: 잔차 0.041 vs SEM 0.035 → 20 % 안에서 일치, 밴드가 실제 요동을 대표한다).
    """
    m = (q > lo) & (q < hi) & np.isfinite(s)
    qq, ss = q[m], s[m]
    p0 = [ss.max() - ss.min(), qq[np.argmax(ss)], 0.25, ss.min(), 0.0]
    p, cov = curve_fit(gmodel, qq, ss, p0=p0, maxfev=200000)
    res = float(np.sqrt(((ss - gmodel(qq, *p))**2).mean()))
    return p[1], float(np.sqrt(np.diag(cov))[1]), float(gmodel(p[1], *p)), p, res


def bandlimit(q, s, qout=None, rmax=15.2, rlim=60.0, nr=6000):
    """S(q) 잡음 제거 — **박스 크기가 정하는 물리적 대역 제한**. 조정 파라미터가 없다.

    원리
        박스가 L=30.4 Å 이라 minimum image 로 **r > L/2 = 15.2 Å 의 상관은 원리적으로
        모른다**. 그런데 S(q)→h(r) 변환은 잡음을 전 r 에 퍼뜨리므로 그 너머에도 값이 생긴다.
        거기 있는 건 정의상 신호가 아니다. 잘라내고 되돌리면 **잡음만 빠진다.**
            h(r) = 1/(2π²ρr) ∫ q[S−1] sin(qr) dq  →  h(r>L/2)=0  →  S−1 = 4πρ/q ∫ r h sin(qr) dr
        (ρ 는 정변환·역변환에서 정확히 상쇄된다. 넣을 필요가 없다.)

    검증 — 네 가지를 모두 통과했다
      1. 잡음 1.7~1.8 배 감소 (2차차분 RMS: BKS 0.099→0.057, 7net 0.096→0.053)
      2. FSDP 불변: q 1.593→1.590, S 1.462→1.457 (**인용 불확도 ±0.014 안**)
         피팅 불확도는 오히려 ±0.014 → ±0.005 로 개선
      3. 필터 곡선이 원본 ±2 SEM 안에 98~99 % 들어온다 → 통계 요동 범위를 안 벗어난다
      4. ★ **실험 곡선에 같은 필터를 걸면 아무 일도 안 일어난다**
         (q 1.494→1.494, S 1.348→1.348, 거칠기 0.0407→0.0404).
         이미 매끈한 실데이터를 안 건드린다는 것이 이 필터의 결정적 알리바이다.

    rmax 는 조정 대상이 아니다 — 14~20 Å 전 구간에서 q 1.587~1.591, S 1.455~1.461 로 불변.

    ※ 시도했다 버린 것들
      · r<1.5 Å 에서 g=0 (원자 겹침 불가) 제약 추가: 잡음은 **하나도** 더 안 줄면서
        (거칠기 0.057 그대로) 진폭만 rmin 1.3→1.6 에서 1.53→1.19 로 흔들린다. 폐기.
      · r 창 없이 순수 왕복: **발산한다** (rlim 45→800 에서 RMS 0.03→7.8).
        잘린 q 데이터의 h(r) 은 리플이 안 죽어서, r 창은 선택이 아니라 성립 조건이다.
      · restricted cubic spline 회귀: 매듭 50~80 개면 이 필터와 같은 답을 준다
        (q 1.587~1.600, S 1.460~1.468) → **독립적인 두 방법의 일치**라 신뢰 근거가 된다.
        다만 매듭 30 개(간격 0.41 = 하필 박스가 정하는 한계값)면 S=1.25 로 14 % 뭉개지는데
        **방법 안에 그게 틀렸다는 신호가 없다.** 답을 이미 알아야 매듭을 고를 수 있다.
        rmax 는 박스가 정해주므로 이쪽을 쓴다.

    ★ qout 을 주면 **임의의 촘촘한 격자에서 평가**한다. 이게 중요하다 —
      대역제한 결과는 이산점이 아니라 **연속함수**다. 그래서 그림을 그릴 때 보간이
      아예 필요 없다. PCHIP 로 이으면 단조성 보존 때문에 데이터 점을 못 넘어서
      0.1 격자 사이에 떨어진 피크 꼭짓점이 눌린다 (7net 진폭 1.36 → 1.33).
      그래서 (a) 와 (b) 의 피크 높이가 어긋나 보였다. 직접 평가하면 그 문제가 없다.
    """
    r = np.linspace(1e-6, rlim, nr)
    dr = r[1] - r[0]
    h = (np.sin(np.outer(r, q)) @ (q * (s - 1.0) * np.gradient(q))) / r
    h[r > rmax] = 0.0
    qo = q if qout is None else qout
    return 1.0 + 2.0 / np.pi / qo * (np.sin(np.outer(qo, r)) @ (r * h * dr))


# 저q 표시 하한 = **실험 데이터가 시작하는 q** (0.8 Å⁻¹). 비교 대상이 없는 구간은 안 그린다.
#   마침 우리 쪽 통계 한계와도 맞는다. 박스가 30.4 Å 이라 최소 q = 2π/L = 0.207 인데
#   q<0.5 껍질에는 q벡터가 1·8·5·26·19 개뿐이다 (q=0.8 에서 59 개, FSDP 구간은 175~393 개).
#   그 구간의 널뛰기는 물리가 아니라 **표본 부족**이다. S(q→0) = ρk_BT·κ_T ≈ 0.09 로
#   수렴하는 모습을 보려면 박스를 훨씬 키워야 한다.
QMIN_PLOT = float(exp[:, 0].min())


SET = [("Neutron diff. (exp.)", "k", exp[:, 0], exp[:, 1], None, 1.9, None),
       ("BKS", "tab:blue", bks[:, 0], bks[:, 1], bks[:, 2], 1.3, bks[:, 3]),
       ("7net-Nano-4.5", "tab:red", net[:, 0], net[:, 1], net[:, 2], 1.3, net[:, 3])]
pk = {lab: peak(q, s) for lab, _, q, s, *_ in SET}
qe = pk[SET[0][0]][0]
QFIT = np.linspace(FIT_LO, FIT_HI, 400)

fig, ax = plt.subplots(1, 2, figsize=(7.0, 2.9),
                       gridspec_kw={"width_ratios": [2.1, 1]})
a, b = ax


def draw(axis, mode="raw"):
    """mode="raw"  : **대역 제한한** 곡선 + SEM 밴드  (패널 a)
       mode="fit"  : 데이터는 점, **FSDP 를 실제로 뽑은 가우시안 피팅**이 굵은 곡선 (패널 b)

    ★ (a) 의 곡선은 bandlimit() 을 통과한 값이다 — 근거는 그 함수 docstring 에.
      평활 스플라인·Savitzky-Golay 는 **쓰면 안 된다.** 곡률에 벌점을 매기는데 진짜
      뾰족한 피크도 곡률이 커서 같이 깎인다 (평활 스플라인 s=2N 에서 진폭 −14 %,
      SG 창 9 에서 −6 %). 둘 다 평활도를 고를 물리적 근거가 없다.
      bandlimit 은 다르다 — **잘라내는 기준을 박스 크기가 정해주고**, 실험 곡선에
      걸어도 아무 일이 안 일어난다는 알리바이가 있다.

    ※ (b) 는 필터를 안 건다. 보고 숫자는 가우시안 피팅에서 나오고 그건 이미 잡음에
      면역이므로, 날 데이터 점을 그대로 보여주는 편이 정직하다.
      (필터를 걸어도 q 1.593→1.590, S 1.462→1.457 로 인용 불확도 안에서 안 움직인다.)
    """
    for lab, c, q, s, e, lw, nq in SET:
        z = 4 if c == "k" else 3
        if mode == "raw" and e is not None:
            # ★ 대역제한 필터를 **촘촘한 격자에서 직접 평가**한다 — 보간이 아예 없다.
            #   PCHIP 는 단조성 보존이라 데이터 점을 못 넘어서, 꼭짓점이 0.1 격자 사이에
            #   떨어지면 봉우리를 누른다 (7net 1.36 → 1.33). (a)·(b) 높이가 어긋난 원인이었다.
            #   실험이 없는 저q 는 **표시만** 자른다. 변환 입력에선 빼지 않는다 —
            #   푸리에 변환은 전 q 정보를 쓰기 때문이다.
            m = q >= QMIN_PLOT
            qf = np.linspace(q[m][0], q[m][-1], 1500)
            sf = bandlimit(q, s, qf)
            se = PchipInterpolator(q[m], e[m])(qf)   # 밴드 폭은 그대로 — 불확도는 안 줄인다
            axis.fill_between(qf, sf - se, sf + se, color=c, alpha=0.2, lw=0, zorder=z - 1)
            axis.plot(qf, sf, "-", c=c, lw=lw, label=lab, zorder=z)
            continue
        if e is not None:
            ok = np.isfinite(e) & np.isfinite(s)
            qf = np.linspace(q[ok][0], q[ok][-1], 1200)
            lo = PchipInterpolator(q[ok], (s - e)[ok])(qf)
            hi = PchipInterpolator(q[ok], (s + e)[ok])(qf)
            axis.fill_between(qf, lo, hi, color=c, alpha=0.2, lw=0, zorder=z - 1)
        if mode == "raw" or c == "k":
            # 여기 오는 건 실험 곡선뿐 (이미 매끈하고 SEM 이 없다)
            axis.plot(q, s, "-", c=c, lw=lw, label=lab, zorder=z)
        else:
            m = (q > FIT_LO - 0.15) & (q < FIT_HI + 0.15)
            # 데이터 점: 테두리 없이 면색만 (곡선과 같은 색) — 피팅 곡선을 덜 가린다
            axis.plot(q[m], s[m], "o", ms=3.6, mfc=c, mec="none",
                      alpha=0.95, zorder=z)
            axis.plot(QFIT, gmodel(QFIT, *pk[lab][3]), "-", c=c, lw=1.9, zorder=z + 1)


# ---------- (a) 전 구간 ----------
draw(a, "raw")
a.axhline(1, ls=":", lw=0.8, c="0.6", zorder=1)
a.set_xlim(QMIN_PLOT - 0.6, QMAX_PLOT); a.set_ylim(0.0, 2)
a.set_xlabel(r"$q$ ($\rm\AA^{-1}$)"); a.set_ylabel(r"$S_{\rm N}(q)$")
a.legend(loc="upper right", framealpha=0.92, fontsize=8.5,
         handlelength=1.4, borderpad=0.4, labelspacing=0.35)
a.text(0.025, 0.955, "(a)", transform=a.transAxes, fontsize=11.5, fontweight="bold", ha='left', va='top')
# FSDP 를 화살표로 지시
a.annotate("FSDP", xy=(qe+0.1, 1.44), xytext=(qe+0.6, 1.7),
           fontsize=9, ha="center", va="bottom", color="0.15",
           arrowprops=dict(arrowstyle="->", lw=1.1, color="0.15"))
# exp 출처를 표기 .
a.text(1-0.02, 0.045,"exp.: Zeidler $et\\ al.$, PRL 113, 135501 (2014)", transform=a.transAxes, fontsize=8.5, ha='right', va='bottom')

# ---------- (b) FSDP 확대 ----------
draw(b, "fit")
for lab, c, *_ in SET:
    qp, _, sp = pk[lab][:3]
    b.plot([qp], [sp], "o", ms=7, mfc=c, mec="w", mew=1.5, zorder=6)
    b.axvline(qp, ls=":", lw=1.0, c=c, alpha=0.85, zorder=1)
b.set_xlim(1.05, 2.15); b.set_ylim(0.80, 2.0)
b.set_xlabel(r"$q$ ($\rm\AA^{-1}$)")
b.set_title("FSDP", fontsize=10)
b.text(0.955, 0.955, "(b)", transform=b.transAxes, fontsize=11.5,
       fontweight="bold", ha="right", va="top")

b.text(0.07, 0.955, r"$q_{\rm FSDP}$ ($\rm\AA^{-1}$)", transform=b.transAxes,
       fontsize=7.5, ha="left", va="top", color="0.15")
for j, (nm, c, lab) in enumerate([("exp.", "k", SET[0][0]),
                                  ("BKS", "tab:blue", "BKS"),
                                  ("7net-Nano-4.5", "tab:red", "7net-Nano-4.5")]):
    qp = pk[lab][0]
    # % 는 붙여 쓴다. SI/ISO 31-0 은 띄우라고 하지만 PRL·PRB 등 대부분의 저널 관행은 붙임.
    txt = f"{nm}: {qp:.2f}" + ("" if j == 0 else f" ({100*(qp/qe-1):+.0f}%)")
    b.text(0.05, 0.955 - 0.082 * (j + 1), txt, transform=b.transAxes,
           fontsize=7.5, ha="left", va="top", color=c,
           fontweight="bold" if j else "normal", zorder=8,
           # 세로 점선이 글자를 가로질러 읽기 나쁘다 → 흰 배경을 깔되 테두리는 없앤다
           bbox=dict(fc="w", ec="none", alpha=0.8, pad=1.2))

for a_ in ax:
    a_.xaxis.set_minor_locator(AutoMinorLocator(2))
    a_.yaxis.set_minor_locator(AutoMinorLocator(2))

#fig.suptitle("Neutron structure factor of a-SiO$_2$ at 300 K  "
#             '\n'"(exp.: Zeidler $et\\ al.$, PRL 113, 135501 (2014))",
#             fontsize=10, y=0.995, x=0.5)
fig.suptitle("Neutron structure factor of a-SiO$_2$ at 300 K", 
             fontsize=11, y=0.995, x=0.5)
fig.tight_layout(rect=[0, 0, 1, 1.10])
fig.savefig(FIG / "fig_sq.png", dpi=300)
print(f"-> {FIG}/fig_sq.png\n")

print(f"{'':28s}{'q_FSDP':>9s}{'±':>7s}{'vs exp':>9s}{'S_peak':>9s}{'vs exp':>9s}")
se = pk[SET[0][0]][2]
for lab, _, q, s, e, *_ in SET:
    q0, e0, s0, _, res = pk[lab]
    sem = np.nanmedian(e) if e is not None else np.nan
    extra = f"   잔차 {res:.4f} vs SEM {sem:.4f}" if e is not None else f"   잔차 {res:.4f}"
    print(f"{lab:28s}{q0:9.3f}{e0:7.3f}{100*(q0/qe-1):+8.1f}%{s0:9.3f}{100*(s0/se-1):+8.1f}%{extra}")
