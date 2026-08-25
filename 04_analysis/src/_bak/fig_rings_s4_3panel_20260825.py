#!/usr/bin/env python
"""Fig. S4 rings — 7net 이 '스스로 만든' 망 위상 vs BKS 가 만든 망 위상.

★ fig_rings.py 와 혼동하지 말 것.
  fig_rings.py = BKS 가 만든 망을 7net 이 **물려받아 이완만** 한 경우
                 (ring 분포가 비트 단위로 동일 -> "위상은 이완으로 안 바뀐다"의 증거).
  이 그림      = 7net 이 **자기 힘으로 melt-quench** 해서 만든 망.
                 두 그림의 차이가 이 프로젝트가 처음 재는 양, 곧 **위상 형성 효과**다.

비교 설계:
  - 냉각률을 맞춘 짝(7net 2e13 vs BKS 2e13)이 1차 비교. 초기 액체·셀·앙상블·통계길이 동일.
  - BKS 를 5e12 / 2e13 / 5e13 로 돌린 세 런은 **같은 시드(90210)·같은 4000 K 액체**에서
    갈라져 나온 것이라 서로 독립 표본이 아니다. 이 셋의 폭은 '냉각률 효과'지 통계 산포가 아니다.
  - 그래서 s0_requench 의 BKS 220 런(seed 77213, 4000 K 200 ps 용융, 5e12 K/s)을 함께 넣는다.
    S4 BKS_5e12 와 **같은 냉각률·다른 실현**이므로 BKS 의 실현간 산포를 재는 유일한 자료다.
    ★ 그리고 이 구조가 바로 기존 실험에서 7net 이 물려받았던 망이다 (패널 c 주석).

오차 처리 (두 종류를 구분해서 보인다):
  - 계수오차: distinct ring 개수의 Poisson (count/n 개). 3-ring 은 56개(7net)/23개(BKS) 수준.
  - 실현간 산포: BKS 5e12 두 실현(1.80 % vs 3.07 %)에서 추정. 계수오차와 같은 자릿수.
  7net 은 시드 1개뿐이라(117 h/런) 자체 오차막대를 그릴 수 없다 — 이 한계를 그림에 명시한다.

강건성: 결합 판정 RCUT 을 1.85~2.15 A 로 스윕해도 3-ring 순위가 뒤집히지 않는다
        (ring_robust_s4.py -> S4_rings_robust.dat). 즉 7net-BKS 결합길이 차이
        (1.635 vs 1.605 A)로 생긴 cutoff 아티팩트가 아니다.

입력: 04_analysis/dat/S4_*_rings.dat, dat/BKS220_rings.dat
출력: 04_analysis/fig/fig_rings_s4.png, dat/S4_rings_summary.dat
"""
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.ticker import AutoMinorLocator

ROOT = Path(__file__).resolve().parents[2]
DAT, FIG = ROOT / "04_analysis/dat", ROOT / "04_analysis/fig"
FIG.mkdir(exist_ok=True); DAT.mkdir(exist_ok=True)

plt.rcParams.update({
    "font.size": 10, "axes.labelsize": 11, "xtick.labelsize": 10, "ytick.labelsize": 10,
    "legend.fontsize": 8.5, "legend.handlelength": 1.5,
    "xtick.direction": "in", "ytick.direction": "in",
    "xtick.top": True, "ytick.right": True,
    "xtick.major.size": 5, "ytick.major.size": 5,
    "xtick.minor.size": 2.8, "ytick.minor.size": 2.8,
    "axes.linewidth": 0.9, "lines.linewidth": 1.4,
})

NET_COL = "#D7292A"
BKS_COL = "#267BB6"
NET_LABEL = "7net-Nano-4.5"
NS = np.arange(3, 10)

try:
    BKS_CMAP = matplotlib.colormaps["Blues"]
except AttributeError:
    import matplotlib.cm as _cm
    BKS_CMAP = _cm.get_cmap("Blues")


def load_rings(path, col_distinct=True):
    """S4_*_rings.dat: n count f_triplet f_distinct.
    BKS220_rings.dat 는 구판이라 (n count fraction=triplet) 3열뿐 -> distinct 를 재계산."""
    d = np.loadtxt(path)
    n, cnt = d[:, 0].astype(int), d[:, 1]
    if d.shape[1] >= 4 and col_distinct:
        f = d[:, 3]
    else:
        f = cnt / n
        f = f / f.sum()
    out_f, out_c = np.zeros(len(NS)), np.zeros(len(NS))
    for i, nn in enumerate(NS):
        m = n == nn
        if m.any():
            out_f[i], out_c[i] = f[m][0], cnt[m][0]
    return out_f, out_c


