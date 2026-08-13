#!/usr/bin/env python
"""S2-2  E-V 스캔 분석: Birch-Murnaghan 3차 피팅 + virial vs -dE/dV consistency.

검증 논리:
  BM3를 E(V)에 피팅 -> 해석적 -dE/dV = P_fit  (에너지만 사용, virial 미사용)
  LAMMPS 보고 press 에서 운동에너지항을 빼서 P_virial 산출
  둘이 맞으면 pair_e3gnn 의 응력 구현이 에너지와 정합한다는 뜻.

주의: in.relax / in.ev 가 velocity 를 0으로 죽이지 않아, data 파일이 들고 온
      T=302.3 K 속도가 그대로 남아 press 에 운동에너지항이 섞여 있다.
      P_kin = (N-1) kB T / V 로 제거한다.
"""
import numpy as np
from scipy.optimize import curve_fit
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
DAT, FIG = ROOT / "04_analysis/dat", ROOT / "04_analysis/fig"
FIG.mkdir(exist_ok=True); DAT.mkdir(exist_ok=True)


EV2BAR = 1.602176634e6
KB = 8.617333262e-5
N = 2160
T_DATA = 0.0          # sio2_quenched.data 속도가 대응하는 온도 (S1에서 독립 산출)
MASS_SUM = 43260.70     # amu, 720 Si + 1440 O
RHO = lambda V: MASS_SUM * 1.66053907 / V

d = np.loadtxt(f"{ROOT}/02_run/s2_relax/ev220_scan.txt")
V, E, P_lmp = d[:, 1], d[:, 3], d[:, 5]


def bm3_E(V, E0, V0, K0, Kp):
    e = (V0 / V) ** (2 / 3) - 1
    return E0 + 9 * V0 * K0 / 16 * (e**3 * Kp + e**2 * (6 - 4 * (V0 / V) ** (2 / 3)))


def bm3_P(V, E0, V0, K0, Kp):
    x = (V0 / V) ** (1 / 3)
    return 3 * K0 / 2 * (x**7 - x**5) * (1 + 0.75 * (Kp - 4) * (x**2 - 1))


p0 = [E.min(), V[np.argmin(E)], 0.04, 4.0]
pf, pc = curve_fit(bm3_E, V, E, p0=p0, maxfev=400000)
err = np.sqrt(np.diag(pc))
E0, V0, K0, Kp = pf

P_kin = (N - 1) * KB * T_DATA / V * EV2BAR
P_vir = P_lmp - P_kin
P_fit = bm3_P(V, *pf) * EV2BAR
resid = E - bm3_E(V, *pf)

print("=== Birch-Murnaghan 3차 (E-V 피팅, virial 미사용) ===")
print(f"  V0  = {V0:9.2f} +- {err[1]:.2f} A^3   -> rho0 = {RHO(V0):.4f} g/cm3")
print(f"  K0  = {K0*EV2BAR/1e4:7.2f} +- {err[2]*EV2BAR/1e4:.2f} GPa")
print(f"  K0' = {Kp:7.3f} +- {err[3]:.3f}")
print(f"  E0  = {E0/N:.6f} eV/atom")
print(f"  RMS residual = {np.sqrt((resid**2).mean())*1e3:.1f} meV (전체 에너지 범위 {np.ptp(E):.1f} eV)")

print("\n=== virial 정합성 (P_kin = (N-1)kT/V, T=302.3 K 제거) ===")
print("   V(A^3)   rho     P_LAMMPS    P_kin    P_virial    P=-dE/dV     diff    diff%")
for i in range(len(V)):
    dd = P_fit[i] - P_vir[i]
    print(f"{V[i]:9.1f} {RHO(V[i]):6.4f} {P_lmp[i]:10.1f} {P_kin[i]:8.1f} "
          f"{P_vir[i]:10.1f} {P_fit[i]:11.1f} {dd:8.1f} {100*dd/max(abs(P_vir[i]),1):7.2f}")

c = np.polyfit(V, P_vir, 3)
r = np.roots(c); r = r[np.isreal(r)].real
r = r[(r > V.min()) & (r < V.max())][0]
print(f"\n  virial P=0 at V = {r:.1f} A^3 -> rho = {RHO(r):.4f} g/cm3")
print(f"  BM3  dE/dV=0 at V = {V0:.1f} A^3 -> rho = {RHO(V0):.4f} g/cm3")
print(f"  두 경로 차이: {100*abs(r-V0)/V0:.3f} %")

# ---- 그림 ----
Vs = np.linspace(V.min() * 0.995, V.max() * 1.005, 400)
fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))

ax[0].plot(Vs, (bm3_E(Vs, *pf) - E0) / N * 1e3, "-", lw=1.6, label="BM3 fit")
ax[0].plot(V, (E - E0) / N * 1e3, "o", ms=6, label="7net-nano-4.5")
ax[0].axvline(V0, ls="--", c="0.5", lw=1)
ax[0].axvline(32652.5, ls=":", c="crimson", lw=1.2)
ax[0].text(32652.5, ax[0].get_ylim()[1]*0.92, " BKS\n 2.607", color="crimson", fontsize=8, va="top")
ax[0].text(V0, ax[0].get_ylim()[1]*0.55, f" $V_0$\n {RHO(V0):.3f}", color="0.3", fontsize=8, va="top")
ax[0].set_xlabel(r"$V$ ($\rm\AA^3$)"); ax[0].set_ylabel(r"$E-E_0$ (meV/atom)")
ax[0].set_title("E-V (0 K static relaxation)"); ax[0].legend(fontsize=8)

ax[1].plot(Vs, bm3_P(Vs, *pf) * EV2BAR / 1e4, "-", lw=1.6, label=r"$-dE/dV$ (BM3)")
ax[1].plot(V, P_vir / 1e4, "o", ms=6, label="LAMMPS virial")
ax[1].plot(V, P_lmp / 1e4, "x", ms=6, c="0.6", label="LAMMPS press (incl. kinetic)")
ax[1].axhline(0, ls="--", c="0.5", lw=1)
ax[1].set_xlabel(r"$V$ ($\rm\AA^3$)"); ax[1].set_ylabel("P (GPa)")
ax[1].set_title("virial vs -dE/dV consistency"); ax[1].legend(fontsize=8)

for a in ax:
    sec = a.secondary_xaxis("top", functions=(RHO, lambda r_: MASS_SUM * 1.66053907 / r_))
    sec.set_xlabel(r"$\rho$ (g/cm$^3$)", fontsize=9)
fig.tight_layout()
fig.savefig(f"{FIG}/ev220_fit.png", dpi=160)
print("\n-> ev220_fit.png 저장")
