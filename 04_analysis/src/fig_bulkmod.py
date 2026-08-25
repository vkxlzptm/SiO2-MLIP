#!/usr/bin/env python
"""Fig. bulk modulus — K(rho). **누가 망을 만들었는가**가 K 오차의 주범이다.

★ 2026-08-25 개정. 이전 판(2곡선)은 `_bak/fig_bulkmod_pre_s4_20260825.py` 에 있다.
  이전 판의 메시지는 "같은 밀도에서 보면 BKS 와 7net 의 K 가 3 % 안에서 겹친다
  -> 겉보기 K0 차이는 평형밀도가 달라서 생긴 착시" 였고, 그 결론은 **그대로 유효하다**.
  S4 가 더한 것은 그 다음 질문의 답이다: **그러면 그 공통 오차(+20 %)는 어디서 오나?**

이 그림이 말하는 것 (S4 결과 반영)
  1. BKS 망 위에서는 포텐셜을 무엇으로 읽든 K 가 +19~23 % 로 붙어 있다.
     (파란 곡선과 붉은 띠가 서로 가깝다)
  2. **같은 BKS 망을 냉각률만 4배 바꿔 만들어도 K 는 거의 안 움직인다**
     (rho_exp 에서 0.9 GPa, 2.1 %). 곡선을 하나 더 그리지 않고 표 아래 각주로 적는다 —
     ★ 처음엔 두 냉각률 곡선 사이를 '띠'로 칠했는데 **그림이 거짓말을 했다**:
       두 피팅의 K0' 가 -2.02 와 -0.52 로 크게 달라 rho ~ 2.24 에서 교차하고
       양 끝에서 3 GPa 까지 벌어지는 부채꼴이 된다. "띠 두께 = 냉각률 효과"는
       rho_exp 에서만 참이다. (K0' 차이는 +-5 % 창 7점 피팅의 잡음으로 본다 —
       RESULTS 2절이 "K0' 를 물리적 주장으로 쓰지 말 것"이라 한 그 사정.)
  3. **7net 이 자기 힘으로 망을 만들면 K 가 뚝 떨어진다**
     (rho_exp 에서 42.98 -> 38.11 GPa, 실험까지의 간극 81 % 제거).
  -> K 오차의 주범은 포텐셜도 냉각률도 아니라 **망 위상 생성자**다.
     수치 분해는 04_analysis/dat/ev_s4_summary.dat, 근거는 s4_mq7net/NOTE.md "분석 8".

읽는 법 — 색은 **포텐셜**, 선 굵기는 **망**
  파랑 = BKS 포텐셜, 빨강 = 7net 포텐셜 (프로젝트 공통 약속)
  가는 빨강 = 7net 이 **BKS 가 만든 망**을 읽은 것 (냉각률 2e13, 자기망과 매칭)
  굵은 빨강 = 7net 이 **자기가 만든 망**을 읽은 것
  냉각률을 맞춘 쌍만 그린다 — 곡선 3개가 이 그림이 감당할 수 있는 한계다.

⚠ **BKS 곡선의 K 는 인용하지 말 것** (선은 맥락용으로만 그린다).
   부피창을 바꾸면 K 가 최대 20 % 움직인다 (BM3 잔차 292 / 793 bar).
   절단된 -C/r^6 꼬리 artifact 다 — RESULTS 2절 참조.
   7net 행들은 같은 검사에서 0.3~0.9 % 로 안정하다.

⚠ "BKS 가 오차 상쇄로 K0 를 맞춘다"(이전 판 docstring)는 **본 계산의 관찰**이지
   문헌 인용이 아니다. 실리카는 K0' < 0 이라 조밀할수록 무르고, BKS 는 평형밀도를
   6.6 % 높게 잡으므로 자동으로 낮은 K0 를 보고하게 된다.

피팅: BM3 를 virial P(V) 에 맞춘 뒤 K = -V dP/dV. `bm3.py` 사용(scipy 불필요,
      scipy curve_fit 과 유효숫자 4자리 대조 완료).
"""
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator
from matplotlib.patches import Rectangle

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from bm3 import MASS, fit_PV, K_of_rho, load_scan          # noqa: E402

FIG = ROOT / "04_analysis/fig"; FIG.mkdir(exist_ok=True)