RUNS = [
    dict(tag="7net",      file="S4_7net_rings.dat",     rate=2.0e13, fam="7net",
         label=f"{NET_LABEL} (self-quenched)"),
    dict(tag="BKS 2e13",  file="S4_BKS_2e13_rings.dat", rate=2.0e13, fam="BKS",
         label="BKS 2e13 K/s  (matched pair)"),
    dict(tag="BKS 5e12",  file="S4_BKS_5e12_rings.dat", rate=5.0e12, fam="BKS",
         label="BKS 5e12 K/s"),
    dict(tag="BKS 5e13",  file="S4_BKS_5e13_rings.dat", rate=5.0e13, fam="BKS",
         label="BKS 5e13 K/s"),
    dict(tag="BKS 5e12*", file="BKS220_rings.dat",      rate=5.0e12, fam="BKS",
         label="BKS 5e12 K/s, indep. seed (s0)"),
]

for r in RUNS:
    r["f"], r["cnt"] = load_rings(DAT / r["file"])
    ndist = np.maximum(r["cnt"] / NS, 1e-9)          # distinct ring 개수
    r["sig"] = r["f"] / np.sqrt(ndist)               # Poisson 상대오차 -> 절대 %p
    r["ndist"] = ndist

net = RUNS[0]
bks = RUNS[1:]
B = np.array([r["f"] for r in bks])                  # (4, 7)
b_mean, b_lo, b_hi = B.mean(0), B.min(0), B.max(0)
# BKS 실현간 산포: 같은 5e12 의 두 실현 차이 / sqrt(2) 를 1 sigma 로 본다 (n=2, 보수적)
b_real = np.abs(RUNS[2]["f"] - RUNS[4]["f"]) / np.sqrt(2)
b_count = np.array([r["sig"] for r in bks]).mean(0)
b_tot = np.sqrt(b_real**2 + b_count**2)
d_tot = np.sqrt(net["sig"]**2 + b_tot**2)            # 7net - BKS 차의 총 불확도

# ------------------------------------------------------------------ figure
fig, ax = plt.subplots(1, 3, figsize=(11.0, 3.5))
a, b, c = ax

# ---------------- (a) 분포 ----------------
w = 0.38
a.bar(NS - w / 2, net["f"], width=w, color=NET_COL, alpha=0.85,
      edgecolor="k", lw=0.7, zorder=2,
      yerr=net["sig"], error_kw=dict(lw=0.9, capsize=2.2, ecolor="0.2"))
a.bar(NS + w / 2, b_mean, width=w, color=BKS_COL, alpha=0.85,
      edgecolor="k", lw=0.7, zorder=2,
      yerr=[b_mean - b_lo, b_hi - b_mean],
      error_kw=dict(lw=0.9, capsize=2.2, ecolor="0.2"))
a.set_xlabel("Ring size  (number of Si)")
a.set_ylabel("Fraction  (distinct rings)")
a.set_xticks(NS); a.set_xlim(2.4, 9.6); a.set_ylim(0, 0.44)
a.yaxis.set_minor_locator(AutoMinorLocator(2))
a.plot([], [], "s", c=NET_COL, ms=8, mec="k", mew=0.7, label=f"{NET_LABEL}, self-quenched")
a.plot([], [], "s", c=BKS_COL, ms=8, mec="k", mew=0.7, label="BKS, 4 runs (bar = mean,\n bar cap = full range)")
a.legend(loc="upper right", frameon=False, fontsize=7.8,
         bbox_to_anchor=(1.005, 0.965))
a.set_title("Ring size distribution  (King)", fontsize=10.5)
a.text(0.035, 0.965, "(a)", transform=a.transAxes, fontsize=11.5,
       fontweight="bold", ha="left", va="top")

# ---------------- (b) 차이 ----------------
diff = 100 * (net["f"] - b_mean)
err = 100 * d_tot
cols = [NET_COL if d > 0 else BKS_COL for d in diff]
b.bar(NS, diff, width=0.6, color=cols, alpha=0.85, edgecolor="k", lw=0.7, zorder=2,
      yerr=err, error_kw=dict(lw=0.9, capsize=2.6, ecolor="0.2"))
b.axhline(0, ls="-", lw=0.8, c="0.35", zorder=1)
b.set_xlabel("Ring size  (number of Si)")
b.set_ylabel("7net $-$ BKS  (%p)")
b.set_xticks(NS); b.set_xlim(2.4, 9.6)
b.yaxis.set_minor_locator(AutoMinorLocator(2))
b.set_title("Topology-formation effect", fontsize=10.5)
b.text(0.035, 0.965, "(b)", transform=b.transAxes, fontsize=11.5,
       fontweight="bold", ha="left", va="top")
