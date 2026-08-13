#!/usr/bin/env python
"""Fig. density — 같은 유리 네트워크의 평형밀도와 부피탄성률: BKS vs 7net-nano-4.5.

BKS 가 ρ=2.20 고정 NVT 로 만든 **하나의** 네트워크를 두 포텐셜에 각각 넘겨
"너는 어느 부피를 원하냐"고 물었다. 각 부피에서 셀은 고정하고 원자만 0 K 이완.

(a) E(ρ) + Birch-Murnaghan 3차 (E 에 피팅)
(b) P(ρ): LAMMPS virial 실측점 + BM3 를 **P 에 직접** 피팅한 곡선  → K0 = -V dP/dV

★ 세로 점선 3개는 (a)(b) 모두 **P=0 인 밀도**다. (a) 의 E 최소가 아니다.
  그래서 (b) 에서는 선이 P=0 교차점을 지나고, (a) 에서 BKS 만 최소와 0.7 % 어긋나 보인다.
  **이건 두 패널이 어긋난 게 아니라, BKS 에서 -dE/dV != P_virial 이라는 사실 그 자체다.**
  잘린 포텐셜에서는 "E 가 최소인 부피"와 "P 가 0 인 부피"가 서로 다른 양이다.
  7net 은 둘이 0.008 % 라 육안으로 구분이 안 된다. 어느 쪽이 조작적 정답이냐면 P=0 이다
  — NPT 가 virial 로 구동되고, 실제로 BKS 300 K NPT 결과 2.3119 와 0.14 % 일치한다.

★ 왜 (b) 에서 E 가 아니라 P 를 피팅하나 (2026-08 수정)
  BKS 의 Buckingham -C/r^6 는 10 A 에서 뚝 잘린다(shift/tail 보정 없음).
  부피가 변하면 원자쌍이 cutoff 를 넘나들며 E 가 계단처럼 튀는데 virial 은 그 계단을
  못 보므로 -dE/dV != P_virial 이 된다. 해석적 tail 압력 A/V^2 (A=-1.34e6 eV A^3) 로
  -2014 bar @V=32652 가 예측되고 실측 오프셋 -2071 bar 와 일치했다 → 원인 확정.
  7net 은 MLIP 라 **매끄러운 cutoff 함수**를 쓰므로 계단이 없다.
  실험이 재는 것도 탄성률이므로 P(V) 피팅이 원래 더 직접적인 경로다.
  검증: 7net 은 두 경로가 43.08 vs 43.23 GPa (0.4 %) 로 일치한다.
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
RHO_EXP, K_EXP = 2.20, 36.7          # fused silica 실험값 (문헌 인용)


def bm3_E(V, E0, V0, K0, Kp):
    e = (V0 / V) ** (2 / 3) - 1
    return E0 + 9 * V0 * K0 / 16 * (e**3 * Kp + e**2 * (6 - 4 * (V0 / V) ** (2 / 3)))


def bm3_P(V, V0, K0, Kp):            # bar 단위로 바로 뱉는다
    x = (V0 / V) ** (1 / 3)
    return 3 * K0 / 2 * (x**7 - x**5) * (1 + 0.75 * (Kp - 4) * (x**2 - 1)) * EV2BAR


RUN = ROOT / "02_run/s2_relax"
SET = [("BKS", "tab:blue", RUN / "ev_bks_scan.txt"),
       ("7net-nano-4.5", "tab:red", RUN / "ev220_scan.txt")]

fit = {}
for lab, col, fn in SET:
    d = np.loadtxt(fn)
    V, E, P = d[:, 1], d[:, 3], d[:, 5]
    pe, ce = curve_fit(bm3_E, V, E, p0=[E.min(), V[np.argmin(E)], 0.04, 4.0], maxfev=400000)
    pp, cp = curve_fit(bm3_P, V, P, p0=[V[np.argmin(np.abs(P))], 0.04, 4.0], maxfev=400000)
    fit[lab] = dict(col=col, V=V, E=E, P=P, pe=pe, pp=pp,
                    ee=np.sqrt(np.diag(ce)), ep=np.sqrt(np.diag(cp)),
                    rmsE=np.sqrt(((E - bm3_E(V, *pe))**2).mean()) * 1e3,
                    rmsP=np.sqrt(((P - bm3_P(V, *pp))**2).mean()))

RHO0 = {k: rho_of(v["pp"][0]) for k, v in fit.items()}      # 평형밀도는 virial 경로

# ★ 피팅 곡선은 **자기 데이터 구간 안에서만** 그린다 (외삽 금지).
#   BM3 는 피팅 구간 밖에서 빠르게 신뢰를 잃는데, 길게 그려두면 마치 그 영역까지
#   검증된 것처럼 보인다. 양끝 0.5 % 여유만 준다.
for v in fit.values():
    v["Vs"] = np.linspace(v["V"].min() * 0.995, v["V"].max() * 1.005, 400)

# LOO(한 점씩 빼고 재피팅) 산포 = 실질 불확도. curve_fit 의 표준오차는 과소평가다.
for lab, v in fit.items():
    ks = []
    for i in range(len(v["V"])):
        m = np.ones(len(v["V"]), bool); m[i] = False
        p2, _ = curve_fit(bm3_P, v["V"][m], v["P"][m], p0=v["pp"], maxfev=400000)
        ks.append(p2[1] * EV2BAR / 1e4)
    v["loo"] = (np.max(ks) - np.min(ks)) / 2

fig, ax = plt.subplots(1, 2, figsize=(7.8, 3.4))
a, b = ax

# 세로 기준선: 실험 + 두 포텐셜의 평형밀도.
# ★ 세 선 모두 "P = 0 인 밀도"다. (a) 의 E 최소가 아니다 — BKS 는 둘이 0.7 % 어긋나며
#   그게 절단 꼬리 artifact 그 자체다. 범례 제목에 명시해 오해를 막는다.
hx = [a.axvline(RHO_EXP, ls="--", lw=1.2, c="k", alpha=0.7)]
b.axvline(RHO_EXP, ls="--", lw=1.2, c="k", alpha=0.7)
hline = {}
for lab, v in fit.items():
    for ax_ in ax:
        h = ax_.axvline(RHO0[lab], ls=":", lw=1.4, c=v["col"])
    hline[lab] = h

# ---------- (a) E-V ----------
for lab, v in fit.items():
    E0 = v["pe"][0]
    a.plot(rho_of(v["Vs"]), (bm3_E(v["Vs"], *v["pe"]) - E0) / N * 1e3, "-",
           c=v["col"], zorder=2)
    a.plot(rho_of(v["V"]), (v["E"] - E0) / N * 1e3, "o", ms=5, mfc="w",
           mec=v["col"], mew=1.3, zorder=3)
a.set_xlabel(r"$\rho$ (g/cm$^3$)"); a.set_ylabel(r"$E-E_0$ (meV/atom)")
a.set_ylim(-0.5, 13)
# 범례 핸들은 마커가 아니라 **세로선** 이다. 세 선이 무엇인지가 이 패널의 요점이므로.
a.legend([hx[0], hline["BKS"], hline["7net-nano-4.5"]],
         [rf"$\rho_{{\rm exp}}$ = {RHO_EXP:.2f}  (fused silica)",
          rf"BKS:  $\rho_0$ = {RHO0['BKS']:.3f}",
          rf"7net-nano-4.5:  $\rho_0$ = {RHO0['7net-nano-4.5']:.3f}"],
         loc="upper right", framealpha=0.92, fontsize=8, handlelength=1.6,
         borderpad=0.4, labelspacing=0.35,
         title=r"vertical lines: $\rho$ where $P=0$", title_fontsize=7.5)

# ★ BKS 만 E 곡선의 최소(파란 점선의 오른쪽)가 P=0 위치와 어긋난다. 그게 절단 artifact 다.
#   그림에 그대로 보이므로 오해하지 않도록 화살표로 명시한다. (7net 은 0.008 % 라 안 보인다)
#   간격이 0.7 % 라 양방향 화살표로는 안 보인다 → 최소점을 지시선으로 가리키고 값을 적는다.
rE_bks = rho_of(fit["BKS"]["pe"][1])
a.annotate(f"$E$-min {rE_bks:.3f}\n$P$=0    {RHO0['BKS']:.3f}\n(truncated tail)",
           xy=(rE_bks, 0.05), xytext=(2.355, 5.2),
           fontsize=7.5, c="tab:blue", ha="left", va="center",
           multialignment="left", linespacing=1.25,
           arrowprops=dict(arrowstyle="-", lw=0.8, color="tab:blue",
                           connectionstyle="arc3,rad=0.15"))

# ---------- (b) P-V ----------
b.axhline(0, ls="-", lw=0.7, c="0.6")
for lab, v in fit.items():
    b.plot(rho_of(v["Vs"]), bm3_P(v["Vs"], *v["pp"]) / 1e4, "-", c=v["col"], zorder=2)
    b.plot(rho_of(v["V"]), v["P"] / 1e4, "o", ms=5, mfc="w", mec=v["col"],
           mew=1.3, zorder=3)
    K = v["pp"][1] * EV2BAR / 1e4
    b.plot([], [], "o-", c=v["col"], mfc="w", mew=1.3, ms=5,
           label=rf"{lab}:  $K_0$ = {K:.1f} $\pm$ {v['loo']:.1f} GPa")
b.plot([], [], " ", label=rf"exp. fused silica: {K_EXP} GPa")
b.plot([], [], "--", c="k", alpha=0.7, lw=1.2,
       label=rf"$\rho_{{\rm exp}}$ = {RHO_EXP:.2f}")
b.set_xlabel(r"$\rho$ (g/cm$^3$)"); b.set_ylabel(r"$P$ (GPa)")
b.set_ylim(-4.2, 3.2)
b.legend(loc="lower right", framealpha=0.9, fontsize=8, handlelength=1.2,
         borderpad=0.4, labelspacing=0.35)

for k, a_ in enumerate(ax):
    a_.set_xlim(2.05, 2.48)
    a_.xaxis.set_minor_locator(AutoMinorLocator(2))
    a_.yaxis.set_minor_locator(AutoMinorLocator(2))
    a_.text(0.035, 0.91, "(a)" if k == 0 else "(b)", transform=a_.transAxes,
            fontsize=11.5, fontweight="bold")

fig.suptitle(r"a-SiO$_2$ network formed at $\rho$ = 2.20 g/cm$^3$   "
             r"(0 K static relaxation at each volume)", fontsize=10.5, y=1.0)
fig.tight_layout(rect=[0, 0, 1, 1.05])
fig.savefig(FIG / "fig_density.png", dpi=300)
print(f"-> {FIG}/fig_density.png\n")

# ---------------- 수치 요약 ----------------
print(f"{'':16s}{'경로':>7s}{'rho0':>9s}{'K0 (GPa)':>16s}{'K0p':>9s}{'RMS':>13s}")
for lab, v in fit.items():
    print(f"{lab:16s}{'E(V)':>7s}{rho_of(v['pe'][1]):9.4f}"
          f"{v['pe'][2]*EV2BAR/1e4:11.2f} ±{v['ee'][2]*EV2BAR/1e4:4.2f}"
          f"{v['pe'][3]:9.2f}{v['rmsE']:9.1f} meV")
    print(f"{'':16s}{'P(V)':>7s}{rho_of(v['pp'][0]):9.4f}"
          f"{v['pp'][1]*EV2BAR/1e4:11.2f} ±{v['ep'][1]*EV2BAR/1e4:4.2f}"
          f"{v['pp'][2]:9.2f}{v['rmsP']:9.0f} bar")
    dK = abs(v['pe'][2] - v['pp'][1]) / v['pp'][1] * 100
    dr = abs(rho_of(v['pe'][1]) - rho_of(v['pp'][0])) / rho_of(v['pp'][0]) * 100
    print(f"{'':16s}두 경로 차이:  rho0 {dr:.3f} %,  K0 {dK:.1f} %"
          f"{'   <- 절단 꼬리 artifact' if dK > 2 else '   <- 정합'}\n")

print(f"실험 대비:  rho0  BKS {RHO0['BKS']:.4f} ({100*(RHO0['BKS']/RHO_EXP-1):+.2f} %)"
      f"   7net {RHO0['7net-nano-4.5']:.4f} ({100*(RHO0['7net-nano-4.5']/RHO_EXP-1):+.2f} %)")
KB, K7 = fit["BKS"]["pp"][1]*EV2BAR/1e4, fit["7net-nano-4.5"]["pp"][1]*EV2BAR/1e4
print(f"            K0    BKS {KB:.2f} ({100*(KB/K_EXP-1):+.1f} %)"
      f"   7net {K7:.2f} ({100*(K7/K_EXP-1):+.1f} %)     exp {K_EXP} GPa")
