#!/usr/bin/env python
"""재quench(ρ=2.20 고정 NVT) 결과 요약: PE-T 곡선에서 Tg 추정 + 그림."""
import numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt

d = np.loadtxt("qt_from_log.dat")          # T, PotEng(eV), Press(bar)
T, E, P = d[:, 0], d[:, 1] / 2160 * 1000, d[:, 2]   # E → meV/atom

# 고온/저온 두 직선을 각각 피팅해 교점을 Tg로 (표준적인 방법)
hi = T > 3000
lo = T < 1500
ah = np.polyfit(T[hi], E[hi], 1)
al = np.polyfit(T[lo], E[lo], 1)
Tg = (al[1] - ah[1]) / (ah[0] - al[0])
print(f"고온 기울기 {ah[0]*1000:.3f} meV/atom/kK   저온 기울기 {al[0]*1000:.3f} meV/atom/kK")
print(f"교점 Tg ≈ {Tg:.0f} K")
print(f"압력 (ρ=2.20 고정): 4000 K {P[0]:+.0f} bar → 300 K {P[-1]:+.0f} bar")

fig, ax = plt.subplots(1, 2, figsize=(11, 4))
ax[0].plot(T, E, "o-", ms=4)
x = np.linspace(300, 4100, 10)
ax[0].plot(x, np.polyval(ah, x), "--", lw=1, c="0.5")
ax[0].plot(x, np.polyval(al, x), "--", lw=1, c="0.5")
ax[0].axvline(Tg, ls=":", c="crimson")
ax[0].text(Tg, E.min() + 0.55 * np.ptp(E), f" $T_g\\approx${Tg:.0f} K", c="crimson", fontsize=9)
ax[0].set_xlabel("T (K)"); ax[0].set_ylabel("PotEng (meV/atom)")
ax[0].set_title(r"BKS quench @ fixed $\rho$=2.20 (NVT)")

ax[1].plot(T, P / 1e4, "o-", ms=4)
ax[1].axhline(0, ls="--", c="0.5", lw=1)
ax[1].set_xlabel("T (K)"); ax[1].set_ylabel("P (GPa)")
ax[1].set_title(r"Pressure at fixed $\rho$=2.20  (BKS wants to contract)")
fig.tight_layout(); fig.savefig("quench220_fit.png", dpi=160)
print("-> quench220_fit.png")
