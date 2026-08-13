#!/usr/bin/env python
"""Fig. PDF — partial pair distribution functions of a-SiO2 at ρ = 2.20 g/cm³, 300 K.

BKS vs 7net-nano-4.5 (본 작업) vs AIMD PBE (Dechant JPCC 2026, 색분리 digitize).
공통 x축을 공유하는 3단 세로 배치. Si-O 는 1피크가 뾰족해 r=[1.5,1.8] inset 확대,
inset 안에만 **평균 결합길이**(색 점선)와 실험값(검정 파선)을 표기한다.
"""
import re
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
    "legend.fontsize": 9.5, "legend.handlelength": 1.5, "legend.frameon": True,
    "xtick.direction": "in", "ytick.direction": "in",
    "xtick.top": True, "ytick.right": True,
    "xtick.major.size": 5, "ytick.major.size": 5,
    "xtick.minor.size": 2.8, "ytick.minor.size": 2.8,
    "axes.linewidth": 0.9, "lines.linewidth": 1.4,
})
ALPHA = 0.8                      # 겹친 곡선 뒤가 비치도록

OURS = [("BKS", "02_run/s0_requench/bks220", "tab:blue"),
        ("7net-nano-4.5", "02_run/s3_md/7net220", "tab:red")]
AI = np.loadtxt(DAT / "dechant_pdf_digitized.dat")     # r, gSiO, gOO, gSiSi
AILAB = "AIMD PBE (Dechant 2026)"
EXP = {"Si-O": 1.61, "O-O": 2.63, "Si-Si": 3.08}       # Dechant Table 1, experimental
AIT = {"Si-O": 1.63, "O-O": 2.67, "Si-Si": 3.03}       # Dechant Table 1, AIMD

PAN = [("Si-O", 1, (1.3, 2.1), 41, "(a)"),
       ("O-O", 2, (2.1, 3.3), 7.5, "(b)"),
       ("Si-Si", 3, (2.4, 3.8), 7.5, "(c)")]
RLIM = (1.0, 8.0)
INS_YMAX = 40.0                  # inset 상단이 본 그림 축(41) 안에 들어오도록


def mean_sio(stem):
    """traj_analyze.py 가 남긴 *_stats.dat 에서 평균 Si-O 결합길이를 읽는다."""
    txt = (ROOT / f"{stem}_stats.dat").read_text()
    # ^ 고정 필수. 그냥 "Si-O" 로 찾으면 "O-Si-O mean 109.4" 줄에 먼저 걸린다.
    return float(re.search(r"^Si-O\s+mean\s+([\d.]+)", txt, re.M).group(1))


fig, ax = plt.subplots(3, 1, figsize=(5.6, 7.6), sharex=True,
                       gridspec_kw={"hspace": 0.06})

for k, (pair, col, pk, ymax, tag) in enumerate(PAN):
    a = ax[k]
    for lab, stem, c in OURS:
        d = np.loadtxt(ROOT / f"{stem}_gr.dat")
        a.plot(d[:, 0], d[:, k + 1], "-", c=c, alpha=ALPHA, label=lab)
    a.plot(AI[:, 0], AI[:, col], "-", c="tab:green", alpha=ALPHA, label=AILAB)
    a.set_xlim(*RLIM); a.set_ylim(0, ymax)
    a.set_ylabel(rf"$g_{{\rm {pair}}}(r)$")
    a.xaxis.set_minor_locator(AutoMinorLocator(2))
    a.yaxis.set_minor_locator(AutoMinorLocator(2))
    a.text(0.025, 0.88, tag, transform=a.transAxes, fontsize=11.5, fontweight="bold")
    a.text(0.115, 0.88, pair, transform=a.transAxes, fontsize=11.5)

    if pair != "Si-O":
        continue

    ins = a.inset_axes([0.46, 0.28, 0.50, 0.60])
    for lab, stem, c in OURS:
        d = np.loadtxt(ROOT / f"{stem}_gr.dat")
        ins.plot(d[:, 0], d[:, 1], "-", c=c, alpha=ALPHA)
        ins.axvline(mean_sio(stem), ls=":", lw=1.1, c=c, alpha=0.9)   # 평균 결합길이
    ins.plot(AI[:, 0], AI[:, 1], "-", c="tab:green", alpha=ALPHA)
    # AIMD 도 같은 정의(1차 배위껍질의 평균 거리)로 계산해 우리 값과 정합시킨다.
    # 논문 Table 1 의 1.63 은 peak/mean 구분이 명시돼 있지 않아 그대로 쓰면 정의가 섞인다.
    mm = (AI[:, 0] > pk[0]) & (AI[:, 0] < pk[1])
    w = AI[mm, 1] * AI[mm, 0] ** 2
    ai_mean = (AI[mm, 0] * w).sum() / w.sum()
    ins.axvline(ai_mean, ls=":", lw=1.1, c="tab:green", alpha=0.9)
    ins.axvline(EXP[pair], ls="--", lw=1.2, c="k")
    # 실험값 라벨은 점선 밀집 구간을 피해 오른쪽으로 빼고 가는 선으로 연결
    ins.annotate(f"exp {EXP[pair]:.2f}", xy=(EXP[pair], INS_YMAX * 0.50),
                 xytext=(1.530, INS_YMAX * 0.80), fontsize=8.5,
                 ha="center", va="center",
                 bbox=dict(fc="white", ec="none", alpha=0.5, pad=1.0),
                 arrowprops=dict(arrowstyle="-", lw=0.7, color="0.3",
                                 shrinkA=1, shrinkB=1))
    ins.set_xlim(1.50, 1.80); ins.set_ylim(0, INS_YMAX)
    ins.set_xticks([1.5, 1.6, 1.7, 1.8])
    ins.tick_params(labelsize=8, direction="in", top=True, right=True)
    ins.xaxis.set_minor_locator(AutoMinorLocator(2))
    ins.yaxis.set_minor_locator(AutoMinorLocator(2))
    a.indicate_inset_zoom(ins, edgecolor="0.45", lw=0.8, alpha=0.8)

