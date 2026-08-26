#!/usr/bin/env python
"""Fig. Si-O-Si 각 사다리 — **3-ring 은 원인이 아니라 증상이다.**

★ 이 그림이 말하는 것 (NOTE.md "S4 분석 13")
  7net 자기 망은 3원환이 BKS 의 2.5 배(4.3 % -> 10.7 %)다. 3원환 산소는 기하학적으로
  각이 좁으므로(모든 구조에서 비3원환보다 18~20° 낮다) "3원환이 많아져서 평균이 내려갔다"
  는 설명이 자연스러워 보인다. **그런데 데이터가 그걸 지지하지 않는다.**

  전체 평균 이동 -10.48° (BKS 2e13 -> 7net 자기망) 중
      3원환 **비율 증가**만으로 설명되는 몫  =  1.2°  (11 %)
      비3원환 산소 자체가 좁아진 몫          =  9.3°  (89 %)

  -> 그림에서 **회색 점선(비3원환)이 실선(전체)과 나란히 내려간다**는 것이 요점이다.
     3원환 비율이 바뀌어서 평균이 끌려 내려간 것이라면 비3원환 선은 평평해야 한다.

  방어 가능한 서술:
    "7net 자기 망은 Si-O-Si 가 **전역적으로** 좁고, 3-ring 초과는 그 전역 변화가
     고리 통계에 드러난 **한 단면**이다."
  쓰면 안 되는 서술:
    "3원환이 많아서 망이 변형되고 그래서 무르다" (인과가 데이터로 지지되지 않는다)

★ 그림 안 라벨은 **영문**이다 — 프로젝트의 다른 그림과 통일. 발표 자료가 한국어여도
  그림은 영문으로 두고 슬라이드 본문에서 한국어로 설명한다.

★ 왜 단일 패널인가
  분해 수치(11 % / 89 %)는 숫자 두 개라 그림 안 주석으로 충분하다. 패널을 더하면
  같은 이야기를 두 번 하게 된다 (project rule: 패널 추가 전에 "없으면 어떤 정보가
  완전히 사라지는가"를 먼저 묻는다).

⚠ 한계
  - `prod_*.data` **단일 300 K 스냅샷** 기반. 트라젝토리 평균과 0.15° 이내로 일치함을
    확인했으므로 결론에는 영향이 없다(분석 13).
  - 7net 계열은 **시드 1개**라 실현간 산포를 잴 수 없다 -> 오차막대를 그리지 않는다
    (project rule). BKS 2e13 도 각도는 시드 1개만 계산돼 있다.
  - AIMD 는 전체 평균만 있다(3원환 분리 값 없음). 120 원자·5 ps quench 조건.

입력: 04_analysis/dat/S4_angles_by_ring.dat  (src/ring_angle_s4.py 산출)
출력: 04_analysis/fig/fig_angle_s4.png
"""
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator

ROOT = Path(__file__).resolve().parents[2]
DAT = ROOT / "04_analysis/dat"
FIG = ROOT / "04_analysis/fig"; FIG.mkdir(exist_ok=True)

plt.rcParams.update({
    "font.size": 10, "axes.labelsize": 11, "xtick.labelsize": 9.5, "ytick.labelsize": 10,
    "legend.fontsize": 8.6, "xtick.direction": "in", "ytick.direction": "in",
    "ytick.right": True, "xtick.major.size": 0, "ytick.major.size": 5,
    "ytick.minor.size": 2.8, "axes.linewidth": 0.9,
})

# 색 = 포텐셜 + 망 조합 (fig_sq_s4.png · fig_bulkmod2.png 와 같은 약속)
COL = {"BKS_2e13": "#267BB6", "7net_BKSnet": "#8E44AD",
       "7net_own": "#D7292A", "AIMD": "#2E9E5B"}

# ---------------------------------------------------------------- data
rows = {}
for ln in open(DAT / "S4_angles_by_ring.dat"):
    if ln.startswith("#"):
        continue
    c = ln.split()
    if len(c) < 8:
        continue
    rows[c[0]] = dict(pct3=float(c[3]), all=float(c[4]), in3=float(c[5]), not3=float(c[6]))

ORDER = ["BKS_2e13", "7net_BKSnet", "7net_own"]
LABEL = {"BKS_2e13": "BKS\non BKS-net",
         "7net_BKSnet": "7net\non BKS-net",
         "7net_own": "7net\non 7net-net",
         "AIMD": "AIMD PBE\n(120 atoms)"}
AIMD_ALL = 138.65                      # Dechant 2026 (3원환 분리값 없음)

x = np.arange(len(ORDER) + 1)
y_all = [rows[k]["all"] for k in ORDER] + [AIMD_ALL]
y_not = [rows[k]["not3"] for k in ORDER]
y_in3 = [rows[k]["in3"] for k in ORDER]

fig, ax = plt.subplots(figsize=(5.4, 3.9))

