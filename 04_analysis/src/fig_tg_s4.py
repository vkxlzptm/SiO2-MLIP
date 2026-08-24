#!/usr/bin/env python
"""Fig. S4 quench Tg — BKS vs 7net, 냉각률 의존성을 한 그림에.

quench220_fit.py(BKS ρ=2.20 단일 냉각률)의 후속. S4에서 냉각률을 바꿔가며
BKS 통제런 3종 + 7net 본런 1종을 같이 돌렸으므로, 이제 "포텐셜 차이"와
"냉각률 차이"를 한 축에 놓고 비교할 수 있다.

Tg 추정 두 가지 (mq7net_profile.dat 형식: T epa(eV/atom) P(bar) MSD(A^2)):
  (1) kinetic arrest — ΔMSD/100K 가 잡음 수준 아래로 떨어지는 T. **1차 지표.**
      물리적으로 가장 직접적이다(구조 완화가 관측시간을 못 따라가는 지점 = 유리전이
      그 자체). 냉각률에 단조 반응해야 하며 실제로 BKS 3종이 그렇다.
  (2) caloric Tg — epa(T) 액체/유리 두 직선의 교점. quench220_fit.py 는 고정폭
      (T>3000 / T<1500) 창을 썼는데, 냉각률마다 실제 전이온도가 다른 채로 같은
      고정창을 쓰면 액체/유리 가지에 전이구간이 섞여 들어가 비단조 결과가 났다
      (BKS 5e12/2e13/5e13 → 2801/2776/2305 K, 냉각률과 무관하게 흔들림).
      → 이 스크립트는 **kinetic arrest를 기준으로 창을 재배치**한다
        (arrest+400K 이상 = 액체 가지, arrest-400K 이하 = 유리 가지).
        모든 후보 온도에서 실제로 액체/유리 상태에 있다고 볼 수 있는 점만 쓰는 것.

입력: 02_run/s4_mq7net/profiles/{mq7net,mqbks_*}_profile.dat
출력: 04_analysis/fig/fig_tg_s4.png, 04_analysis/dat/tg_s4_summary.dat

색은 덱 하우스스타일과 통일: BKS = #267BB6, 7net = #D7292A
(06_ppt/NEXT_SESSION_PROMPT.md 서식 규칙).
"""
import glob
import os
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "02_run/s4_mq7net/profiles"
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

BKS_COL, NET_COL = "#267BB6", "#D7292A"
DMSD_NOISE = 0.30
ARR_MARGIN = 400.0
MIN_PTS = 4


def load(path):
    d = np.loadtxt(path)
    d = d[np.argsort(-d[:, 0])]
    return d[:, 0], d[:, 1], d[:, 2], d[:, 3]


def kinetic_arrest(T, msd):
    d = np.abs(np.diff(msd))
    Tmid = T[1:]
    for i in range(len(d)):
        if np.all(d[i:] < DMSD_NOISE):
            return Tmid[i], Tmid, d
    return None, Tmid, d


def caloric_tg_adaptive(T, epa, arrest):
    if arrest is None:
        return None, None, None, None, None
    liq = T >= arrest + ARR_MARGIN
    gla = T <= arrest - ARR_MARGIN
    if liq.sum() < MIN_PTS or gla.sum() < MIN_PTS:
        return None, None, None, None, None
    sL, aL = np.polyfit(T[liq], epa[liq], 1)
    sG, aG = np.polyfit(T[gla], epa[gla], 1)
    if abs(sL - sG) < 1e-12:
        return None, None, None, None, None
    tg = (aG - aL) / (sL - sG)
    return tg, sL, sG, liq.sum(), gla.sum()


def parse_runs():
    runs = []
    p7 = RUN / "mq7net_profile.dat"
    if p7.exists():
        runs.append(dict(tag="7net", rate=2e13, path=p7, col=NET_COL,
                          ls="-", label="7net-Nano-4.5"))
    for f in sorted(glob.glob(str(RUN / "mqbks_*_profile.dat"))):
        rate_s = os.path.basename(f).split("_")[1]
        rate = float(rate_s)
        runs.append(dict(tag=f"BKS {rate_s}", rate=rate, path=Path(f), col=BKS_COL,
                          ls="--", label=f"BKS {rate_s} K/s"))
    return runs


