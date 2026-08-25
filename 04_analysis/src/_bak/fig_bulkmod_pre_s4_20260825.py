#!/usr/bin/env python
"""Fig. bulk modulus — K(rho) 로 보면 두 포텐셜이 겹친다.

★ 이 그림이 말하는 것
  각자의 평형밀도에서 읽은 K0 만 보면 BKS 34.3 / 7net 43.2 로 8.9 GPa 벌어져
  "BKS 가 훨씬 정확하다"처럼 보인다. 그런데 **같은 밀도에서** K 를 비교하면
  두 곡선이 3 % 이내로 포개진다. 겉보기 차이는 탄성 기술의 우열이 아니라
  **평형밀도가 달라서 곡선 위의 다른 지점을 읽은 것**이다.

  실리카는 이상 압축거동(K0' < 0)이라 **조밀할수록 무르다.** BKS 는 평형밀도를
  6.6 % 높게 잡으므로 자동으로 더 낮은 K0 를 보고하게 된다. 즉 BKS 가 실험 K0 에
  가까운 것은 **밀도 오차와 K 오차가 서로 상쇄된 결과**다 (두 번 틀려서 한 번 맞음).

  그리고 실험 밀도 2.20 에서 보면 **둘 다 +20 % 넘게 딱딱하다.**
  같은 네트워크를 쓰기 때문이다 — ring 분포가 bit-identical 임을 이미 확인했고,
  그 네트워크는 5e12 K/s 로 quench 된 BKS 산물이다.
  → K0 오차의 출처는 포텐셜이 아니라 **구조 생성 프로토콜**이다.

⚠ 출처 구분: 위 해석 중 "BKS 가 오차 상쇄로 K0 를 맞춘다"는 **본 계산의 관찰**이지
  문헌에서 가져온 것이 아니다. 인용할 문헌을 찾으면 그때 바꿀 것.
  K = -V dP/dV 는 BM3 를 virial P(V) 에 피팅한 뒤 해석적으로 미분해 얻는다
  (fig_density.py 와 같은 피팅. 경로 근거는 그쪽 docstring 참조).
"""
from pathlib import Path

import numpy as np
from scipy.optimize import curve_fit
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator
from matplotlib.patches import Rectangle

ROOT = Path(__file__).resolve().parents[2]
FIG = ROOT / "04_analysis/fig"; FIG.mkdir(exist_ok=True)

plt.rcParams.update({
    "font.size": 10, "axes.labelsize": 11, "xtick.labelsize": 10, "ytick.labelsize": 10,
    "legend.fontsize": 9, "legend.handlelength": 1.5,
    "xtick.direction": "in", "ytick.direction": "in",
    "xtick.top": True, "ytick.right": True,
    "xtick.major.size": 5, "ytick.major.size": 5,
    "xtick.minor.size": 2.8, "ytick.minor.size": 2.8,
    "axes.linewidth": 0.9, "lines.linewidth": 1.6,
})

EV2BAR = 1.602176634e6
MASS = 43260.70
rho_of = lambda V: MASS * 1.66053907 / V
V_of = lambda r: MASS * 1.66053907 / r
RHO_EXP, K_EXP = 2.20, 37   # Deschamps 2014 / Yokoyama 2010 (05_doc/SOURCES.md)


def bm3_P(V, V0, K0, Kp):
    x = (V0 / V) ** (1 / 3)
    return 3 * K0 / 2 * (x**7 - x**5) * (1 + 0.75 * (Kp - 4) * (x**2 - 1)) * EV2BAR


def K_of(V, pf, h=1e-3):
    """K = -V dP/dV  (GPa). 중앙차분의 V 가 약분되어 -(dP)/(2h) 가 된다."""
    return -(bm3_P(V * (1 + h), *pf) - bm3_P(V * (1 - h), *pf)) / (2 * h) / 1e4


RUN = ROOT / "02_run/s2_relax"
SET = [("BKS", "tab:blue", RUN / "ev_bks_scan_tail.txt"),
       ("7net-Nano-4.5", "tab:red", RUN / "ev220_scan.txt")]

fit = {}
for lab, col, fn in SET:
    d = np.loadtxt(fn)
    V, P = d[:, 1], d[:, 5]
    pf, _ = curve_fit(bm3_P, V, P, p0=[V[np.argmin(np.abs(P))], 0.04, 4.0], maxfev=400000)
    fit[lab] = dict(col=col, pf=pf, V=V,
                    rho0=rho_of(pf[0]), K0=K_of(pf[0], pf),
                    rlo=rho_of(V.max()), rhi=rho_of(V.min()))

