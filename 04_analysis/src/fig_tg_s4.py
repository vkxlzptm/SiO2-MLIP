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

★ 2026-08-24 (확장 스윕 반영). 임계값 0.10 / K=5 는 **그대로 두었다** (재도출 금지 항목).
  바뀐 것은 두 가지뿐이고 둘 다 '있던 판정을 어디까지 믿을지'의 문제다.

  (1) **동적 범위 게이트 (신규).** ΔMSD/100K 는 구간 '시간'에 비례하는데 스윕이
      1e12(구간 100 ps) ~ 2e14(구간 0.5 ps)로 **200배**를 벌려놨다. 그 끝에서는
      액체 상태의 ΔMSD 자체가 임계값 아래로 내려간다:
          2e14 : 액체(T>=3700K) ΔMSD = 0.072  < 임계값 0.10   -> 판정 불가
          1e14 : 액체 0.271 (임계값의 2.7배)                  -> 통과, 단 여유 적음
          2e13 : 액체 1.03  (10배)                            -> 정상
          1e12 : 액체 18.65 (186배)                           -> 정상
      액체가 이미 임계값 아래면 급랭 시작 직후 판정이 걸린다. 실제로 2e14 는
      arrest = 3800 K (출발 4000 K 에서 200 K)로 나왔고, caloric 피팅은 액체 가지
      점이 없어 실패했다 — 코드가 스스로 "이 값 못 쓴다"고 말한 것이다.
      -> **액체 ΔMSD < 2.5 x 임계값이면 그 런을 제외한다.** 2e14 만 걸린다.
      이 게이트는 임계값을 바꾸는 게 아니라 **임계값이 적용 가능한 구간인지**를 본다.

  (2) **매칭 냉각률 반복 3개(2e13, 2e13_r2, 2e13_r3) 집계.** Tg = 2800/3000/2500 K,
      sd = 252 K. 이게 이 프로젝트가 처음 갖는 **Tg 의 시드간 오차막대**다.
      반복이 없는 냉각률에는 이 sd 를 '전가한' 오차막대를 옅게 그린다(측정치 아님).
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
BKS_COL_MID = "#267BB6"       # 범례 스와치용
try:
    BKS_CMAP = matplotlib.colormaps["Blues"]          # matplotlib >= 3.5
except AttributeError:
    import matplotlib.cm as _cm
    BKS_CMAP = _cm.get_cmap("Blues")                  # matplotlib < 3.9 fallback
DMSD_NOISE = 0.10   # A^2 / 100K-segment. 유도 근거 아래 참조
K_CONSEC = 5        # 연속 구간 수 (=500 K 폭) 동안 문턱 아래 유지되면 정지로 판정
ARR_MARGIN = 400.0
MIN_PTS = 4
# 액체(T >= LIQ_T)의 ΔMSD 가 임계값의 이 배수보다 작으면 arrest 판정 자체가 불가능하다.
LIQ_T = 3700.0
DR_MIN = 2.5
# (c) 에서 반복을 돌린 냉각률(2e13)에만 시드 산포를 막대로 표시할지. **기본 끔.**
# 8개 점 중 하나만 막대가 서면 그 점이 무슨 특별한 것처럼 읽히는데, 실제로는
# "같은 조건을 세 번 돌려 중앙값을 쓴" 것뿐이다. 시드 산포(2500~3000 K)는
# 결론 중 하나지만 그림이 아니라 tg_s4_summary.dat / NOTE.md 가 들고 있으면 된다.
# 켜면 n=3 지점에 sd 가 아닌 **실측 최소~최대**를 그린다(정규분포 가정 불가한 표본).
SHOW_SEED_SPREAD = False


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


def liquid_dmsd(T, msd):
    """액체 구간 ΔMSD 평균. 임계값과의 비(동적 범위)가 판정 가능성을 정한다."""
    d = np.abs(np.diff(msd))
    m = T[1:] >= LIQ_T
    return float(d[m].mean()) if m.any() else float("nan")


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
        # 반복런(_r2/_r3)도 같은 dashed 로 둔다. 예전엔 dotted 로 구분했는데
        # (b)에서 선 종류가 두 가지로 보여 "다른 무엇"처럼 읽힌다. 같은 냉각률의
        # 같은 계산이므로 구분할 이유가 없다.
        runs.append(dict(tag=f"BKS {tag}", rate=rate, path=Path(f), col=cmap[rate],
                          ls="--", label=f"BKS {tag} K/s"))
    return runs


