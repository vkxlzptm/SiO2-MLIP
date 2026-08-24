#!/usr/bin/env python
"""Fig. S4 quench Tg — BKS vs 7net, 냉각률 의존성을 한 그림에.

quench220_fit.py(BKS ρ=2.20 단일 냉각률)의 후속. S4에서 냉각률을 바꿔가며
BKS 통제런 여러 개 + 7net 본런 1종을 같이 돌렸으므로, 이제 "포텐셜 차이"와
"냉각률 차이"를 한 축에 놓고 비교할 수 있다.

★ 여기서 재는 에너지는 엔탈피(H)가 아니라 **포텐셜 에너지(PE)**다.
  epa = pe/atoms (LAMMPS variable), NVT 고정부피라 PV 항도 운동에너지도 안 들어간다.

Tg 추정 두 가지, 그림에 **둘 다** 보인다 (mq7net_profile.dat 형식:
T epa(eV/atom) P(bar) MSD(A^2)):
  (a)+(b) kinetic arrest — ΔMSD/100K 가 잡음 수준(점선) 아래로 떨어지는 T.
      **1차 지표.** (b) 패널이 그 판정 자체를 보여준다 — 이게 없으면 (a)의
      점선이 어디서 왔는지 그림만 보고는 알 수 없다.
  (a) caloric Tg (보조) — E(T) 액체/유리 두 직선의 교점. fit 창을 kinetic
      arrest 기준으로 재배치한다(arrest+400K 이상 = 액체 가지, arrest-400K
      이하 = 유리 가지). 수치는 tg_s4_summary.dat 에 별도로 남긴다(그림엔 안 그림 —
      caloric 값은 냉각률마다 fit 안정성이 달라 1차 지표로 안 쓴다).
  (c) 두 방법이 아니라 **kinetic arrest를 냉각률에 대해** 모아 본 것.

입력: 02_run/s4_mq7net/profiles/{mq7net,mqbks_*}_profile.dat
출력: 04_analysis/fig/fig_tg_s4.png, 04_analysis/dat/tg_s4_summary.dat

색: 7net = 하우스 레드(#D7292A) 고정. BKS는 냉각률에 따른 파랑 그라데이션
(느릴수록 옅게, 빠를수록 짙게) — 냉각률 개수가 늘어도(스윕 확장) 구분되게.
"""
import glob
import os
import re
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
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

NET_COL = "#D7292A"
NET_LABEL = "7net-Nano-4.5"
BKS_TREND_COL = "#267BB6"     # (c) 추세선 전용 (점은 그라데이션)
try:
    BKS_CMAP = matplotlib.colormaps["Blues"]          # matplotlib >= 3.5
except AttributeError:
    import matplotlib.cm as _cm
    BKS_CMAP = _cm.get_cmap("Blues")                  # matplotlib < 3.9 fallback
DMSD_NOISE = 0.10   # A^2 / 100K-segment. 유도 근거 아래 참조
K_CONSEC = 5        # 연속 구간 수 (=500 K 폭) 동안 문턱 아래 유지되면 정지로 판정
ARR_MARGIN = 400.0
MIN_PTS = 4


def bks_color_map(rates):
    """냉각률 -> 파랑 그라데이션. 느릴수록 옅게, 빠를수록 짙게."""
    rates = sorted(set(rates))
    if len(rates) == 1:
        return {rates[0]: BKS_TREND_COL}
    lo, hi = np.log10(min(rates)), np.log10(max(rates))
    norm = Normalize(vmin=lo, vmax=hi)
    return {r: BKS_CMAP(0.35 + 0.55 * norm(np.log10(r))) for r in rates}


def load(path):
    d = np.loadtxt(path)
    d = d[np.argsort(-d[:, 0])]
    return d[:, 0], d[:, 1], d[:, 2], d[:, 3]


