#!/usr/bin/env python
"""Fig. speed — CPU 처리량과 병렬 확장성 (i5-11600K 6c12t, GPU 없음).

(a) 처리량: BKS vs 7net-nano cutoff 4종. 로그 축.
(b) 병렬 확장성: OMP 스레드 / 독립 프로세스(리플리카) 둘 다 조기 포화.
    → 이 워크로드는 연산이 아니라 **메모리 대역폭**에 묶여 있다.

전부 2160원자 실측. 출처는 02_run/s1_sanity/NOTE.md 와 각 런의 LAMMPS Loop time.
"""
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator

ROOT = Path(__file__).resolve().parents[2]
FIG = ROOT / "04_analysis/fig"; FIG.mkdir(exist_ok=True)

plt.rcParams.update({
    "font.size": 10, "axes.labelsize": 11, "xtick.labelsize": 10, "ytick.labelsize": 10,
    "legend.fontsize": 9, "legend.handlelength": 1.5,
    "xtick.direction": "in", "ytick.direction": "in",
    "xtick.top": True, "ytick.right": True,
    "xtick.major.size": 5, "ytick.major.size": 5,
    "xtick.minor.size": 2.8, "ytick.minor.size": 2.8,
    "axes.linewidth": 0.9, "lines.linewidth": 1.4,
})

# ---- (a) 처리량 (atom-step/s) ----
#  BKS 는 6랭크×1스레드, 7net 은 1랭크×6스레드 (e3gnn 은 2랭크 이상에서 크래시)
BKS_220 = 1.347e6      # ρ=2.20, in.bks_traj 생산 3000 step
BKS_261 = 1.204e6      # ρ=2.607, in.timing_bks 생산 200 step
NANO_261 = {4.5: 899.5, 5.0: 651.9, 5.5: 489.0, 6.0: 384.2}   # cutoff 스윕 @ρ=2.607
NANO_220 = 1082.8      # 4.5 @ρ=2.20, S3 생산 3000 step (1.995 s/step)

# ---- (b) 병렬 확장성 (각 계열의 n=1 대비 배수) ----
THREADS = ([1, 4, 6, 12], np.array([266.7, 479.2, 488.5, 489.1]))      # 5.5 @2.607
REPLICA = ([1, 2, 4, 6], np.array([509.4, 804.9, 960.3, 1007.3]))      # 4.5 @2.607, 총 처리량

fig, ax = plt.subplots(1, 2, figsize=(7.8, 3.4))

# ================= (a) =================
a = ax[0]
xs = np.arange(6)
vals = [BKS_220, BKS_261] + [NANO_261[c] for c in (6.0, 5.5, 5.0, 4.5)]
cols = ["tab:blue", "0.6", "0.75", "0.65", "0.5", "tab:red"]
labs = [r"BKS" + "\n" + r"$\rho$2.20", r"BKS" + "\n" + r"$\rho$2.61",
        "6.0", "5.5", "5.0", "4.5"]
a.bar(xs, vals, color=cols, width=0.68, edgecolor="k", lw=0.6)
a.plot([5], [NANO_220], "o", ms=7, mfc="w", mec="tab:red", mew=1.6, zorder=5)
a.set_yscale("log"); a.set_ylim(2e2, 4e6)
a.set_xticks(xs); a.set_xticklabels(labs, fontsize=8.5)
a.set_ylabel("throughput (atom-step / s)")
a.set_xlabel(r"BKS        7net-nano  cutoff ($\rm\AA$)")
a.text(0.035, 0.91, "(a)", transform=a.transAxes, fontsize=11.5, fontweight="bold")
# 배수 화살표 + 양 끝 높이를 가로 점선으로 연결해 어느 값끼리 비교하는지 명시
a.hlines(BKS_220, 0, 5.35, ls=":", lw=0.9, color="0.35", zorder=1)
a.hlines(NANO_220, 4.65, 5.35, ls=":", lw=0.9, color="0.35", zorder=1)
a.annotate("", xy=(5, NANO_220), xytext=(5, BKS_220),
           arrowprops=dict(arrowstyle="<->", lw=1.0, color="0.25"))
a.text(4.90, np.sqrt(NANO_220 * BKS_220)/2, f"×{BKS_220/NANO_220:,.0f}",
       fontsize=10, ha="right", va="center",
       bbox=dict(fc="white", ec="none", alpha=0.75, pad=1.0))
a.plot([1.7], [7e4*3], "o", ms=7, mfc="w", mec="tab:red", mew=1.6, clip_on=False)
a.text(1.85, 7e4*3, r"7net-nano-4.5 @ $\rho$2.20", fontsize=8.5, va="center")
a.text(1.7, 2e4*3, r"bars: @ $\rho$2.607" + "\n" + r"(cutoff sweep)",
       fontsize=8.5, va="center")

# ================= (b) =================
b = ax[1]
n = np.arange(1, 13)
b.plot(n, n, "-", lw=0.9, c="0.6", label="ideal")
b.plot(THREADS[0], THREADS[1] / THREADS[1][0], "s-", ms=5.5, c="tab:red",
       mfc="w", mew=1.3, label="OMP threads (1 process)")
b.plot(REPLICA[0], REPLICA[1] / REPLICA[1][0], "^-", ms=6, c="tab:purple",
       mfc="w", mew=1.3, label="independent processes")
b.axvline(6, ls=":", lw=1.0, c="0.5")
b.text(5.85, 6.9, "6 physical\ncores", fontsize=8, c="0.35", va="top", ha="right")
b.set_xlim(0.5, 12.5); b.set_ylim(0, 7.2)
b.set_xlabel("number of threads / processes"); b.set_ylabel("speedup")
b.set_xticks([1, 2, 4, 6, 8, 10, 12])
b.legend(loc="center right", framealpha=0.9)
b.text(0.035, 0.91, "(b)", transform=b.transAxes, fontsize=11.5, fontweight="bold")

for a_ in ax:
    a_.xaxis.set_minor_locator(AutoMinorLocator(2))
ax[1].yaxis.set_minor_locator(AutoMinorLocator(2))

# suptitle 과 axes 간격: rect 상단(=axes 가 쓸 수 있는 최대 높이)과 y 를 가깝게 두면 붙는다.
fig.suptitle("2160-atom a-SiO$_2$,  i5-11600K (6c12t), no GPU", fontsize=10.5, y=1)
fig.tight_layout(rect=[0, 0, 1, 1.05])
fig.savefig(FIG / "fig_speed.png", dpi=300)
print(f"-> {FIG}/fig_speed.png\n")

print("처리량 (atom-step/s)")
print(f"  BKS      ρ=2.20   {BKS_220:>12,.0f}   (6 ranks)")
print(f"  BKS      ρ=2.607  {BKS_261:>12,.0f}   (6 ranks)")
for c in (6.0, 5.5, 5.0, 4.5):
    print(f"  7net {c}  ρ=2.607  {NANO_261[c]:>12,.1f}   (1 rank x 6 threads)")
print(f"  7net 4.5  ρ=2.20   {NANO_220:>12,.1f}")
print(f"\n생산 조건 배수 (둘 다 ρ=2.20): BKS / 7net-nano-4.5 = {BKS_220/NANO_220:,.0f}x")
print(f"초기 조건 배수 (ρ=2.607, cutoff 5.5): {BKS_261/NANO_261[5.5]:,.0f}x")
print(f"\n병렬 확장: 스레드 1->12 {THREADS[1][-1]/THREADS[1][0]:.2f}x, "
      f"프로세스 1->6 {REPLICA[1][-1]/REPLICA[1][0]:.2f}x  (ideal 12x / 6x)")