# sigma 라벨은 0선 바로 안쪽(막대 위)에 흰 글씨로 — 오차막대·주석과 겹치지 않는다
for i, nn in enumerate(NS):
    if abs(diff[i]) > 2.0 * err[i]:
        b.text(nn, np.sign(diff[i]) * 0.55, f"{abs(diff[i])/err[i]:.1f}$\\sigma$",
               ha="center", va="bottom" if diff[i] > 0 else "top",
               fontsize=7.8, color="w", fontweight="bold", zorder=4)
b.text(0.97, 0.955,
       "error = Poisson $\\oplus$ BKS run-to-run\n(7net: 1 seed, no own error bar)",
       transform=b.transAxes, fontsize=7.2, color="0.35", va="top", ha="right")
b.margins(y=0.22)

# ---------------- (c) 3-ring vs 냉각률 ----------------
rates = sorted({r["rate"] for r in bks})
norm = Normalize(vmin=np.log10(min(rates)), vmax=np.log10(max(rates)))
cmap = {r: BKS_CMAP(0.35 + 0.55 * norm(np.log10(r))) for r in rates}

c.axhspan(100 * b_lo[0], 100 * b_hi[0], color=BKS_COL, alpha=0.13, zorder=0)
for r in bks:
    mk = "s" if r["tag"].endswith("*") else "o"
    c.errorbar(r["rate"], 100 * r["f"][0], yerr=100 * r["sig"][0], fmt=mk, ms=8.5,
               mfc=cmap[r["rate"]], mec="0.25", mew=0.9, ecolor="0.45",
               elinewidth=0.9, capsize=2.6, zorder=3)
c.errorbar(net["rate"], 100 * net["f"][0], yerr=100 * net["sig"][0], fmt="*", ms=17,
           mfc=NET_COL, mec=NET_COL, ecolor=NET_COL, elinewidth=1.0, capsize=2.6, zorder=4)
c.set_xscale("log")
c.set_xlabel("Quench rate (K/s)")
c.set_ylabel("3-ring fraction (%)")
c.set_ylim(0, 9.2)
c.set_xlim(3.0e12, 1.3e14)
c.yaxis.set_minor_locator(AutoMinorLocator(2))
c.annotate("the topology 7net\ninherited earlier\n(fig_rings.png)",
           xy=(5.0e12, 100 * RUNS[4]["f"][0]), xytext=(0.05, 0.80),
           textcoords=c.transAxes, fontsize=7.0, color="0.30", ha="left", va="top",
           arrowprops=dict(arrowstyle="-|>", lw=0.8, color="0.45",
                           connectionstyle="arc3,rad=-0.3", shrinkB=6))
c.plot([], [], "*", c=NET_COL, ms=13, label=f"{NET_LABEL} (2e13 K/s)")
c.plot([], [], "o", mfc=BKS_COL, mec="0.25", ms=8, label="BKS, S4 controls (seed 90210)")
c.plot([], [], "s", mfc=BKS_COL, mec="0.25", ms=8, label="BKS, s0 run (seed 77213)")
c.legend(loc="lower right", frameon=False, fontsize=7.2,
         handletextpad=0.5, borderaxespad=0.3)
c.set_title("3-ring excess is not a rate effect", fontsize=10.5)
c.text(0.035, 0.965, "(c)", transform=c.transAxes, fontsize=11.5,
       fontweight="bold", ha="left", va="top")

fig.tight_layout()
fig.savefig(FIG / "fig_rings_s4.png", dpi=300)
print(f"-> {FIG}/fig_rings_s4.png")

# ------------------------------------------------------------------ summary
with open(DAT / "S4_rings_summary.dat", "w") as f:
    hdr = (f"{'n':>3}{'7net%':>9}{'BKSmean%':>10}{'BKSmin%':>9}{'BKSmax%':>9}"
           f"{'diff%p':>9}{'err%p':>8}{'sigma':>7}\n")
    f.write("# King ring, distinct fraction. BKS = 4 runs (5e12 x2 seeds, 2e13, 5e13)\n")
    f.write("# err = Poisson(7net) (+) Poisson(BKS) (+) BKS run-to-run scatter\n")
    f.write("# " + hdr)
    print("\n" + hdr, end="")
    for i, nn in enumerate(NS):
        line = (f"{nn:>3d}{100*net['f'][i]:>9.2f}{100*b_mean[i]:>10.2f}"
                f"{100*b_lo[i]:>9.2f}{100*b_hi[i]:>9.2f}{diff[i]:>9.2f}"
                f"{err[i]:>8.2f}{abs(diff[i])/err[i]:>7.1f}\n")
        f.write(line); print(line, end="")
    mn = lambda fr: float((NS * fr).sum())
    tail = (f"\n# mean ring size (distinct):  7net {mn(net['f']):.3f}   "
            + "  ".join(f"{r['tag']} {mn(r['f']):.3f}" for r in bks) + "\n")
    f.write(tail); print(tail, end="")
print(f"-> {DAT}/S4_rings_summary.dat")