b, s = fit["BKS"], fit["7net-Nano-4.5"]
kb, ks = K_of(V_of(RHO_EXP), b["pf"]), K_of(V_of(RHO_EXP), s["pf"])

fig, ax = plt.subplots(figsize=(5.0, 4.1))

# ---- 세로 기준선 3개: 실험 밀도 + 각 방법의 평형밀도 ----
ax.axvline(RHO_EXP, ls="--", lw=1.2, c="0.35", alpha=0.9, zorder=1)
for v in fit.values():
    ax.axvline(v["rho0"], ls=":", lw=1.1, c=v["col"], alpha=0.85, zorder=1)

# ---- K(rho) 곡선 + 스캔한 부피 위치 ----
#   작은 빈 원 = P(V) 를 실제로 계산한 7개 부피. 큰 채운 원 = 그 방법의 rho0.
#   크기·채움을 다르게 해 역할이 겹치지 않게 한다. (K 자체는 피팅에서 나온 값이므로
#   "측정점"이 아니라 "데이터가 있는 밀도"라는 뜻으로 읽혀야 한다 → 범례에 명시)
for lab, v in fit.items():
    rr = np.linspace(v["rlo"], v["rhi"], 400)
    ax.plot(rr, K_of(V_of(rr), v["pf"]), "-", c=v["col"], zorder=3)
    rd = rho_of(v["V"])
    ax.plot(rd, K_of(V_of(rd), v["pf"]), "o", ms=4.2, mfc="w",
            mec=v["col"], mew=1.1, zorder=4)
for lab, v in fit.items():
    ax.plot(v["rho0"], v["K0"], "o", ms=11, mfc=v["col"], mec="w", mew=1.7, zorder=6)

ax.plot(RHO_EXP, K_EXP, "*", ms=18, mfc="k", mec="w", mew=1.0, zorder=7)

# ---- 세로선 위의 rho0 라벨 (선 색과 맞추고 흰 배경 alpha 0.8) ----
#   BKS 는 평형 마커(34.3)와 범례 상자(y~47) 사이 빈 띠로 올린다. 마커 아래로는
#   회전 라벨 높이(약 6.7 단위)가 안 들어가 마커를 가린다.
for v, yy in ((s, 37.4), (b, 29.9)):
    ax.text(v["rho0"], yy, rf"$\rho_0$ = {v['rho0']:.3f}",
            fontsize=8.5, c=v["col"], ha="center", va="center", rotation=90,
            bbox=dict(fc="white", ec="none", alpha=0.8, pad=1.0), zorder=8)
ax.text(RHO_EXP, 31.0, rf"$\rho_{{\rm exp}}$ = {RHO_EXP:.2f}",
        fontsize=8.5, c="0.25", ha="center", va="center", rotation=90,
        bbox=dict(fc="white", ec="none", alpha=0.8, pad=1.0), zorder=8)

# ---- 두 읽기 방식을 상자에 정리 ----
#   matplotlib 는 한 text 안에서 부분 색을 못 준다. 값마다 색(BKS 파랑 / 7net 빨강)을
#   입히려면 text 를 쪼개야 하므로, 열 위치를 고정한 **표**로 배치한다.
#   덤으로 "43.2 / 34.3" 의 슬래시(나눗셈으로 오독)도 사라진다.
# ---- 실험값과의 간격: rho_exp 에서만 재는 게 정당한 비교다 ----
#   두 곡선이 1.4 GPa 밖에 안 떨어져 있어 화살표를 색깔별로 두 개 그리면 겹쳐서 지저분하다.
#   "실험과의 간격"은 하나의 개념이므로 **검정 화살표 하나**로 그리고 값은 옆에 적는다.
ax.annotate("", xy=(RHO_EXP, K_EXP + 0.7), xytext=(RHO_EXP, (kb + ks) / 2 - 1),
            arrowprops=dict(arrowstyle="<->", lw=1.2, color="0.15"), zorder=7)
ax.text(RHO_EXP - 0.005, (K_EXP + (kb + ks) / 2) / 2 + 0.0,
        "both$\\approx$+20 %\nvs $K_{\\rm exp}$",
        fontsize=8.5, ha="right", va="center", multialignment="right",
        color="0.15", linespacing=1.4,
        bbox=dict(fc="white", ec="none", alpha=0.8, pad=1.5), zorder=8)

BOX = dict(x=0.025, y=0.025, w=0.72, h=0.155)
ax.add_patch(Rectangle((BOX["x"], BOX["y"]), BOX["w"], BOX["h"],
                       transform=ax.transAxes, fc="white", ec="0.75", lw=0.7,
                       alpha=0.95, zorder=9))