ax[1].legend(loc="upper right", framealpha=0.92, borderpad=0.5)
ax[2].set_xlabel(r"$r$ ($\rm\AA$)")
ax[0].set_title(r"a-SiO$_2$,  $\rho$ = 2.20 g/cm$^3$,  300 K", fontsize=11, pad=8)

fig.tight_layout()
fig.savefig(FIG / "fig_pdf.png", dpi=300)
fig.savefig(FIG / "fig_pdf.pdf")
print(f"-> {FIG}/fig_pdf.png, .pdf\n")

# ---------------- 수치 표 ----------------
hdr = f"{'':20s}{'Si-O':>9s}{'O-O':>9s}{'Si-Si':>9s}"
print(hdr + "   1피크 위치 (Å)")
for lab, stem, _ in OURS:
    d = np.loadtxt(ROOT / f"{stem}_gr.dat"); r = d[:, 0]
    print(f"{lab:20s}" + "".join(
        f"{r[(r>p[0])&(r<p[1])][np.argmax(d[(r>p[0])&(r<p[1]), i+1])]:9.3f}"
        for i, (_n, _c, p, _y, _t) in enumerate(PAN)))
print(f"{'AIMD (digitized)':20s}" + "".join(
    f"{AI[(AI[:,0]>p[0])&(AI[:,0]<p[1]),0][np.argmax(AI[(AI[:,0]>p[0])&(AI[:,0]<p[1]), i+1])]:9.3f}"
    for i, (_n, _c, p, _y, _t) in enumerate(PAN)))
print(f"{'AIMD (Table 1)':20s}" + "".join(f"{AIT[p[0]]:9.3f}" for p in PAN))
print(f"{'experiment':20s}" + "".join(f"{EXP[p[0]]:9.3f}" for p in PAN))

print(f"\n{hdr}   1피크 높이 g_max")
for lab, stem, _ in OURS:
    d = np.loadtxt(ROOT / f"{stem}_gr.dat"); r = d[:, 0]
    print(f"{lab:20s}" + "".join(f"{d[(r>p[0])&(r<p[1]), i+1].max():9.2f}"
                                 for i, (_n, _c, p, _y, _t) in enumerate(PAN)))
print(f"{'AIMD (digitized)':20s}" + "".join(
    f"{AI[(AI[:,0]>p[0])&(AI[:,0]<p[1]), i+1].max():9.2f}"
    for i, (_n, _c, p, _y, _t) in enumerate(PAN)))

print("\n평균 Si-O 결합길이 (Å)  ← inset 세로 점선")
for lab, stem, _ in OURS:
    print(f"  {lab:20s}{mean_sio(stem):.4f}")
print(f"  {'AIMD (digitized)':20s}{ai_mean:.4f}")
print(f"  {'AIMD (Table 1)':20s}{AIT['Si-O']:.4f}  <- peak/mean 구분 없음")
print(f"  {'experiment':20s}{EXP['Si-O']:.4f}")
