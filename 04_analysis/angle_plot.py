#!/usr/bin/env python
"""결합각 분포 비교: BKS vs SevenNet-nano-4.5 @ ρ=2.20, 300 K, 3 ps."""
import numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt

S = [("BKS", "../02_run/s0_requench/bks220_angles.dat", "tab:blue"),
     ("7net-nano-4.5", "../02_run/s3_md/7net220_angles.dat", "tab:red")]

# 문헌 평균값 (본문 수치)
REF_SIOSI = [("MTP npj2024  145.5", 145.5, "tab:green"),
             ("CPMD PW91  146", 146.0, "0.4"),
             ("BKS lit.  150-152", 151.0, "0.7")]

fig, ax = plt.subplots(1, 2, figsize=(11, 4))
for lab, p, c in S:
    d = np.loadtxt(p)
    ax[0].plot(d[:, 0], d[:, 1], "-", lw=1.5, c=c, label=lab)
    ax[1].plot(d[:, 0], d[:, 2], "-", lw=1.5, c=c, label=lab)
    m = d[:, 1] > 0
    mean = (d[m, 0] * d[m, 1]).sum() / d[m, 1].sum()
    ax[0].axvline(mean, ls=":", lw=1, c=c)

for lab, v, c in REF_SIOSI:
    ax[0].axvline(v, ls="--", lw=1, c=c)
    ax[0].text(v, ax[0].get_ylim()[1] * 0.97, " " + lab, rotation=90,
               fontsize=7, c=c, va="top")

ax[0].set_xlim(100, 180); ax[0].set_xlabel("Si-O-Si angle (deg)")
ax[0].set_ylabel("P (1/deg)"); ax[0].set_title("Si-O-Si  (discriminating)")
ax[0].legend(fontsize=8, loc="upper left")

ax[1].axvline(109.4, ls="--", lw=1, c="0.4")
ax[1].text(109.4, ax[1].get_ylim()[1] * 0.97, " exp 109.4", rotation=90,
           fontsize=7, c="0.4", va="top")
ax[1].set_xlim(85, 135); ax[1].set_xlabel("O-Si-O angle (deg)")
ax[1].set_ylabel("P (1/deg)"); ax[1].set_title("O-Si-O  (no discriminating power)")
ax[1].legend(fontsize=8)

fig.tight_layout(); fig.savefig("angle_compare.png", dpi=160)
print("-> angle_compare.png")
