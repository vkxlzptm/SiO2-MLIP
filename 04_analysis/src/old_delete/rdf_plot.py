#!/usr/bin/env python
"""LAMMPS compute rdf (ave/time vector) 파일을 읽어 partial g(r) 비교 그림."""
import numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
import sys


def read_rdf(path):
    L = [l for l in open(path) if not l.startswith("#")]
    n = int(L[0].split()[1])
    d = np.array([[float(x) for x in l.split()[1:]] for l in L[1:1 + n]])
    # r, g_OO, c_OO, g_SiO, c_SiO, g_SiSi, c_SiSi
    return d[:, 0], {"O-O": d[:, 1], "Si-O": d[:, 3], "Si-Si": d[:, 5]}


sets = [("BKS  rho=2.20  300 K", "../02_run/s0_requench/rdf_bks220.dat", "tab:blue")]
# SevenNet 결과가 생기면 여기에 추가:
#   ("7net-nano-4.5 rho=2.20 300 K", "../02_run/s3_md/rdf_7net220_3ps.dat", "tab:red")
import os
extra = "../02_run/s3_md/rdf_7net220_3ps.dat"
if os.path.exists(extra):
    sets.append(("7net-nano-4.5  rho=2.20  300 K", extra, "tab:red"))

# 문헌 1피크 위치 (본문 수치, digitize 아님)
REF = {
    "Si-O":  [("exp 1.61-1.62", 1.615), ("CPMD PW91 1.65", 1.65)],
    "O-O":   [("CPMD PW91 2.68", 2.68)],
    "Si-Si": [("CPMD PW91 3.18", 3.18)],
}

fig, ax = plt.subplots(1, 3, figsize=(13, 3.8))
for k, pair in enumerate(["Si-O", "O-O", "Si-Si"]):
    for label, path, c in sets:
        r, g = read_rdf(path)
        ax[k].plot(r, g[pair], "-", lw=1.4, c=c, label=label)
        m = {"Si-O": (r > 1.3) & (r < 2.0), "O-O": (r > 2.2) & (r < 3.2),
             "Si-Si": (r > 2.8) & (r < 3.6)}[pair]
        rp = r[m][np.argmax(g[pair][m])]
        ax[k].axvline(rp, ls=":", lw=1, c=c)
        ax[k].text(rp, ax[k].get_ylim()[1] * 0.02, f" {rp:.3f}", c=c, fontsize=8)
    for lab, rv in REF[pair]:
        ax[k].axvline(rv, ls="--", lw=1, c="0.55")
    ax[k].set_xlim(1, 6); ax[k].set_xlabel(r"$r$ ($\rm\AA$)")
    ax[k].set_ylabel(f"$g_{{{pair}}}(r)$"); ax[k].set_title(pair)
ax[2].legend(fontsize=7, loc="upper right")
# Si-Si 결함 구간 강조
ax[2].axvspan(2.2, 2.7, color="crimson", alpha=0.10)
ax[2].text(2.45, ax[2].get_ylim()[1] * 0.75, "defect\nregion", fontsize=7,
           color="crimson", ha="center")
fig.tight_layout(); fig.savefig("rdf_compare.png", dpi=160)
print("-> rdf_compare.png")
for label, path, _ in sets:
    r, g = read_rdf(path)
    m = (r > 2.2) & (r < 2.7)
    print(f"{label}:  Si-Si 2.2-2.7 A 최대 g = {g['Si-Si'][m].max():.4f}  (Dechant 결함 지표)")