def main():
    runs = parse_runs()
    for r in runs:
        T, epa, P, msd = load(r["path"])
        arr, Tmid, dmsd = kinetic_arrest(T, msd)
        tg, sL, sG, nL, nG = caloric_tg_adaptive(T, epa, arr)
        r.update(T=T, epa=epa, P=P, msd=msd, Tmid=Tmid, dmsd=dmsd,
                  arrest=arr, tg=tg, sL=sL, sG=sG)

    with open(DAT / "tg_s4_summary.dat", "w") as f:
        header = f"{'run':<10}{'rate(K/s)':>11}{'Tg_arrest(K)':>14}{'Tg_caloric(K)':>15}{'P300(GPa)':>11}\n"
        print(header, end="")
        f.write("# " + header)
        for r in runs:
            arr_s = f"{r['arrest']:.0f}" if r['arrest'] else "-"
            tg_s = f"{r['tg']:.0f}" if r['tg'] else "-"
            line = f"{r['tag']:<10}{r['rate']:>11.1e}{arr_s:>14}{tg_s:>15}{r['P'][-1]/1e4:>11.2f}\n"
            print(line, end="")
            f.write(line)
    print(f"-> {DAT}/tg_s4_summary.dat")

    fig, ax = plt.subplots(1, 2, figsize=(9.6, 4.0))
    a, b = ax

    # ★ BKS epa(~-19 eV/atom)와 7net epa(~-7.8 eV/atom)는 서로 다른 에너지 영점을 쓴다
    #   (BKS = pairwise+Coulomb 장부, 7net = DFT 전자구조 기준). 절대값은 비교 대상이 아니다.
    #   Tg 자체는 각 곡선을 독립적으로 fit하므로 영향받지 않지만, 이 패널에서 곡선 "모양"을
    #   눈으로 비교하려면 세로축을 맞춰야 한다 → 각 곡선을 자기 자신의 300 K 값 기준
    #   상대에너지(depa, meV/atom)로 다시 그린다. T=300 K는 정렬 후 마지막 원소(최저온).
    for r in runs:
        depa = (r["epa"] - r["epa"][-1]) * 1000.0     # meV/atom, 자기 300K 기준
        lw = 2.0 if r["tag"] == "7net" else 1.4
        a.plot(r["T"], depa, r["ls"], lw=lw, c=r["col"], label=r["label"])
        if r["arrest"]:
            a.axvline(r["arrest"], ls=":", lw=1, c=r["col"], alpha=0.55)
    a.axhline(0, ls="-", lw=0.6, c="0.75", zorder=0)
    a.set_xlabel("T (K)"); a.set_ylabel(r"$\Delta$epa vs. 300 K (meV/atom)")
    a.invert_xaxis()
    a.legend(loc="lower right", fontsize=7.5, framealpha=0.9)
    a.xaxis.set_minor_locator(AutoMinorLocator(2))
    a.yaxis.set_minor_locator(AutoMinorLocator(2))
    a.text(0.04, 0.93, "(a)", transform=a.transAxes, fontsize=11.5, fontweight="bold")
    a.set_title(r"$\rho$=2.20 NVT quench, each curve referenced to its own 300 K value", fontsize=9)

    bks = [r for r in runs if r["tag"].startswith("BKS")]
    net = [r for r in runs if r["tag"] == "7net"]
    if len(bks) >= 2:
        x = np.log10([r["rate"] for r in bks])
        y = np.array([r["arrest"] for r in bks], float)
        s, i0 = np.polyfit(x, y, 1)
        xs = np.linspace(x.min() - 0.15, x.max() + 0.15, 50)
        b.plot(10**xs, s * xs + i0, "--", c=BKS_COL, lw=1.2, alpha=0.7, zorder=1)
    for r in bks:
        b.plot(r["rate"], r["arrest"], "o", ms=8, mfc="w", mec=BKS_COL, mew=1.6, zorder=3)
    for r in net:
        b.plot(r["rate"], r["arrest"], "*", ms=16, c=NET_COL, zorder=4)
        if len(bks) >= 2:
            bks_pred = s * np.log10(r["rate"]) + i0
            b.annotate(f"BKS interp {bks_pred:.0f} K\n7net actual {r['arrest']:.0f} K\n"
                       f"gap {bks_pred - r['arrest']:.0f} K",
                       xy=(r["rate"], r["arrest"]), xytext=(1.4, 0.12),
                       textcoords="axes fraction", fontsize=7.8, color=NET_COL,
                       arrowprops=dict(arrowstyle="->", color=NET_COL, lw=0.9))
    b.set_xscale("log")
    b.set_xlabel("quench rate (K/s)"); b.set_ylabel("kinetic-arrest $T_g$ (K)")
    b.text(0.04, 0.06, "(b)", transform=b.transAxes, fontsize=11.5, fontweight="bold")
    b.plot([], [], "o", mfc="w", mec=BKS_COL, mew=1.6, ms=8, label="BKS (3 control rates)")
    b.plot([], [], "*", c=NET_COL, ms=13, label="7net (2e13 K/s)")
    if len(bks) >= 2:
        b.plot([], [], "--", c=BKS_COL, lw=1.2, alpha=0.7, label="BKS linear fit (log rate)")
    b.legend(loc="upper left", fontsize=7.8, framealpha=0.92)
    b.set_title("cooling-rate dependence of $T_g$", fontsize=9.5)

    fig.tight_layout()
    fig.savefig(FIG / "fig_tg_s4.png", dpi=300)
    print(f"-> {FIG}/fig_tg_s4.png")


if __name__ == "__main__":
    main()