plt.rcParams.update({
    "font.size": 10, "axes.labelsize": 11, "xtick.labelsize": 10, "ytick.labelsize": 10,
    "legend.fontsize": 9, "legend.handlelength": 1.5,
    "xtick.direction": "in", "ytick.direction": "in",
    "xtick.top": True, "ytick.right": True,
    "xtick.major.size": 5, "ytick.major.size": 5,
    "xtick.minor.size": 2.8, "ytick.minor.size": 2.8,
    "axes.linewidth": 0.9, "lines.linewidth": 1.6,
})

BKS_COL, NET_COL = "#267BB6", "#D7292A"
RHO_EXP, K_EXP = 2.20, 37          # Deschamps 2014 / Yokoyama 2010 (05_doc/SOURCES.md)

SRC = {
    "bks":      "02_run/s2_relax/ev_bks_scan_tail.txt",              # BKS  / BKS net 5e12
    "net_bks1": "02_run/s2_relax/ev220_scan.txt",                    # 7net / BKS net 5e12
    "net_bks2": "02_run/s4_mq7net/ev/ev_s4_bksnet2e13_scan.txt",     # 7net / BKS net 2e13
    "net_own":  "02_run/s4_mq7net/ev/ev_s4_7net_scan.txt",           # 7net / OWN net 2e13
}
F = {}
for k, fn in SRC.items():
    p = ROOT / fn
    if not p.exists():
        sys.exit(f"없는 입력: {fn}")
    V, E, P = load_scan(p)
    pf = fit_PV(V, P)
    F[k] = dict(pf=pf, V=V, rho0=MASS / pf[0],
                rlo=MASS / V.max(), rhi=MASS / V.min())
    F[k]["K0"] = float(K_of_rho(*pf, F[k]["rho0"]))
    F[k]["Kx"] = float(K_of_rho(*pf, RHO_EXP))

fig, ax = plt.subplots(figsize=(5.6, 4.3))

# ---- 실험 밀도 기준선 ----
ax.axvline(RHO_EXP, ls="--", lw=1.2, c="0.35", alpha=0.9, zorder=1)
# 세로 라벨은 표·곡선과 계속 부딪힌다. 2.20 은 x 눈금과 정확히 겹치므로
# 상단 빈 구역에 가로로 한 번만 적는다.
ax.text(RHO_EXP + 0.004, 51.2, rf"$\rho_{{\rm exp}}$",
        fontsize=9, c="0.3", ha="left", va="top", zorder=8)

# ---- (1) BKS 곡선 — 맥락용 ----
v = F["bks"]
rr = np.linspace(v["rlo"], v["rhi"], 400)
ax.plot(rr, K_of_rho(*v["pf"], rr), "-", c=BKS_COL, lw=1.6, zorder=3)
ax.plot(MASS / v["V"], K_of_rho(*v["pf"], MASS / v["V"]), "o", ms=4.0,
        mfc="w", mec=BKS_COL, mew=1.1, zorder=4)

# ---- (2) 7net on BKS-made network ----
#   5e12 = **곡선으로** 그린다. RESULTS 2절의 기준 곡선(rho0 2.219, K@2.20 43.9)이라
#     문서와의 대조가 여기 걸려 있고, K(rho) 함정을 보여주는 것도 이 곡선이다.
#   2e13 = **rho_exp 의 점 하나로만** 그린다. [B](순수 위상 효과)의 기준선이라
#     필요한 것은 K@2.20 = 43.0 **한 숫자뿐**이다. 곡선을 그리면 쓰지도 않을 모양을
#     보여주게 되고, 하필 그 모양이 다른 두 스캔과 반대로 휜다.
#
#   ★ 왜 곡선을 안 그리는지 — "피팅이 나빠서"가 아니다 (2026-08-25 진단):
#       잔차 RMS 35 bar (셋 중 **가장 좋음**), K0' = -0.52 ± 0.06,
#       leave-one-out 진폭 0.13 (5e12 는 0.27, 자기망은 0.68) -> **가장 단단한 피팅**.
#       그리고 피팅과 무관하게 원자료 |dP/dV| 가 V 증가에 따라 **감소**한다(-0.666),
#       다른 두 스캔은 **증가**한다(+1.159, +0.614). 곡률의 부호가 자료 수준에서 다르다.
#   ★ 대신 의심스러운 것은 **이완 정도**다: maxf 중앙값이 0.064 eV/A 로
#       5e12(0.037)·자기망(0.028)의 두 배다. minimize 가 150 eval 상한에서 멈추는데
#       이 구조만 끝까지 덜 풀린 채로 멈춘다 -> 부피에 따라 다르게 덜 풀리면
#       P(V) 의 **곡률**이 계통적으로 휜다. K@2.20 은 LOO 0.06 GPa 로 무사하지만
#       K0'(모양)는 이 계통오차에 노출된다.
#   -> 우리가 인용하는 것은 K@2.20 하나이고 그건 튼튼하다. 모양은 안 그린다.
#      (모양이 필요해지면 이 스캔을 eval 상한 400 이상으로 재실행할 것. 약 1시간.)
v = F["net_bks1"]
rr = np.linspace(v["rlo"], v["rhi"], 400)
ax.plot(rr, K_of_rho(*v["pf"], rr), "-", c=NET_COL, lw=1.5, zorder=3)
ax.plot(MASS / v["V"], K_of_rho(*v["pf"], MASS / v["V"]), "o", ms=4.0,
        mfc="w", mec=NET_COL, mew=1.2, zorder=4)
