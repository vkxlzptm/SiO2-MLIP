#!/usr/bin/env python
"""Fig. BAD — bond angle distributions of a-SiO2 at ρ = 2.20 g/cm³, 300 K.

(a) O-Si-O  : 사면체 내부 각. 세 방법 모두 실험 109.4° 근처로 포개진다 → 변별력 없음.
(b) Si-O-Si : 사면체 사이 각. 여기서 방법 간 차이가 드러난다.

두 각의 범위가 달라 x축은 공유하지 않고, 첨도 차이가 커(≈2.5배) y축도 공유하지 않는다.
AIMD 는 Dechant JPCC 2026 Fig. 4 의 **LES-quenched** 곡선을 색분리 digitize 한 것.
(digitize 검증: 평균 O-Si-O 109.47° / Si-O-Si 138.65° vs 논문 Table 1 의 109.4 / 138.5)
"""
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator

ROOT = Path(__file__).resolve().parents[2]
DAT, FIG = ROOT / "04_analysis/dat", ROOT / "04_analysis/fig"
FIG.mkdir(exist_ok=True)

plt.rcParams.update({
    "font.size": 10, "axes.labelsize": 11, "xtick.labelsize": 10, "ytick.labelsize": 10,
    "legend.fontsize": 9, "legend.handlelength": 1.5, "legend.frameon": True,
    "xtick.direction": "in", "ytick.direction": "in",
    "xtick.top": True, "ytick.right": True,
    "xtick.major.size": 5, "ytick.major.size": 5,
    "xtick.minor.size": 2.8, "ytick.minor.size": 2.8,
    "axes.linewidth": 0.9, "lines.linewidth": 1.4,
})
ALPHA = 0.8

OURS = [("BKS", "02_run/s0_requench/bks220_angles.dat", "tab:blue"),
        ("7Net-nano-4.5", "02_run/s3_md/7net220_angles.dat", "tab:red")]
        #("SevenNet-nano-4.5", "02_run/s3_md/7net220_angles.dat", "tab:red")]
AI = np.loadtxt(DAT / "dechant_bad_digitized.dat")   # angle, OSiO_LES, OSiO_HES, SiOSi_LES, SiOSi_HES
AILAB = "AIMD PBE\n(Dechant 2026)"
#AILAB = "AIMD PBE (Dechant 2026)"

#  (패널명, 우리 파일 열, AIMD 열, x범위, 실험 표기, 태그)
#   실험값 출처 = Dechant JPCC 2026 Table 1 (experimental 열)
#   실험은 둘 다 **범위**로 보고돼 있으므로 음영 밴드로 통일한다.
#   O-Si-O 의 109.4-109.7 은 폭이 0.3° 뿐이라 축 위에서는 가는 띠로 보인다 (사실 그대로).
PAN = [("O-Si-O", 2, 1, (85, 135), ((109.4, 109.7), "exp\n109.4-109.7"), "(a)"),
       # xlim 하한을 102 로 (100 이면 x축 첫 라벨이 y축 첫 라벨과 겹친다).
       # 세 곡선 모두 105° 아래에서는 사실상 0 이라 잘리는 정보 없음.
       ("Si-O-Si", 1, 3, (104, 180), ((140.0, 150.0), "exp 140-150"), "(b)")]

fig, ax = plt.subplots(1, 2, figsize=(7.8, 3.4))

rows = []
for k, (name, ocol, acol, xlim, expspec, tag) in enumerate(PAN):
    a = ax[k]
    val, elab = expspec
    a.axvspan(val[0], val[1], color="0.45", alpha=0.20, lw=0, zorder=0)

    ent = []
    for lab, fn, c in OURS:
        d = np.loadtxt(ROOT / fn)
        a.plot(d[:, 0], d[:, ocol], "-", c=c, alpha=ALPHA, label=lab)
        m = (d[:, 0] * d[:, ocol]).sum() / d[:, ocol].sum()
        sd = np.sqrt((d[:, ocol] * (d[:, 0] - m) ** 2).sum() / d[:, ocol].sum())
        a.axvline(m, ls=":", lw=1.1, c=c, alpha=0.9)
        ent.append((lab, m, sd))
    a.plot(AI[:, 0], AI[:, acol], "-", c="tab:green", alpha=ALPHA, label=AILAB)
    mA = np.trapezoid(AI[:, 0] * AI[:, acol], AI[:, 0])
    sA = np.sqrt(np.trapezoid(AI[:, acol] * (AI[:, 0] - mA) ** 2, AI[:, 0]))
    a.axvline(mA, ls=":", lw=1.1, c="tab:green", alpha=0.9)
    ent.append(("AIMD PBE", mA, sA))
    rows.append((name, ent))

    ymax = max(np.loadtxt(ROOT / OURS[0][1])[:, ocol].max(),
               np.loadtxt(ROOT / OURS[1][1])[:, ocol].max(), AI[:, acol].max())
    # (a) 에 범례를 두므로 위쪽 여백을 넉넉히 (곡선이 가려지지 않게)
    a.set_xlim(*xlim); a.set_ylim(0, ymax * (1.55 if name == "O-Si-O" else 1.15))
    a.set_xlabel(f"{name} angle (deg)")
    a.set_ylabel(r"$P(\theta)$  (deg$^{-1}$)")
    a.xaxis.set_minor_locator(AutoMinorLocator(2))
    a.yaxis.set_minor_locator(AutoMinorLocator(2))
    a.text(0.03, 0.92, tag, transform=a.transAxes, fontsize=11.5, fontweight="bold")
    a.text(0.145, 0.92, name, transform=a.transAxes, fontsize=11.5)

    # 실험 라벨
    xa = 0.5 * (val[0] + val[1])
    xtx = xlim[0] + (0.44 if name == "O-Si-O" else 0.74) * (xlim[1] - xlim[0])
    a.annotate(elab, xy=(xa, ymax * 0.02), xytext=(xtx, ymax * (0.22 if name == "O-Si-O" else 0.15)),
               fontsize=8.5, ha="center", va="center",
               bbox=dict(fc="white", ec="none", alpha=0.5, pad=1.0),
               arrowprops=dict(arrowstyle="-", lw=0.7, color="0.3", shrinkA=1, shrinkB=1))

ax[0].legend(loc="upper right", framealpha=0.82, borderpad=0.5)
fig.suptitle(r"a-SiO$_2$,  $\rho$ = 2.20 g/cm$^3$,  300 K   "
             r"(dotted: mean;  shaded: experimental range)", fontsize=10.5, y=0.94)
fig.tight_layout(rect=[0, 0, 1, 1])
fig.savefig(FIG / "fig_bad.png", dpi=300)
fig.savefig(FIG / "fig_bad.pdf")
print(f"-> {FIG}/fig_bad.png, .pdf\n")

for name, ent in rows:
    print(f"[{name}]{'평균':>10s}{'표준편차':>12s}")
    for lab, m, sd in ent:
        print(f"   {lab:22s}{m:8.2f}{sd:10.2f}")
print("\n실험 (Dechant Table 1):  O-Si-O 109.4-109.7,  Si-O-Si 140-150")