FS, CL = 8.5, "0.15"
COL = dict(lab=0.048, red=0.375, blue=0.485, gap=0.525)
for yy, lab, vr, vb, gap in (
        (0.122, r"$K_0$ at own $\rho_0$", s["K0"], b["K0"],
         rf"$\Delta K_0$ = {b['K0']-s['K0']:+.1f} GPa"),
        (0.058, rf"$K$ at $\rho_{{\rm exp}}$ = {RHO_EXP:.2f}", ks, kb,
         rf"$\Delta K$ = {kb-ks:+.1f} GPa")):
    ax.text(COL["lab"], yy, lab, transform=ax.transAxes, fontsize=FS,
            ha="left", va="center", color=CL, zorder=10)
    ax.text(COL["red"], yy, f"{vr:.1f}", transform=ax.transAxes, fontsize=FS,
            ha="right", va="center", color=s["col"], fontweight="bold", zorder=10)
    ax.text(COL["blue"], yy, f"{vb:.1f}", transform=ax.transAxes, fontsize=FS,
            ha="right", va="center", color=b["col"], fontweight="bold", zorder=10)
    ax.text(COL["gap"], yy, gap, transform=ax.transAxes, fontsize=FS,
            ha="left", va="center", color=CL, zorder=10)

ax.set_xlabel(r"$\rho$ (g/cm$^3$)")
ax.set_ylabel(r"$K = -V\,\mathrm{d}P/\mathrm{d}V$  (GPa)")
ax.set_xlim(2.06, 2.46)
# ymin 20: BKS 최우측 스캔점(rho 2.4445, K 22.4)까지 보이게. ymax 55: rho0 라벨 자리만 확보.
ax.set_ylim(21, 50)
ax.xaxis.set_minor_locator(AutoMinorLocator(2))
ax.yaxis.set_minor_locator(AutoMinorLocator(2))

# 범례 핸들은 직접 만든다. 곡선 항목에 **빈 원을 함께** 넣어, 스캔한 부피 위치를
# 별도 항목으로 설명하지 않고 그 라인 자체가 라벨이 되게 한다 (fig_density 와 같은 방식).
h = [plt.Line2D([], [], ls="-", lw=1.6, c=v["col"],
                marker="o", ms=4.2, mfc="w", mec=v["col"], mew=1.1)
     for v in fit.values()]
l = list(fit.keys())
h.append(plt.Line2D([], [], ls="", marker="o", ms=9, mfc="0.5", mec="w", mew=1.5))
# 범례와 아래 상자의 표현을 **일치**시킨다. "equilibrium" / "own rho_0" 로 갈리면
# 읽는 사람이 둘을 매칭하는 단계를 한 번 더 거친다.
l.append(r"$K_0$ at own $\rho_0$ ($P=0$)")
h.append(plt.Line2D([], [], ls="", marker="*", ms=14, mfc="k", mec="w"))
l.append(rf"Fused silica: $K_{{\rm exp}}$ = {K_EXP} GPa")
ax.legend(h, l, loc="upper right", framealpha=0.93, fontsize=8.5,
          handlelength=1.6, borderpad=0.45, labelspacing=0.4)

ax.set_title("Bulk modulus of the same a-SiO$_2$ network", fontsize=11)
fig.tight_layout()
fig.savefig(FIG / "fig_bulkmod.png", dpi=300)
print(f"-> {FIG}/fig_bulkmod.png\n")

print(f"{'rho':>7s}{'BKS':>9s}{'7net':>9s}{'차이%':>8s}")
for r in (2.157, 2.20, 2.2185, 2.25, 2.30, 2.3442):
    vals = [K_of(V_of(r), v["pf"]) if v["rlo"] - 1e-9 <= r <= v["rhi"] + 1e-9 else np.nan
            for v in (b, s)]
    dv = 100 * abs(vals[0] / vals[1] - 1) if np.isfinite(vals).all() else np.nan
    print(f"{r:7.4f}{vals[0]:9.2f}{vals[1]:9.2f}{dv:8.1f}")
print(f"\n각자 평형에서:  BKS {b['K0']:.2f} @ {b['rho0']:.4f}   "
      f"7net {s['K0']:.2f} @ {s['rho0']:.4f}   (겉보기 차 {b['K0']-s['K0']:+.2f} GPa)")
print(f"실험 밀도 2.20 에서:  BKS {kb:.2f} ({100*(kb/K_EXP-1):+.1f} %)   "
      f"7net {ks:.2f} ({100*(ks/K_EXP-1):+.1f} %)   실험 {K_EXP}")