# ---- (3) 7net on its OWN network — 이 그림의 주인공 ----
v = F["net_own"]
rr = np.linspace(v["rlo"], v["rhi"], 400)
ax.plot(rr, K_of_rho(*v["pf"], rr), "-", c=NET_COL, lw=2.6, zorder=5)
ax.plot(MASS / v["V"], K_of_rho(*v["pf"], MASS / v["V"]), "D", ms=4.2,
        mfc=NET_COL, mec="w", mew=0.9, zorder=6)

# ---- 각 곡선의 평형점 rho0 를 큰 채운 마커로 (옛 fig_bulkmod 방식) ----
#   표의 rho0 열과 그림을 이어주는 고리. 작은 빈 마커(스캔한 부피)와 크기·채움이
#   달라 역할이 겹치지 않는다.
for key, col in (("bks", BKS_COL), ("net_bks1", NET_COL), ("net_own", NET_COL)):
    v = F[key]
    ax.plot(v["rho0"], v["K0"], "o", ms=11, mfc=col, mec="w", mew=1.7, zorder=7)

# ---- 실험값 ----
ax.plot(RHO_EXP, K_EXP, "*", ms=18, mfc="k", mec="w", mew=1.0, zorder=9)

# ---- rho_exp 에서의 낙차: 띠 -> 자기망 ----
# 2e13 을 그림에서 뺐으므로 화살표는 5e12 곡선에서 잰다.
# 그러면 이 낙차는 위상 효과 + 냉각률 효과의 **합**이다 — 라벨에 그대로 쓴다.
# 순수 위상 효과([B] = -4.87)는 ev_s4_summary.dat / NOTE 분석 8 에 있다.
ktop, kown = F["net_bks1"]["Kx"], F["net_own"]["Kx"]
ax.annotate("", xy=(RHO_EXP, kown + 0.35), xytext=(RHO_EXP, ktop - 0.35),
            arrowprops=dict(arrowstyle="<->", lw=1.5, color=NET_COL), zorder=8)
ax.text(RHO_EXP + 0.006, 0.5 * (ktop + kown),
        f"$-${ktop-kown:.1f} GPa\nfrom topology\n+ quench rate",
        fontsize=8.3, ha="left", va="center", color=NET_COL, linespacing=1.35,
        bbox=dict(fc="white", ec="none", alpha=0.85, pad=1.5), zorder=9)

# ---- 표 ----
BOX = dict(x=0.025, y=0.098, w=0.660, h=0.232)   # 3행 기준 (4행이면 y=0.028, h=0.300)
ax.add_patch(Rectangle((BOX["x"], BOX["y"]), BOX["w"], BOX["h"],
                       transform=ax.transAxes, fc="white", ec="0.75", lw=0.7,
                       alpha=0.96, zorder=10))
FS = 7.1
CX = dict(lab=0.042, rate=0.310, r0=0.425, k0=0.520, kx=0.672)
ax.text(CX["rate"], 0.293, "quench", transform=ax.transAxes, fontsize=FS,
        ha="right", va="center", color="0.35", zorder=11)
ax.text(CX["r0"], 0.293, r"$\rho_0$", transform=ax.transAxes, fontsize=FS,
        ha="right", va="center", color="0.35", zorder=11)
ax.text(CX["k0"], 0.293, r"$K_0$", transform=ax.transAxes, fontsize=FS,
        ha="right", va="center", color="0.35", zorder=11)
