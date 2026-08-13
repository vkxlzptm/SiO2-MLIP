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
from matplotlib.legend_handler import HandlerTuple

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
    # 해칭 색은 edgecolor 를 따라간다 (edgecolor 를 주면 rcParams["hatch.color"] 는 무시됨).
    # → 막대를 두 겹으로 그린다: 아래는 해칭용(edgecolor=빨강, 테두리 없음),
    #   위는 테두리용(면 없음, edgecolor=검정).
    "axes.linewidth": 0.9, "hatch.linewidth": 4,
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
# BKS 와 7net 의 ring 분포는 완전히 동일하므로 한 막대로 그리되,
# 파랑 바탕(BKS) + 빨강 사선(7net) 으로 **두 색이 번갈아 나오는 줄무늬**를 만들어
# "둘이 같은 값"임을 색으로 드러낸다. 다른 그림의 색 약속(BKS 파랑 / 7net 빨강)과 일치.
# AIMD 는 무늬 없이 초록 단색 → 대비가 충분해 별도 패턴이 필요 없다.
h_fill = ax.bar(nring - w / 2, frac, width=w, color="tab:blue", alpha=0.8,
                edgecolor="tab:red", lw=0.0, hatch="//")
h_edge = ax.bar(nring - w / 2, frac, width=w, facecolor="none", edgecolor="k", lw=0.7)
h_ai = ax.bar(nring + w / 2, ai, width=w, color="tab:green", alpha=0.8,
              edgecolor="k", lw=0.7)
ax.set_xlabel("Ring size  (number of Si)")
ax.set_ylabel("Fraction")
ax.set_xticks(nring); ax.set_xlim(1.4, 9.6); ax.set_ylim(0, 0.4)
ax.yaxis.set_minor_locator(AutoMinorLocator(2))
# 막대를 두 겹으로 그리므로 범례 스와치도 두 겹으로 겹쳐 그린다.
# HandlerTuple 의 ndivide 는 스와치를 몇 칸으로 나눌지다.
# None = 튜플 길이만큼 나눠 **나란히** 그림 → 원하는 건 ndivide=1 (한 칸에 포개기).
ax.legend([(h_fill, h_edge), h_ai],
          ["This work \n(BKS = 7net-nano-4.5)",
           "AIMD PBE \n(Dechant 2026, 120 atoms)"],
          handler_map={tuple: HandlerTuple(ndivide=1)},
          loc="upper left", framealpha=0.9, fontsize=8.5, frameon=False)
ax.set_title("Ring size distribution  (King criterion)", fontsize=11)
fig.tight_layout()
fig.savefig(FIG / "fig_rings.png", dpi=300)
print(f"-> {FIG}/fig_rings.png\n")

print(f"{'n':>3s}{'This work':>12s}{'AIMD (dig.)':>13s}")
for i, n in enumerate(nring):
    print(f"{n:3d}{100*frac[i]:11.2f}%{100*ai[i]:12.2f}%")
mo = (nring * frac).sum() / frac.sum()
ma = (nring * ai).sum() / ai.sum()
print(f"\n평균 고리 크기: this work {mo:.2f},  AIMD {ma:.2f}")
