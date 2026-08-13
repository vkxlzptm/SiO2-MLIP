#!/usr/bin/env python
"""최종 3자 비교 (2x2): BKS vs SevenNet-nano-4.5 vs AIMD PBE(Dechant 2026, digitize)
   전부 ρ = 2.20 g/cm³, 300 K.

- g(r) 세 패널은 공통 r 범위 1~8 Å (Si-O 도 4.1 Å 부근에 2차 feature 가 있다).
- 피크 위치는 그림에 세로선으로 넣지 않는다(거의 겹쳐 판독 불가). 아래 표로만 출력.
- Si-O 는 1피크가 뾰족해 r=[1.4,1.8] inset 으로 확대.
- BAD 는 곡선이 잘 갈리므로 평균·실험값을 세로선으로 표시.
"""
import numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt

plt.rcParams.update({"font.size": 10, "axes.titlesize": 11, "axes.labelsize": 10,
                     "xtick.labelsize": 9, "ytick.labelsize": 9, "legend.fontsize": 8.5})

OURS = [("BKS", "../02_run/s0_requench/bks220_gr.dat",
         "../02_run/s0_requench/bks220_angles.dat", "tab:blue"),
        ("SevenNet-nano-4.5", "../02_run/s3_md/7net220_gr.dat",
         "../02_run/s3_md/7net220_angles.dat", "tab:red")]
AI = np.loadtxt("dechant_pdf_digitized.dat")      # r, gSiO, gOO, gSiSi
BAD = np.loadtxt("dechant_bad_digitized.dat")     # angle, P_LES, P_HES
AILAB = "AIMD PBE (Dechant 2026)"
EXP = {"Si-O": 1.61, "O-O": 2.63, "Si-Si": 3.08}
RLIM = (1.0, 8.0)

panels = [("Si-O", 1, (1.3, 2.1), 36), ("O-O", 2, (2.1, 3.3), 7.5),
          ("Si-Si", 3, (2.4, 3.8), 7.5)]

fig, axes = plt.subplots(2, 2, figsize=(9.2, 6.6))
ax = axes.ravel()

for k, (pair, col, pk, ymax) in enumerate(panels):
    a = ax[k]
    for lab, gp, _, c in OURS:
        d = np.loadtxt(gp)
        a.plot(d[:, 0], d[:, k + 1], "-", lw=1.3, c=c, label=lab)
    a.plot(AI[:, 0], AI[:, col], "-", lw=1.3, c="tab:green", label=AILAB)
    a.set_xlim(*RLIM); a.set_ylim(0, ymax)
    a.set_xlabel(r"$r$ ($\rm\AA$)"); a.set_ylabel(rf"$g_{{\rm {pair}}}(r)$")
    a.set_title(f"{pair}")

    if pair == "Si-O":                       # 1피크 확대 inset
        ins = a.inset_axes([0.44, 0.36, 0.53, 0.58])
        for lab, gp, _, c in OURS:
            d = np.loadtxt(gp)
            ins.plot(d[:, 0], d[:, 1], "-", lw=1.3, c=c)
        ins.plot(AI[:, 0], AI[:, 1], "-", lw=1.3, c="tab:green")
        ins.set_xlim(1.40, 1.80); ins.set_ylim(0, ymax)
        ins.tick_params(labelsize=7.5); ins.set_xticks([1.4, 1.5, 1.6, 1.7, 1.8])
        a.indicate_inset_zoom(ins, edgecolor="0.4", lw=0.8)

ax[0].legend(loc="lower left", framealpha=0.9)

# ---- Si-O-Si BAD ----
a = ax[3]
means = []
for lab, _, ap, c in OURS:
    d = np.loadtxt(ap)
    a.plot(d[:, 0], d[:, 1], "-", lw=1.3, c=c, label=lab)
    m = (d[:, 0] * d[:, 1]).sum() / d[:, 1].sum()
    means.append((lab, m)); a.axvline(m, ls=":", lw=1.1, c=c)
a.plot(BAD[:, 0], BAD[:, 1], "-", lw=1.3, c="tab:green", label=AILAB)
mA = np.trapezoid(BAD[:, 0] * BAD[:, 1], BAD[:, 0])
means.append(("AIMD", mA)); a.axvline(mA, ls=":", lw=1.1, c="tab:green")
a.axvline(146.1, ls="--", lw=1.2, c="k")
a.text(146.1, a.get_ylim()[1] * 0.03, "  exp 146.1", rotation=90, fontsize=8, va="bottom")
a.set_xlim(100, 180); a.set_ylim(0, None)
a.set_xlabel("Si-O-Si angle (deg)"); a.set_ylabel(r"$P(\theta)$  (deg$^{-1}$)")
a.set_title("Si-O-Si bond angle distribution")
a.legend(loc="upper right", framealpha=0.9)

fig.suptitle(r"a-SiO$_2$ at $\rho$ = 2.20 g/cm$^3$, 300 K", fontsize=12)
fig.tight_layout(rect=[0, 0, 1, 0.955])
fig.savefig("final_compare.png", dpi=170)
print("-> final_compare.png\n")

# ---- 수치는 표로 ----
hdr = f"{'':20s}{'Si-O':>8s}{'O-O':>8s}{'Si-Si':>8s}{'Si-O-Si':>10s}"
print("1피크 위치 (Å) / Si-O-Si 평균 (deg)"); print(hdr)
for (lab, gp, ap, _), (_, mm) in zip(OURS, means):
    d = np.loadtxt(gp); r = d[:, 0]
    v = [r[(r > p[0]) & (r < p[1])][np.argmax(d[(r > p[0]) & (r < p[1]), i + 1])]
         for i, (_n, _c, p, _y) in enumerate(panels)]
    print(f"{lab:20s}{v[0]:8.3f}{v[1]:8.3f}{v[2]:8.3f}{mm:10.2f}")
print(f"{'AIMD (Table 1)':20s}{1.63:8.3f}{2.67:8.3f}{3.03:8.3f}{138.50:10.2f}")
print(f"{'AIMD (digitized)':20s}"
      + "".join(f"{AI[(AI[:,0]>p[0])&(AI[:,0]<p[1]),0][np.argmax(AI[(AI[:,0]>p[0])&(AI[:,0]<p[1]), i+1])]:8.3f}"
                for i, (_n, _c, p, _y) in enumerate(panels)) + f"{mA:10.2f}")
print(f"{'experiment':20s}{1.61:8.3f}{2.63:8.3f}{3.08:8.3f}{146.10:10.2f}")
print("\n1피크 높이 g_max")
print(hdr[:44])
for lab, gp, _, _ in OURS:
    d = np.loadtxt(gp); r = d[:, 0]
    print(f"{lab:20s}" + "".join(
        f"{d[(r>p[0])&(r<p[1]), i+1].max():8.2f}" for i, (_n, _c, p, _y) in enumerate(panels)))
print(f"{'AIMD (digitized)':20s}" + "".join(
    f"{AI[(AI[:,0]>p[0])&(AI[:,0]<p[1]), i+1].max():8.2f}"
    for i, (_n, _c, p, _y) in enumerate(panels)))