# 실험 밴드 (Wright 1994 / Dupree — Part 1 과 같은 출처)
ax.axhspan(140, 150, color="0.85", zorder=0)
ax.text(3.42, 149.4, "expt. band\n140-150 deg", fontsize=8.2, color="0.35",
        ha="right", va="top", linespacing=1.25, zorder=1)

# 비3원환 / 3원환 — 회색 점선. **이 두 선이 나란히 내려가는 것이 이 그림의 요점.**
ax.plot(x[:3], y_not, "--", c="0.45", lw=1.2, zorder=2)
ax.plot(x[:3], y_in3, ":", c="0.45", lw=1.2, zorder=2)
for xx, yy in zip(x[:3], y_not):
    ax.plot(xx, yy, "^", ms=5.5, mfc="w", mec="0.45", mew=1.1, zorder=3)
for xx, yy in zip(x[:3], y_in3):
    ax.plot(xx, yy, "v", ms=5.5, mfc="w", mec="0.45", mew=1.1, zorder=3)

# 전체 평균 — 굵은 실선 + 구조별 색 마커
ax.plot(x, y_all, "-", c="0.2", lw=1.8, zorder=4)
for i, k in enumerate(ORDER + ["AIMD"]):
    ax.plot(x[i], y_all[i], "o", ms=11, mfc=COL[k], mec="w", mew=1.6, zorder=6)

# 3원환 ↔ 비3원환 간격 (기하학적 강제) — 한 곳에만 표시
gap = y_not[0] - y_in3[0]
ax.annotate("", xy=(0.30, y_in3[0]), xytext=(0.30, y_not[0]),
            arrowprops=dict(arrowstyle="<->", lw=1.0, color="0.45"), zorder=5)
ax.text(0.40, y_in3[0] + 1.2, f"geometric offset  {gap:.0f}°\n(holds in every structure)",
        fontsize=8.0, color="0.35", ha="left", va="bottom", linespacing=1.3, zorder=7)

# 핵심 주석 — 전역 이동
d_tot = rows["7net_own"]["all"] - rows["BKS_2e13"]["all"]
ax.annotate("", xy=(2.0, rows["7net_own"]["not3"]), xytext=(2.0, rows["BKS_2e13"]["not3"]),
            arrowprops=dict(arrowstyle="->", lw=1.6, color="#D7292A"), zorder=5)
ax.text(1.93, 0.5 * (rows["7net_own"]["not3"] + rows["BKS_2e13"]["not3"]),
        "non-3-ring O\nnarrows too", fontsize=8.6, color="#D7292A", fontweight="bold",
        ha="right", va="center", linespacing=1.3, zorder=7,
        bbox=dict(fc="w", ec="none", alpha=0.85, pad=1.6))

ax.set_xticks(x)
ax.set_xticklabels([LABEL[k] for k in ORDER + ["AIMD"]], linespacing=1.35)
ax.set_xlim(-0.42, 3.45)
ax.set_ylim(118, 159)
ax.set_ylabel(r"Si–O–Si angle  (deg)")
ax.yaxis.set_minor_locator(AutoMinorLocator(2))

h = [plt.Line2D([], [], ls="-", lw=1.8, c="0.2", marker="o", ms=7,
                mfc="0.55", mec="w", mew=1.2),
     plt.Line2D([], [], ls="--", lw=1.2, c="0.45", marker="^", ms=5.5, mfc="w", mec="0.45"),
     plt.Line2D([], [], ls=":", lw=1.2, c="0.45", marker="v", ms=5.5, mfc="w", mec="0.45")]
ax.legend(h, ["all bridging O", "not in 3-ring", "in 3-ring"],
          loc="lower left", frameon=False, fontsize=8.4, handlelength=2.2,
          labelspacing=0.34, borderpad=0.25)

ax.set_title("3-rings are a symptom, not the cause", fontsize=11)
fig.tight_layout()
fig.savefig(FIG / "fig_angle_s4.png", dpi=300)
print(f"-> {FIG}/fig_angle_s4.png")

# ---------------------------------------------------------------- 분해 (그림 주석용 수치)
b, n = rows["BKS_2e13"], rows["7net_own"]
fb, fn = b["pct3"] / 100, n["pct3"] / 100
# 3원환 비율만 BKS -> 7net 으로 바뀌고 각 그룹 평균은 BKS 값 그대로일 때의 예측 이동
pred = (fn * b["in3"] + (1 - fn) * b["not3"]) - (fb * b["in3"] + (1 - fb) * b["not3"])
print(f"\n전체 평균 이동 (7net_own - BKS_2e13) : {n['all'] - b['all']:+.2f} deg")
print(f"  3원환 비율 증가만으로 예측되는 몫   : {pred:+.2f} deg  ({100*pred/(n['all']-b['all']):.0f} %)")
print(f"  비3원환 자체가 좁아진 몫            : {n['not3'] - b['not3']:+.2f} deg")
print(f"  3원환 비율 {100*fb:.1f} % -> {100*fn:.1f} %")