def kinetic_arrest(T, msd):
    """★ 문턱값 0.10과 연속조건 K=5의 근거(2026-08-24 재검토):
    저온 유리부(T<=1000K, 확실히 얼어있는 구간)의 ΔMSD 실측 p95가 런마다
    0.010~0.030 (04_analysis/dat 참조 없음, 세션 로그에 기록) — 가장 시끄러운 커브의
    3배(0.10)를 문턱으로 잡는다. "그 뒤로 끝까지 문턱 아래"(K=all) 기준은 저온부의
    우연한 튐 한 번에도 arrest가 훨씬 낮은 T로 오판된다(BKS 5e12: thr 0.10→2700K인데
    thr 0.05→1600K로 급락 — 튐 하나 때문). K=5(500K 폭) 연속조건으로 바꾸면
    thr=0.05/0.10/0.15, k=3/5/8 전 조합에서 thr=0.10 결과가 k와 무관하게 안정된다."""
    d = np.abs(np.diff(msd))
    Tmid = T[1:]
    for i in range(len(d) - K_CONSEC + 1):
        if np.all(d[i:i + K_CONSEC] < DMSD_NOISE):
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
                          ls="-", label=NET_LABEL))
    bks_files = sorted(glob.glob(str(RUN / "mqbks_*_profile.dat")))
    rate_of = {}
    for f in bks_files:
        base = os.path.basename(f)
        tag = base[len("mqbks_"):-len("_profile.dat")]      # '2e13' or '2e13_r2'
        m = re.match(r"(\d+e\d+)", tag)
        rate_of[f] = (tag, float(m.group(1)))
    cmap = bks_color_map([r for _, r in rate_of.values()])
    for f in bks_files:
        tag, rate = rate_of[f]
        runs.append(dict(tag=f"BKS {tag}", rate=rate, path=Path(f), col=cmap[rate],
                          ls="--" if "_r" not in tag else ":",
                          label=f"BKS {tag} K/s"))
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

    fig, ax = plt.subplots(1, 3, figsize=(10.5, 3.5))
    a, b, c = ax

    # ---------------- (a) E(T)-E(300K), T 증가 방향 = 오른쪽 ----------------
    for r in runs:
        depa = (r["epa"] - r["epa"][-1]) * 1000.0     # meV/atom, 자기 300K 기준
        lw = 2.0 if r["tag"] == "7net" else 1.3
        a.plot(r["T"], depa, r["ls"], lw=lw, marker=".", ms=3.5,
               c=r["col"], label=r["label"])
        if r["arrest"]:
            a.axvline(r["arrest"], ls=":", lw=1, c=r["col"], alpha=0.55)
    a.axhline(0, ls="-", lw=0.6, c="0.75", zorder=0)
    a.set_xlabel("T (K)"); a.set_ylabel(r"$E(T)-E(300\,\mathrm{K})$ (meV/atom)")
    a.set_title(r"$\rho$=2.20 NVT quench", fontsize=10)
    a.legend(loc="lower right", fontsize=7.5, framealpha=0.9)
    a.xaxis.set_minor_locator(AutoMinorLocator(2))
    a.yaxis.set_minor_locator(AutoMinorLocator(2))
    a.text(0.04, 0.96, "(a)", transform=a.transAxes, fontsize=11.5, fontweight="bold", ha='left', va='top')

    # ---------------- (b) kinetic-arrest 판정 그 자체 (ΔMSD vs T) ----------------
    for r in runs:
        lw = 2.0 if r["tag"] == "7net" else 1.3
        b.semilogy(r["Tmid"], np.maximum(r["dmsd"], 1e-3), r["ls"], lw=lw,
                   marker=".", ms=3.5, c=r["col"])
        if r["arrest"]:
            b.axvline(r["arrest"], ls=":", lw=1, c=r["col"], alpha=0.55)
    b.axhline(DMSD_NOISE, ls="-", lw=1.1, c="0.35", zorder=0)
    b.text(0.03, 0.49, f"threshold = {DMSD_NOISE} $\\mathrm{{\\AA}}^2$/100K,\n 5 consecutive segments",
           transform=b.transAxes, fontsize=7.3, color="0.35")
    b.set_xlabel("T (K)"); b.set_ylabel(r"$\Delta$MSD per 100 K ($\mathrm{\AA}^2$)")
    b.set_title("kinetic-arrest definition", fontsize=10)
    b.xaxis.set_minor_locator(AutoMinorLocator(2))
    b.text(0.04, 0.92, "(b)", transform=b.transAxes, fontsize=11.5, fontweight="bold")

    # ---------------- (c) Tg(kinetic arrest) vs 냉각률 ----------------
    bks = [r for r in runs if r["tag"].startswith("BKS")]
    net = [r for r in runs if r["tag"] == "7net"]
    if len(bks) >= 2:
        x = np.log10([r["rate"] for r in bks])
        y = np.array([r["arrest"] for r in bks], float)
        s, i0 = np.polyfit(x, y, 1)
        xs = np.linspace(x.min() - 0.15, x.max() + 0.15, 50)
        c.plot(10**xs, s * xs + i0, "--", c=BKS_TREND_COL, lw=2.6, alpha=0.4, zorder=1)
    for r in bks:
        c.plot(r["rate"], r["arrest"], "o", ms=8, mfc=r["col"], mec="0.25", mew=0.8, zorder=3)
    for r in net:
        c.plot(r["rate"], r["arrest"], "*", ms=16, c=NET_COL, zorder=4)
    c.set_xscale("log")
    c.tick_params(axis="x", labelsize=8.5)
    plt.setp(c.get_xticklabels(), rotation=35, ha="right", rotation_mode="anchor")
    plt.setp(c.get_xticklabels(minor=True), rotation=35, ha="right", rotation_mode="anchor")
    c.set_xlabel("quench rate (K/s)"); c.set_ylabel("kinetic-arrest $T_g$ (K)")
    c.text(0.04, 0.06, "(c)", transform=c.transAxes, fontsize=11.5, fontweight="bold")
    if len(bks) >= 2:
        c.plot([], [], "--", c=BKS_TREND_COL, lw=2.6, alpha=0.4, label="BKS linear fit (log rate)")
    c.plot([], [], " ", label="BKS points: light=slow, dark=fast")
    c.plot([], [], "*", c=NET_COL, ms=13, label=f"{NET_LABEL} (2e13 K/s)")
    c.legend(bbox_to_anchor=(0.99,0.4), loc="center right", fontsize=7.8, framealpha=0.92)
    c.set_title("cooling-rate dependence of $T_g$", fontsize=9.5)

    fig.tight_layout()
    fig.savefig(FIG / "fig_tg_s4.png", dpi=300)
    print(f"-> {FIG}/fig_tg_s4.png")


if __name__ == "__main__":
    main()