def main():
    runs = parse_runs()
    for r in runs:
        T, epa, P, msd = load(r["path"])
        arr, Tmid, dmsd = kinetic_arrest(T, msd)
        tg, sL, sG, nL, nG = caloric_tg_adaptive(T, epa, arr)
        liq = liquid_dmsd(T, msd)
        r.update(T=T, epa=epa, P=P, msd=msd, Tmid=Tmid, dmsd=dmsd,
                  arrest=arr, tg=tg, sL=sL, sG=sG,
                  liq=liq, dr=liq / DMSD_NOISE, valid=liq >= DR_MIN * DMSD_NOISE)

    bad = [r for r in runs if not r["valid"]]
    if bad:
        print("!! 동적 범위 부족으로 제외 (액체 ΔMSD < %.2f = %.1f x 임계값):" % (DR_MIN * DMSD_NOISE, DR_MIN))
        for r in bad:
            print(f"   {r['tag']:<12} 액체 ΔMSD = {r['liq']:.3f} ({r['dr']:.1f}x)  "
                  f"-> arrest {r['arrest']} 는 급랭 시작 직후 오판. 사용 안 함.")
        print()
    runs = [r for r in runs if r["valid"]]

    with open(DAT / "tg_s4_summary.dat", "w") as f:
        header = (f"{'run':<12}{'rate(K/s)':>11}{'Tg_arrest(K)':>14}{'Tg_caloric(K)':>15}"
                  f"{'P300(GPa)':>11}{'liqdMSD':>9}{'DR(x)':>7}\n")
        print(header, end="")
        f.write("# " + header)
        for r in runs:
            arr_s = f"{r['arrest']:.0f}" if r['arrest'] else "-"
            tg_s = f"{r['tg']:.0f}" if r['tg'] else "-"
            line = (f"{r['tag']:<12}{r['rate']:>11.1e}{arr_s:>14}{tg_s:>15}"
                    f"{r['P'][-1]/1e4:>11.2f}{r['liq']:>9.3f}{r['dr']:>7.1f}\n")
            print(line, end="")
            f.write(line)
    print(f"-> {DAT}/tg_s4_summary.dat")

    fig, ax = plt.subplots(1, 3, figsize=(10.5, 3.5))
    a, b, c = ax

    # ---------------- (a) E(T)-E(300K), T 증가 방향 = 오른쪽 ----------------
    # 스윕 확장으로 런이 10개가 됐다. 냉각률별 범례를 (a)에 다 쓰면 그림을 덮으므로
    # 두 계열로만 축약한다 — 냉각률 구분은 (c)가 전담한다.
    n_bks = sum(1 for r in runs if r["tag"].startswith("BKS"))
    # BKS 는 **불투명**하게 둔다. 투명도를 주면 냉각률 그라데이션(옅을수록 느림)이
    # 안 보여서 (a) 가 갖고 있던 정보 하나가 통째로 사라진다.
    # 7net 도 zorder 를 올릴 필요가 없다 — BKS 선이 더 얇아 저온에서도 비치고,
    # 고온에서는 어차피 갈라져 나오므로 겹쳐도 보인다.
    for r in runs:
        depa = (r["epa"] - r["epa"][-1]) * 1000.0     # meV/atom, 자기 300K 기준
        is7 = r["tag"] == "7net"
        a.plot(r["T"], depa, r["ls"], lw=2.2 if is7 else 1.1,
               marker="." if is7 else None, ms=3.5, c=r["col"])
        if r["arrest"]:
            a.axvline(r["arrest"], ls=":", lw=1.1, c=r["col"], alpha=0.85, zorder=0)
    a.axhline(0, ls="-", lw=0.6, c="0.75", zorder=0)

    # ── 조화(유리) 기준선 ────────────────────────────────────────────────
    # T <= 1500 K (유리 구간) 의 dE/dT 를 런마다 1차 피팅해 평균한 기울기로,
    # 300 K 를 원점 삼아 4000 K 까지 그은 직선이다.
    # 이 기울기는 **11개 런 전부 0.1327~0.1345** (1.3 % 일치) 이고 조화 고전 극한
    # 1.5 kB = 0.1293 의 1.04배 -> Tg 아래에서는 두 포텐셜이 구별되지 않는다(순수 진동).
    # 곡선이 이 선 위로 벌어진 양이 **배열(configurational) 에너지**다.
    # 4000 K 에서: 7net 249 vs BKS 71~106 meV/atom (수치는 NOTE.md 분석 5).
    # ★ 수치는 그림에 쓰지 않는다 — 화살표로 표시하려면 반드시 T = 4000 K 에 세워야
    #   하는데(양이 그 온도에서 정의된다) 거기는 축 오른쪽 끝이라 자리가 없다.
    #   엉뚱한 T 에 세운 화살표는 실제로 곡선-기준선 간격과 맞지 않는다(1차 판의 버그).
    def glass_slope(r):
        m = r["T"] <= 1500
        return np.polyfit(r["T"][m], (r["epa"][m] - r["epa"][-1]) * 1000.0, 1)[0]
    sg = np.mean([glass_slope(r) for r in runs])
    Tline = np.array([300.0, 4000.0])
    a.plot(Tline, sg * (Tline - 300.0), "-", lw=1.1, c="0.45", zorder=1)

    a.set_xlabel("T (K)"); a.set_ylabel(r"$E(T)-E(300\,\mathrm{K})$ (meV/atom)")
    a.set_title(r"Quench at $\rho$ = 2.20 (NVT)", fontsize=10)
    a.plot([], [], "-", c=NET_COL, lw=2.0, label=NET_LABEL)
    # 색-냉각률 대응에 컬러바를 달지 않는다. (c) 가 이미 색 <-> 냉각률을 점으로
    # 읽게 해주므로 컬러바는 같은 정보를 축 하나 더 써서 반복하는 셈이다.
    # 방향(옅음=느림)만 한 줄로 알려주면 충분하다.
    a.plot([], [], "--", c=BKS_TREND_COL, lw=1.3,
           label=f"BKS, {n_bks} runs, $10^{{12}}$–$10^{{14}}$ K/s\n"
                 f"(light = slow, dark = fast)")
    #a.legend(bbox_to_anchor=(0.01, 0.62), loc="lower left", fontsize=7.5, framealpha=0.9)
    a.legend(loc="lower right", fontsize=7.2, framealpha=0.9)
    a.xaxis.set_minor_locator(AutoMinorLocator(2))
    a.yaxis.set_minor_locator(AutoMinorLocator(2))
    a.text(0.04, 0.96, "(a)", transform=a.transAxes, fontsize=11.5, fontweight="bold", ha='left', va='top')

    # ---------------- (b) kinetic-arrest 판정 그 자체 (ΔMSD vs T) ----------------
    for r in runs:
        is7 = r["tag"] == "7net"
        b.semilogy(r["Tmid"], np.maximum(r["dmsd"], 1e-3), r["ls"],
                   lw=2.2 if is7 else 1.0, marker="." if is7 else None, ms=3.5,
                   c=r["col"])
        if r["arrest"]:
            b.axvline(r["arrest"], ls=":", lw=1.1, c=r["col"], alpha=0.85, zorder=0)
    b.axhline(DMSD_NOISE, ls="-", lw=1.1, c="0.35", zorder=0)
    b.text(0.03, 0.49, f"threshold = {DMSD_NOISE} $\\mathrm{{\\AA}}^2$/100K,\n5 consecutive segments",
           transform=b.transAxes, fontsize=6.6, color="0.35")
    b.set_xlabel("T (K)"); b.set_ylabel(r"$\Delta$MSD per 100 K ($\mathrm{\AA}^2$)")
    b.set_title("Kinetic-arrest definition", fontsize=10)
    b.xaxis.set_minor_locator(AutoMinorLocator(2))
    b.text(0.04, 0.92, "(b)", transform=b.transAxes, fontsize=11.5, fontweight="bold")

    # ---------------- (c) Tg(kinetic arrest) vs 냉각률 ----------------
    # 같은 냉각률의 반복은 하나의 점으로 묶는다. 반복이 있는 냉각률에서만 sd 가
    # '측정'되고, 나머지에는 그 sd 를 전가해 옅게 그린다(측정치 아님을 색으로 구분).
    bks = [r for r in runs if r["tag"].startswith("BKS") and r["arrest"]]
    net = [r for r in runs if r["tag"] == "7net"]

    # 반복이 있는 냉각률은 **중앙값**으로 대표시킨다.
    #   - arrest 판정이 100 K 격자 위의 계단함수라, 평균(2766.7 K)은 이 측정이
    #     원리적으로 낼 수 없는 값이다. 중앙값(2800 K)은 실측된 격자 위의 값이다.
    #   - 세 값 2800/3000/2500 에서 평균 2767 vs 중앙값 2800 은 33 K 차이로
    #     격자 간격(100 K)의 1/3 이다. 즉 어느 쪽을 써도 결론은 안 바뀐다.
    #   - 실제로 중앙값 쪽 회귀가 잔차 sd 72 K 로 평균(79 K)보다 약간 낫다.
    #   ※ 시드 산포 sd = 252 K 자체는 결론 중 하나다 — 그림에서 빼되
    #     tg_s4_summary.dat 와 NOTE.md 에는 세 런이 그대로 남아 있다.
    byrate = {}
    for r in bks:
        byrate.setdefault(r["rate"], []).append(r["arrest"])
    rates = np.array(sorted(byrate))
    means = np.array([np.median(byrate[r]) for r in rates])
    nrep = np.array([len(byrate[r]) for r in rates])
    sds = np.array([np.std(byrate[r], ddof=1) if len(byrate[r]) > 1 else np.nan
                    for r in rates])
    SD_SEED = np.nanmax(sds) if np.isfinite(sds).any() else np.nan   # 측정된 시드 산포

    x = np.log10(rates)
    slope = intcpt = se_slope = None
    if len(rates) >= 3:
        slope, intcpt = np.polyfit(x, means, 1)
        res = means - (slope * x + intcpt)
        n = len(x)
        s_res = np.sqrt((res**2).sum() / (n - 2))          # 잔차 표준편차
        Sxx = ((x - x.mean())**2).sum()
        se_slope = s_res / np.sqrt(Sxx)
        xs = np.linspace(x.min() - 0.2, x.max() + 0.2, 120)
        c.plot(10**xs, slope * xs + intcpt, "--", c=BKS_TREND_COL, lw=2.4, alpha=0.55, zorder=1)
        # 신뢰밴드는 그리지 않는다. 이 패널에서 밴드가 하던 일("7net 이 BKS 추세에서
        # 유의하게 벗어나는가")은 범례의 기울기 ±SE 와 767→10^4.3 화살표가 이미 한다.
        # 색면 하나를 더 얹을 값어치가 없다. 필요하면 아래 se_line 을 되살려라 —
        # ★ 단 올바른 형태는 중심에서 가장 좁은 모래시계다:
        #      SE(x) = s_res * sqrt(1/n + (x - x̄)^2 / Sxx)
        #   기울기만 ±SE 로 흔들고 절편을 고정하면 x=0(= rate 1 K/s, 그림 밖)을 축으로
        #   회전해 데이터 구간 전체에서 부풀어 오른다. 1차 판이 그 상태였다.
        print(f"[fit] slope {slope:.0f} +- {se_slope:.0f} K per decade,  잔차 sd {s_res:.0f} K")

    cmap = bks_color_map(list(rates))
    # ★ 오차막대는 **반복을 실제로 돌린 냉각률에만** 그린다 (현재 2e13 뿐).
    #   나머지 rate 에 같은 sd 를 전가해 그리면 측정하지 않은 것을 측정한 것처럼
    #   보이게 되고, 점이 8개라 그림도 번잡해진다. 다른 rate 의 불확도는
    #   회귀 밴드(±1SE)가 이미 표현하고 있다.
    # 모든 점을 같은 기호로. 반복 여부를 그림에서 구분하지 않는다 —
    # 8개 중 1개만 다르게 표시하면 그 하나가 무슨 특별한 것처럼 읽히는데,
    # 실제로는 "같은 조건을 세 번 돌려 중앙값을 쓴" 것뿐이다.
    for r, m, nn in zip(rates, means, nrep):
        if SHOW_SEED_SPREAD and nn > 1:
            v = np.array(byrate[r], float)
            c.errorbar(r, m, yerr=[[m - v.min()], [v.max() - m]], fmt="o", ms=8.5,
                       mfc=cmap[r], mec="0.3", mew=0.9, ecolor="0.35",
                       elinewidth=1.3, capsize=3.2, capthick=1.3, zorder=4)
        else:
            c.plot(r, m, "o", ms=8.5, mfc=cmap[r], mec="0.3", mew=0.9, zorder=3)
    for r in net:
        c.plot(r["rate"], r["arrest"], "*", ms=17, c=NET_COL, zorder=5)

    # 7net-BKS 간극을 '냉각률 몇 decade 어치인가'로 환산해 표시한다.
    if slope and net:
        m2 = float(np.median(byrate[net[0]["rate"]])) if net[0]["rate"] in byrate else None
        if m2:
            gap = m2 - net[0]["arrest"]
            dec = gap / slope
            c.annotate("", xy=(net[0]["rate"], net[0]["arrest"]+80), xytext=(net[0]["rate"], m2-30),
                       arrowprops=dict(arrowstyle="<->", lw=1.2, color="0.35"))
            # "decades" 는 10배(자릿수)라는 뜻인데 연대(年代)로 오독되기 쉽다.
            # 그림에서는 배수로 직접 쓴다.
            c.text(net[0]["rate"] * 1.13, 0.5 * (m2 + net[0]["arrest"]),
                   f"{gap:.0f} K\n$\\equiv$ $10^{{{dec:.1f}}}\\times$ slower\n  quench rate",
                   fontsize=7.4, color="0.25", va="center", ha="left")

    c.set_xscale("log")
    c.tick_params(axis="x", labelsize=8.5)
    #plt.setp(c.get_xticklabels(), rotation=5, ha="right", rotation_mode="anchor")
    plt.setp(c.get_xticklabels(minor=True), rotation=35, ha="right", rotation_mode="anchor")
    c.set_xlabel("Quench rate (K/s)"); c.set_ylabel("Kinetic-arrest $T_g$ (K)")
    c.set_ylim(1650, 3750)
    c.text(0.035, 0.035, "(c)", transform=c.transAxes, fontsize=11.5,
           fontweight="bold", ha="left", va="bottom")
    if slope:
        # 기울기 수치는 범례에서 뺀다 — 이 패널의 논점은 "7net 이 추세 아래에 있다"이지
        # 기울기의 정밀도가 아니다. 수치는 stdout / tg_s4_summary.dat / NOTE.md 에 있다.
        c.plot([], [], "--", c=BKS_TREND_COL, lw=2.4, alpha=0.55, label="BKS linear fit")
    c.plot([], [], "o", mfc=BKS_COL_MID, mec="0.25", ms=8, label="BKS controls")
    c.plot([], [], "*", c=NET_COL, ms=13, label=NET_LABEL)
    # 범례는 좌상단 — 좌하단/우하단은 7net 별표와 gap 화살표가 차지한다.
    c.legend(loc="upper left", fontsize=7.0, framealpha=0.92,
             handletextpad=0.8, borderaxespad=0.9, labelspacing=0.9)
    c.set_title("Cooling-rate dependence of $T_g$", fontsize=9.5)

    fig.tight_layout()

    # 기준선 라벨은 **선과 평행**하게. 회전각은 화면좌표에서 재야 하므로
    # tight_layout 으로 축 상자가 확정된 뒤에 계산한다(먼저 하면 각이 틀어진다).
    q1 = a.transData.transform((300.0, 0.0))
    q2 = a.transData.transform((4000.0, sg * 3700.0))
    ang = float(np.degrees(np.arctan2(q2[1] - q1[1], q2[0] - q1[0])))
    Tt = 3450.0
    a.text(Tt, sg * (Tt - 300.0) - 12, "harmonic baseline", rotation=ang,
           rotation_mode="anchor", ha="center", va="top",
           fontsize=7.2, color="0.6")

    fig.savefig(FIG / "fig_tg_s4.png", dpi=300)
    print(f"-> {FIG}/fig_tg_s4.png")


if __name__ == "__main__":
    main()
