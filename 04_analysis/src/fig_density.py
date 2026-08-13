#!/usr/bin/env python
"""Fig. density — 7net-nano-4.5 의 평형밀도 (E-V 스캔, ρ=2.20 네트워크).

(a) E(ρ) 와 Birch-Murnaghan 3차 피팅 → V0
(b) P(ρ): LAMMPS virial 실측점과 피팅에서 얻은 −dE/dV. 둘이 맞으면 응력 구현이 정합.

같은 네트워크(BKS 가 ρ=2.20 고정 NVT 로 만든 유리)를 두 포텐셜에 각각 "어느 부피를
원하냐"고 물은 결과를 비교한다: BKS 2.3119 (300 K NPT 실측) vs SevenNet 2.2187.
"""
from pathlib import Path

import numpy as np
from scipy.optimize import curve_fit
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator

ROOT = Path(__file__).resolve().parents[2]
FIG = ROOT / "04_analysis/fig"; FIG.mkdir(exist_ok=True)

plt.rcParams.update({
    "font.size": 10, "axes.labelsize": 11, "xtick.labelsize": 10, "ytick.labelsize": 10,
    "legend.fontsize": 9, "legend.handlelength": 1.5,
    "xtick.direction": "in", "ytick.direction": "in",
    "xtick.top": True, "ytick.right": True,
    "xtick.major.size": 5, "ytick.major.size": 5,
    "xtick.minor.size": 2.8, "ytick.minor.size": 2.8,
    "axes.linewidth": 0.9, "lines.linewidth": 1.4,
})

EV2BAR = 1.602176634e6
N = 2160
MASS = 43260.70                      # amu
rho_of = lambda V: MASS * 1.66053907 / V
RHO_BKS, RHO_EXP = 2.3119, 2.20      # BKS 300 K NPT 실측 / 실험 fused silica

d = np.loadtxt(ROOT / "02_run/s2_relax/ev220_scan.txt")
V, E, P = d[:, 1], d[:, 3], d[:, 5]


def bm3_E(V, E0, V0, K0, Kp):
    e = (V0 / V) ** (2 / 3) - 1
    return E0 + 9 * V0 * K0 / 16 * (e**3 * Kp + e**2 * (6 - 4 * (V0 / V) ** (2 / 3)))


def bm3_P(V, E0, V0, K0, Kp):
    x = (V0 / V) ** (1 / 3)
    return 3 * K0 / 2 * (x**7 - x**5) * (1 + 0.75 * (Kp - 4) * (x**2 - 1))


pf, pc = curve_fit(bm3_E, V, E, p0=[E.min(), V[np.argmin(E)], 0.04, 4.0], maxfev=400000)
err = np.sqrt(np.diag(pc))
E0, V0, K0, Kp = pf
RHO0 = rho_of(V0)
Vs = np.linspace(V.min() * 0.995, V.max() * 1.005, 500)

fig, ax = plt.subplots(1, 2, figsize=(7.8, 3.4))

# ---------- (a) E-V ----------
a = ax[0]
a.axvline(RHO_EXP, ls="--", lw=1.2, c="k", alpha=0.7)
a.axvline(RHO_BKS, ls="--", lw=1.2, c="tab:blue", alpha=0.7)
a.axvline(RHO0, ls=":", lw=1.4, c="tab:red")
a.plot(rho_of(Vs), (bm3_E(Vs, *pf) - E0) / N * 1e3, "-", c="tab:red",
       label="Birch-Murnaghan 3rd")
a.plot(rho_of(V), (E - E0) / N * 1e3, "o", ms=5, mfc="w", mec="tab:red", mew=1.3,
       label="7net-nano-4.5")
a.set_xlabel(r"$\rho$ (g/cm$^3$)"); a.set_ylabel(r"$E-E_0$ (meV/atom)")
# ymax 13: (a) 태그가 왼쪽 팔(빨간 곡선)과 겹치지 않도록 위쪽 여유 확보
a.set_ylim(-0.5, 13)
a.legend(loc="upper right", framealpha=0.9)

# ---------- (b) P-V ----------
b = ax[1]
b.axhline(0, ls="-", lw=0.7, c="0.6")
b.axvline(RHO_EXP, ls="--", lw=1.2, c="k", alpha=0.7)
b.axvline(RHO_BKS, ls="--", lw=1.2, c="tab:blue", alpha=0.7)
b.axvline(RHO0, ls=":", lw=1.4, c="tab:red")
b.plot(rho_of(Vs), bm3_P(Vs, *pf) * EV2BAR / 1e4, "-", c="tab:red",
       label=r"$-\,dE/dV$ (BM3 fit)")