ax.text(CX["kx"], 0.293, rf"$K$ @ {RHO_EXP:.2f}", transform=ax.transAxes, fontsize=FS,
        ha="right", va="center", color="0.35", zorder=11)
ROWS = [("BKS / BKS net", "5e12", "bks", BKS_COL, "normal"),
        ("7net / BKS net", "5e12", "net_bks1", NET_COL, "normal"),
        ("7net / OWN net", "2e13", "net_own", NET_COL, "bold")]
for i, (lab, rate, key, col, wt) in enumerate(ROWS):
    y = 0.245 - 0.042 * i
    v = F[key]
    ax.text(CX["lab"], y, lab, transform=ax.transAxes, fontsize=FS,
            ha="left", va="center", color="0.15", fontweight=wt, zorder=11)
    ax.text(CX["rate"], y, rate, transform=ax.transAxes, fontsize=FS,
            ha="right", va="center", color="0.45", fontweight=wt, zorder=11)
    ax.text(CX["r0"], y, f"{v['rho0']:.3f}", transform=ax.transAxes, fontsize=FS,
            ha="right", va="center", color=col, fontweight=wt, zorder=11)
    ax.text(CX["k0"], y, f"{v['K0']:.1f}", transform=ax.transAxes, fontsize=FS,
            ha="right", va="center", color=col, fontweight=wt, zorder=11)
    ax.text(CX["kx"], y, f"{v['Kx']:.1f}  ({100*(v['Kx']-K_EXP)/K_EXP:+.0f}%)",
            transform=ax.transAxes, fontsize=FS,
            ha="right", va="center", color=col, fontweight=wt, zorder=11)

# 냉각률 효과는 이제 표의 두 행(5e12 / 2e13)이 직접 보여준다 — 각주 삭제.
ax.set_xlabel(r"$\rho$ (g/cm$^3$)")
ax.set_ylabel(r"$K = -V\,\mathrm{d}P/\mathrm{d}V$  (GPa)")
ax.set_xlim(2.02, 2.46)
ax.set_ylim(24, 52)
ax.xaxis.set_minor_locator(AutoMinorLocator(2))
ax.yaxis.set_minor_locator(AutoMinorLocator(2))

h = [plt.Line2D([], [], ls="-", lw=1.6, c=BKS_COL, marker="o", ms=4.0,
                mfc="w", mec=BKS_COL, mew=1.1),
     plt.Line2D([], [], ls="-", lw=1.5, c=NET_COL, marker="o", ms=4.0,
                mfc="w", mec=NET_COL, mew=1.2),
     plt.Line2D([], [], ls="-", lw=2.6, c=NET_COL, marker="D", ms=4.2,
                mfc=NET_COL, mec="w", mew=0.9),
     plt.Line2D([], [], ls="", marker="o", ms=9, mfc="0.5", mec="w", mew=1.5),
     plt.Line2D([], [], ls="", marker="*", ms=14, mfc="k", mec="w")]
l = ["BKS pot. on BKS-net",
     "7net pot. on BKS-net",
     "7net pot. on 7net-net",
     r"$K_0$ at own $\rho_0$ ($P=0$)",
     rf"Fused silica: $K_{{\rm exp}}$ = {K_EXP} GPa"]
ax.legend(h, l, loc="upper right", framealpha=0.94, fontsize=7.6,
          handlelength=1.9, borderpad=0.45, labelspacing=0.45)
ax.set_title("Who built the network sets the elastic error", fontsize=11)
fig.tight_layout()
fig.savefig(FIG / "fig_bulkmod2.png", dpi=300)
print(f"-> {FIG}/fig_bulkmod2.png\n")

print(f"{'구조':<24}{'rho0':>9}{'K0':>8}{'K@2.20':>9}{'vs exp':>9}")
for lab, rate, key, *_ in ROWS:
    v = F[key]
    print(f"{lab+' '+rate:<24}{v['rho0']:>9.4f}{v['K0']:>8.2f}{v['Kx']:>9.2f}"
          f"{100*(v['Kx']-K_EXP)/K_EXP:>+8.1f}%")
print(f"\n띠 두께 @rho_exp (냉각률 4배 효과) : "
      f"{abs(F['net_bks1']['Kx']-F['net_bks2']['Kx']):.2f} GPa")
print(f"띠 -> 자기망 낙차 @rho_exp (위상 효과): "
      f"{F['net_bks2']['Kx']-F['net_own']['Kx']:.2f} GPa")
