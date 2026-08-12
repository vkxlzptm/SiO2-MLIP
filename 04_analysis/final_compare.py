#!/usr/bin/env python
"""최종 3자 비교 (2x2): BKS vs SevenNet-nano-4.5 vs AIMD PBE(Dechant, digitize)
   전부 ρ = 2.20 g/cm³, 300 K.

g(r) 세 패널은 동일한 r 범위(1~8 Å)를 쓴다. Si-O 도 4.1 Å 부근에 2차 feature 가 있다.
AIMD digitize 신뢰도는 1차 배위수로 자체 검증했고 패널마다 표기한다.
"""
import numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt

OURS = [("BKS", "../02_run/s0_requench/bks220_gr.dat",
         "../02_run/s0_requench/bks220_angles.dat", "tab:blue"),
        ("SevenNet-nano-4.5", "../02_run/s3_md/7net220_gr.dat",
         "../02_run/s3_md/7net220_angles.dat", "tab:red")]
AI = np.loadtxt("dechant_pdf_digitized.dat")      # r, gSiO, gOO, gSiSi
BAD = np.loadtxt("dechant_bad_digitized.dat")     # angle, P_LES, P_HES

EXP = {"Si-O": 1.61, "O-O": 2.63, "Si-Si": 3.08}          # Dechant Table 1, experimental
AIT = {"Si-O": 1.63, "O-O": 2.67, "Si-Si": 3.03}          # Dechant Table 1, AIMD
CNCHK = {"Si-O": "CN 2.6 vs 4 (amplitude unreliable)",
         "O-O": "CN 7.1 vs 6", "Si-Si": "CN 4.2 vs 4"}
RLIM = (1.0, 8.0)                                          # 세 패널 공통

panels = [("Si-O", 1, (1.3, 2.1), 34), ("O-O", 2, (2.1, 3.3), 8),
          ("Si-Si", 3, (2.4, 3.8), 8)]

fig, axes = plt.subplots(2, 2, figsize=(11.5, 7.6))
ax = axes.ravel()

for k, (pair, col, pk, ymax) in enumerate(panels):
    a = ax[k]
    for lab, gp, _, c in OURS:
        d = np.loadtxt(gp); r = d[:, 0]; g = d[:, k + 1]
        a.plot(r, g, "-", lw=1.4, c=c, label=lab)
        m = (r > pk[0]) & (r < pk[1])
        a.axvline(r[m][np.argmax(g[m])], ls=":", lw=0.9, c=c)
    a.plot(AI[:, 0], AI[:, col], "-", lw=1.4, c="tab:green",
           label="AIMD PBE, Dechant 2026 (digitized)")
    a.axvline(AIT[pair], ls="--", lw=1.1, c="tab:green")
    a.axvline(EXP[pair], ls="--", lw=1.1, c="k")
    a.axhline(1.0, ls="-", lw=0.6, c="0.8")
    # 1피크 위치를 세로 라벨 대신 우측 상단 블록으로 (겹침 방지)
    pos = []
    for lab, gp, _, c in OURS:
        d2 = np.loadtxt(gp); r2 = d2[:, 0]; m2 = (r2 > pk[0]) & (r2 < pk[1])
        pos.append((f"{lab.split('-')[0]:<9s}{r2[m2][np.argmax(d2[m2, k+1])]:.3f}", c))
    mA_ = (AI[:, 0] > pk[0]) & (AI[:, 0] < pk[1])
    pos.append((f"{'AIMD':<9s}{AIT[pair]:.3f}", "tab:green"))
    pos.append((f"{'exp':<9s}{EXP[pair]:.3f}", "k"))
    for j, (t, c) in enumerate(pos):
        a.text(0.97, 0.93 - 0.075 * j, t, transform=a.transAxes, fontsize=7,
               c=c, ha="right", family="monospace")
    a.text(0.97, 0.93 - 0.075 * len(pos) - 0.02, CNCHK[pair], transform=a.transAxes,
           fontsize=6.3, c="tab:green", ha="right", style="italic")
    a.set_xlim(*RLIM); a.set_ylim(0, ymax)
    a.set_xlabel(r"$r$ ($\rm\AA$)"); a.set_ylabel(rf"$g_{{\rm {pair}}}(r)$")
    a.set_title(f"{pair} pair distribution")
ax[0].legend(fontsize=7.5, loc="center right")

a = ax[3]
for lab, _, ap, c in OURS:
    d = np.loadtxt(ap)
    a.plot(d[:, 0], d[:, 1], "-", lw=1.4, c=c, label=lab)
    mm = (d[:, 0] * d[:, 1]).sum() / d[:, 1].sum()
    a.axvline(mm, ls=":", lw=0.9, c=c)
a.plot(BAD[:, 0], BAD[:, 1], "-", lw=1.4, c="tab:green",
       label="AIMD PBE, Dechant 2026 (digitized)")
mA = np.trapezoid(BAD[:, 0] * BAD[:, 1], BAD[:, 0])
a.axvline(mA, ls=":", lw=0.9, c="tab:green")
a.axvline(146.1, ls="--", lw=1.1, c="k")
a.text(0.97, 0.33, f"mean\nBKS      151.9\n7net     145.1\nAIMD     138.6\nexp*     146.1",
       transform=a.transAxes, fontsize=7, ha="right", va="top", family="monospace")
a.text(0.97, 0.055, "*exp: 2d(Si-O)sin(theta/2)=d(Si-Si)\n  from 1.61 and 3.08",
       transform=a.transAxes, fontsize=6.3, ha="right", style="italic")
a.set_xlim(100, 180); a.set_xlabel(r"Si-O-Si angle (deg)")
a.set_ylabel(r"$P(\theta)$ (1/deg)")
a.set_title("Si-O-Si bond angle distribution")
a.legend(fontsize=7.5, loc="upper left", framealpha=0.95)

fig.suptitle(r"a-SiO$_2$ at $\rho$ = 2.20 g/cm$^3$, 300 K   "
             r"(dotted = 1st-peak / mean, dashed = reference)", fontsize=10)
fig.tight_layout(rect=[0, 0, 1, 0.96])
fig.savefig("final_compare.png", dpi=160)
print("-> final_compare.png")

print("\n1피크 위치 (Å) / 평균각 (deg)")
print(f"{'':20s}{'Si-O':>8s}{'O-O':>8s}{'Si-Si':>8s}{'Si-O-Si':>10s}")
for lab, gp, ap, _ in OURS:
    d = np.loadtxt(gp); r = d[:, 0]; aa = np.loadtxt(ap)
    v = [r[(r > p[0]) & (r < p[1])][np.argmax(d[(r > p[0]) & (r < p[1]), i + 1])]
         for i, (_n, _c, p, _y) in enumerate(panels)]
    mm = (aa[:, 0] * aa[:, 1]).sum() / aa[:, 1].sum()
    print(f"{lab:20s}{v[0]:8.3f}{v[1]:8.3f}{v[2]:8.3f}{mm:10.2f}")
print(f"{'AIMD (Table 1)':20s}{1.63:8.3f}{2.67:8.3f}{3.03:8.3f}{138.50:10.2f}")
print(f"{'실험':20s}{1.61:8.3f}{2.63:8.3f}{3.08:8.3f}{146.10:10.2f}")