b.plot(rho_of(V), P / 1e4, "o", ms=5, mfc="w", mec="k", mew=1.3,
       label="LAMMPS virial")
b.set_xlabel(r"$\rho$ (g/cm$^3$)"); b.set_ylabel(r"$P$ (GPa)")
# 좌상단은 (b) 태그 자리 → bbox 로 태그 아래에 고정
b.legend(loc="upper left", bbox_to_anchor=(0.015, 0.87), framealpha=0.9)

for k, a_ in enumerate(ax):
    a_.set_xlim(2.05, 2.38)
    a_.xaxis.set_minor_locator(AutoMinorLocator(2))
    a_.yaxis.set_minor_locator(AutoMinorLocator(2))
    a_.text(0.035, 0.91, "(a)" if k == 0 else "(b)", transform=a_.transAxes,
            fontsize=11.5, fontweight="bold")

# 밀도 라벨: 곡선이 좌하→우상 이므로 **곡선 아래쪽**이 비어 있다. 거기에 배치.
# 2.20 과 2.219 는 0.019 밖에 안 떨어지므로 좌/우 정렬과 높이를 엇갈리게 준다.
y0, y1 = ax[1].get_ylim()
# 유효숫자: 실험값은 **인용값 그대로** 2.20 (fused silica 는 시료마다 3번째 소수에서
# 흔들려 자릿수를 늘리면 없는 정밀도를 만드는 셈). 계산값은 피팅 정밀도가 받쳐주므로
# 소수 3자리까지 쓴다 (V0 = 32377.9 ± 0.5 A^3 → rho0 불확도 ~3e-5).
# 두 줄짜리 라벨은 중앙 정렬(ha="center", multialignment="center")이 보기 좋다.
# 대신 x 를 선에서 살짝 밀고 높이를 엇갈리게 해 2.20 / 2.219 겹침을 피한다.
lab = [(RHO_EXP, "exp\n2.20", "k", -0.022, 0.10),
       (RHO0, "7net\n2.219", "tab:red", +0.022, 0.32),
       (RHO_BKS, "BKS\n2.312", "tab:blue", -0.022, 0.10)]
for x, t, c, dx, fy in lab:
    ax[1].text(x + dx, y0 + fy * (y1 - y0), t, fontsize=8.5, c=c,
               ha="center", va="center", multialignment="center",
               bbox=dict(fc="white", ec="none", alpha=0.6, pad=0.8))

# suptitle 과 axes 간격: rect 상단과 y 를 가깝게 두면 붙는다 (fig_speed 와 동일).
fig.suptitle(r"a-SiO$_2$ network formed at $\rho$ = 2.20 g/cm$^3$   "
             r"(0 K static relaxation at each volume)", fontsize=10.5, y=1.0)
fig.tight_layout(rect=[0, 0, 1, 1.05])
fig.savefig(FIG / "fig_density.png", dpi=300)
print(f"-> {FIG}/fig_density.png\n")

print("Birch-Murnaghan 3차 (E-V 만 사용, virial 미사용)")
print(f"  V0  = {V0:9.2f} ± {err[1]:.2f} A^3   ->  rho0 = {RHO0:.4f} g/cm^3")
print(f"  K0  = {K0*EV2BAR/1e4:7.2f} ± {err[2]*EV2BAR/1e4:.2f} GPa")
print(f"  K0' = {Kp:7.3f} ± {err[3]:.3f}")
print(f"  E0  = {E0/N:.6f} eV/atom,  RMS residual = "
      f"{np.sqrt(((E-bm3_E(V,*pf))**2).mean())*1e3:.1f} meV")
c = np.polyfit(V, P, 3); r = np.roots(c); r = r[np.isreal(r)].real
r = r[(r > V.min()) & (r < V.max())][0]
print(f"  virial P=0 at rho = {rho_of(r):.4f}  (BM3 와 {100*abs(rho_of(r)-RHO0)/RHO0:.3f} % 차이)")
print(f"\n밀도 비교:  BKS {RHO_BKS:.4f} (+{100*(RHO_BKS/RHO_EXP-1):.2f} %)  |  "
      f"7net {RHO0:.4f} (+{100*(RHO0/RHO_EXP-1):.2f} %)  |  exp {RHO_EXP:.2f}")
