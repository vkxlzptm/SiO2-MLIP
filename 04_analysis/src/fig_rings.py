#!/usr/bin/env python
"""Fig. rings — ring size 분포 (King 기준).

우리 구조(BKS 가 만든 망)와 Dechant JPCC 2026 Fig. S4(a) 의 LES 분포를 비교한다.
SevenNet 이완은 위상을 바꾸지 못하므로 BKS 와 7net 의 ring 분포는 **완전히 동일**하다
(ring_stats.py 로 확인). 그래서 여기 비교는 "우리 망 vs AIMD 망"이다.

⚠ ring 통계는 정의(King / Guttman / primitive)에 따라 달라진다. 논문이 어떤 기준을
   썼는지 명시하지 않았으므로 **정성 비교**로만 읽을 것.
⚠ 논문 계는 120원자(Si 40개, L=12.2 Å)라 큰 고리가 물리적으로 들어가기 어렵다.
   8-ring 이상이 없는 것은 유한크기 효과일 가능성이 크다.
"""
from pathlib import Path

import numpy as np
from PIL import Image
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator

ROOT = Path(__file__).resolve().parents[2]
DAT, FIG = ROOT / "04_analysis/dat", ROOT / "04_analysis/fig"
FIG.mkdir(exist_ok=True)

plt.rcParams.update({
    "font.size": 10, "axes.labelsize": 11, "xtick.labelsize": 10, "ytick.labelsize": 10,
    "legend.fontsize": 9, "legend.handlelength": 1.5,
    "xtick.direction": "in", "ytick.direction": "in",
    "xtick.top": True, "ytick.right": True,
    "xtick.major.size": 5, "ytick.major.size": 5,
    "xtick.minor.size": 2.8, "ytick.minor.size": 2.8,
    "axes.linewidth": 0.9,
})

# ---------- Dechant Fig. S4(a) LES digitize ----------
im = np.array(Image.open(ROOT / "05_doc/dechant_figs/SI_p4_img1.jpeg").convert("RGB")).astype(int)
sub = im[:, : im.shape[1] // 2]
r_, g_, b_ = sub[:, :, 0], sub[:, :, 1], sub[:, :, 2]
black = (r_ < 110) & (g_ < 110) & (b_ < 110)
rs = black.sum(1)
rows = np.where(rs > 0.5 * rs.max())[0]
r0, r1 = rows.min(), rows.max()
ccols = np.where(black[r1])[0]
c0, c1 = ccols.min(), ccols.max()
green = (g_ > 90) & (g_ > r_ + 35) & (g_ > b_ + 35)

XMIN, XMAX = 0.0, 10.0                       # x축 라벨 0~10
to_x = lambda c: XMIN + (c - c0) / (c1 - c0) * (XMAX - XMIN)
xs, ys = [], []
for c in range(c0, c1 + 1):
    rr = np.where(green[:, c])[0]
    rr = rr[(rr > r0) & (rr < r1)]
    if len(rr) == 0:
        continue
    cl, cu = [], [rr[0]]
    for x in rr[1:]:
        (cu.append(x) if x - cu[-1] <= 6 else (cl.append(list(cu)), cu.clear(), cu.append(x)))
    cl.append(list(cu))
    xs.append(to_x(c)); ys.append(r1 - float(np.mean(cl[-1])))   # 범례를 피해 아래 군집
xs, ys = np.array(xs), np.array(ys)

nring = np.arange(2, 10)
ai = np.clip(np.interp(nring, xs, ys, left=0, right=0), 0, None)
ai = ai / ai.sum()

# ---------- 우리 구조 ----------
ours = np.loadtxt(DAT / "BKS220_rings.dat")          # n, count, fraction
frac = np.zeros_like(nring, dtype=float)
for n, _c, f in ours:
    if 2 <= n <= 9:
        frac[int(n) - 2] = f

# ---------- 그림 ----------
fig, ax = plt.subplots(figsize=(5.0, 3.5))
w = 0.38
ax.bar(nring - w / 2, frac, width=w, color="tab:red", alpha=0.85, edgecolor="k", lw=0.6,
       label="this work  (BKS network,\n identical after 7net relaxation)")
ax.bar(nring + w / 2, ai, width=w, color="tab:green", alpha=0.85, edgecolor="k", lw=0.6,
       label="AIMD PBE (Dechant 2026,\n digitized, 120 atoms)")
ax.set_xlabel("ring size  (number of Si)")
ax.set_ylabel("fraction")
ax.set_xticks(nring); ax.set_xlim(1.4, 9.6)
ax.yaxis.set_minor_locator(AutoMinorLocator(2))
ax.legend(loc="upper right", framealpha=0.9, fontsize=8)
ax.set_title("Ring size distribution  (King criterion)", fontsize=11)
fig.tight_layout()
fig.savefig(FIG / "fig_rings.png", dpi=300)
fig.savefig(FIG / "fig_rings.pdf")
print(f"-> {FIG}/fig_rings.png, .pdf\n")

print(f"{'n':>3s}{'this work':>12s}{'AIMD (dig.)':>13s}")
for i, n in enumerate(nring):
    print(f"{n:3d}{100*frac[i]:11.2f}%{100*ai[i]:12.2f}%")
mo = (nring * frac).sum() / frac.sum()
ma = (nring * ai).sum() / ai.sum()
print(f"\n평균 고리 크기: this work {mo:.2f},  AIMD {ma:.2f}")
