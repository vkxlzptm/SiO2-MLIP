#!/usr/bin/env python
"""Fig. bulk modulus — K(rho). **누가 망을 만들었는가**가 K 오차의 주범이다.

★ 2026-08-25 개정. 이전 판(2곡선)은 `_bak/fig_bulkmod_pre_s4_20260825.py` 에 있다.
  이전 판의 메시지는 "같은 밀도에서 보면 BKS 와 7net 의 K 가 3 % 안에서 겹친다
  -> 겉보기 K0 차이는 평형밀도가 달라서 생긴 착시" 였고, 그 결론은 **그대로 유효하다**.
  S4 가 더한 것은 그 다음 질문의 답이다: **그러면 그 공통 오차(+20 %)는 어디서 오나?**

이 그림이 말하는 것 (S4 결과 반영)
  1. BKS 망 위에서는 포텐셜을 무엇으로 읽든 K 가 +19~23 % 로 붙어 있다.
     (파란 곡선과 가는 붉은 곡선이 서로 가깝다)
  2. **7net 이 자기 힘으로 망을 만들면 K 가 뚝 떨어진다**
     (rho_exp 에서 43.9 -> 37.7 GPa, 실험 37 까지의 간극을 대부분 지운다).
  -> K 오차의 주범은 포텐셜이 아니라 **망 위상 생성자**다.

★ 2026-08-25 (2차 개정) — 냉각률 곡선(7net / BKS net 2e13)을 **뺐다.**
  사용자 판단: 이 계산의 목적은 논문이 아니라 MLIP 사용 경험 증빙이고, 빠른 퀜칭
  BKS 망을 정밀화하는 데 시간을 더 쓰지 않는다. 그래서 그 스캔([A] 냉각률 효과의
  기준선)은 재실행하지 않고 그림·표에서 제외했다.
  **결과로 잃은 것**: [A](냉각률) / [B](위상)의 **수치 분해**. 남는 것은 두 항의
  **합**뿐이다 — 그림의 화살표 라벨이 "from topology + quench rate" 인 이유다.
  되살리려면 `ev_s4_bksnet2e13_scan.txt` 를 cap >= 1200 으로 재실행한 뒤
  SRC 에 "net_bks2" 를 되돌리면 된다 (구판: _bak/fig_bulkmod_pre_drop_bksnet2e13_20260825.py).
  참고로 구판의 잠정 분해는 [A] -0.94 / [B] -4.87 GPa 였고, 그 수치는 미수렴
  스캔에서 나온 것이라 인용 금지였다.

⚠ **두 7net 곡선의 이완 수준이 다르다** (2026-08-25 확인, 의도적으로 남겨둔 한계):
   - 자기망(굵은 빨강): 11 점 전부 "linesearch alpha is zero", 최종 힘 2-norm
     0.018~0.047 -> 잡음 바닥까지 내려갔다. **인용 가능.**
   - BKS망 5e12(가는 빨강, = ev220_scan.txt): 7 점 중 6 점이 "max force evaluations",
     최종 2-norm 0.017~0.395. RESULTS 2 절의 rho0 2.2185 / K0 43.23 이 이 스캔이다.
   -> 따라서 **두 곡선의 K 를 직접 빼서 "위상 효과 = 몇 GPa" 라고 쓰지 말 것.**
      같은 자가 아니다. 그림은 두 곡선의 **위치 관계**를 보여주는 용도이고,
      화살표의 낙차도 그 한계 위에서 읽어야 한다.
      (자기망 쪽 실측: 미수렴 2 점을 cap 1200 으로 재실행했을 때 K@2.20 이
       37.84 -> 37.74 로 0.1 GPa 만 움직였다. 이완 부족의 영향이 늘 크지는 않다는
       뜻이지, BKS망 스캔에서도 작다는 보장은 아니다.)

읽는 법 — 색은 **포텐셜**, 선 굵기는 **망**
  파랑 = BKS 포텐셜, 빨강 = 7net 포텐셜 (프로젝트 공통 약속)
  가는 빨강 = 7net 이 **BKS 가 만든 망**을 읽은 것 (냉각률 **5e12**)
  굵은 빨강 = 7net 이 **자기가 만든 망**을 읽은 것 (냉각률 2e13)
  ⚠ **두 빨강은 냉각률이 다르다** (5e12 vs 2e13). 매칭 냉각률 쌍(2e13/2e13)이
    되려면 폐기한 net_bks2 스캔이 있어야 했다. 그래서 낙차 라벨이
    "from topology + quench rate" — 두 효과의 합이라고 그림이 스스로 밝힌다.
  곡선 3개가 이 그림이 감당할 수 있는 한계다.

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
    "net_own":  "02_run/s4_mq7net/ev/ev_s4_7net_scan.txt",           # 7net / OWN net 2e13
    # "net_bks2": "02_run/s4_mq7net/ev/ev_s4_bksnet2e13_scan.txt",   # 7net / BKS net 2e13
    #   2026-08-25 제외. 위 docstring "2차 개정" 참조 — 스캔이 미수렴(11/11)이고
    #   재실행하지 않기로 했다. 되살리려면 이 줄의 주석을 풀고 파일을 재실행판으로
    #   교체하면 된다. 그림의 곡선/표는 원래도 이 항목을 쓰지 않았고,
    #   [A]/[B] 분해 출력에만 쓰였다.
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

fig, ax = plt.subplots(figsize=(5.0, 4.0))

# ---- 실험 밀도 기준선 ----
ax.axvline(RHO_EXP, ls="--", lw=1.2, c="0.35", alpha=0.9, zorder=1)
# 세로 라벨은 표·곡선과 계속 부딪힌다. 2.20 은 x 눈금과 정확히 겹치므로
# 상단 빈 구역에 가로로 한 번만 적는다.
ax.text(RHO_EXP + 0.006, 49.6, rf"$\rho_{{\rm exp}}$",
        fontsize=9, c="0.3", ha="left", va="top", zorder=8)

# ---- (1) BKS 곡선 — 맥락용 ----
v = F["bks"]
rr = np.linspace(v["rlo"], v["rhi"], 400)
ax.plot(rr, K_of_rho(*v["pf"], rr), "-", c=BKS_COL, lw=1.6, zorder=3)
ax.plot(MASS / v["V"], K_of_rho(*v["pf"], MASS / v["V"]), "o", ms=4.0,
        mfc="w", mec=BKS_COL, mew=1.1, zorder=4)

# ---- (2) 7net on BKS-made network (5e12) ----
#   RESULTS 2절의 기준 곡선(rho0 2.219, K@2.20 43.9)이라 문서와의 대조가 여기 걸려
#   있고, K(rho) 함정을 보여주는 것도 이 곡선이다.
#   ⚠ 단 이 스캔은 7 점 중 6 점이 minimize eval 상한에서 잘렸다 (docstring 참조).
#     곡선의 **모양**(K0')은 그 계통오차에 노출돼 있다. 위치 비교에만 쓴다.
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

# ---- rho_exp 에서의 낙차: BKS망(5e12) -> 자기망 ----
# 2e13 스캔을 폐기했으므로 화살표는 5e12 곡선에서 잰다.
# 이 낙차는 위상 효과 + 냉각률 효과의 **합**이다 — 라벨에 그대로 쓴다.
# 두 항으로 쪼갠 수치는 이제 없다 (docstring "2차 개정" 참조).
ktop, kown = F["net_bks1"]["Kx"], F["net_own"]["Kx"]
ax.annotate("", xy=(RHO_EXP, kown + 0.35), xytext=(RHO_EXP, ktop - 0.35),
            arrowprops=dict(arrowstyle="<->", lw=1.5, color=NET_COL), zorder=8)
ax.text(RHO_EXP - 0.007, 0.5 * (ktop + kown) +1 ,
        f"from topology\n+ quench rate",
        fontsize=7.5, ha="right", va="center", color=NET_COL, linespacing=1.35,
        bbox=dict(fc="white", ec="none", alpha=0.70, pad=1.), zorder=9)

ax.text(RHO_EXP + 0.006, 0.5 * (ktop + kown) - 1,
        f"$-${ktop-kown:.1f} GPa",
        fontsize=7.5, ha="left", va="center", color=NET_COL, linespacing=1.35,
        bbox=dict(fc="white", ec="none", alpha=0.05, pad=1.), zorder=9)

# ---- 표 ---------------------------------------------------------------
# ★ 표 위치·크기를 만질 때는 **아래 TABLE 딕셔너리만** 고치면 된다.
#   좌표는 전부 axes 분율(왼쪽아래 0,0 ~ 오른쪽위 1,1). 데이터 값이 아니다.
#     x, y   : 상자의 **왼쪽아래 모서리**
#     w      : 상자 폭.  높이 h 는 행 수에서 자동 계산된다(아래).
#     fs     : 글자 크기
#     row_dy : 행 간격.  키우면 상자도 같이 커진다
#     pad    : 상자 안쪽 위/아래 여백
#     cols   : 각 열의 x 위치를 **상자 왼쪽(x) 기준 상대값**으로 준다.
#              -> 상자를 옮기면 열도 같이 따라온다 (예전엔 절대값이라 따로 고쳐야 했다)
#              lab 만 왼쪽정렬, 나머지는 오른쪽정렬(숫자 자릿수 맞추려고)
TABLE = dict(
    x=0.015, y=0.015, w=0.765, fs=7.2, row_dy=0.05, pad=0.02,
    hdr_extra=0.045,          # 헤더 2번째 줄(단위)이 차지하는 높이. 상자가 위로 늘어난다.
    cols=dict(lab=0.020, rate=0.28, r0=0.40, k0=0.51, kx=0.67),
)
# ※ 2026-08-25 (2차): 수치 열을 전부 **가운데 정렬**로 바꿨다.
#   -> 따라서 아래 cols 값은 **열의 오른쪽 끝이 아니라 열의 중심**이다 (lab 만 왼쪽 끝).
#   오른쪽 정렬이었을 때는 "K @ 2.20" 열의 데이터가 "45.3  (+23%)" 로 유독 길어
#   헤더가 데이터 덩어리 한가운데 오지 않고 치우쳐 보였다.
#   ※ 열 간격은 데이터/단위 중 **더 넓은 쪽**이 결정한다. 지금 병목은
#     rho_0 의 단위 (g/cm^3) 다. 열을 옮기거나 단위를 늘릴 때는 그려서 확인할 것.
# ※ 열 간격은 figsize 에 딸려 온다. 그림 크기를 바꾸면(현재 5.0x4.0)
#   axes 분율은 그대로인데 글자는 pt 단위라 상대적으로 커져 열이 붙는다.
#   -> figsize 를 줄이면 w 를 늘리거나 fs 를 줄일 것.

ROWS = [("BKS / BKS net", "5e12", "bks", BKS_COL, "normal"),
        ("7net / BKS net", "5e12", "net_bks1", NET_COL, "normal"),
        ("7net / OWN net", "2e13", "net_own", NET_COL, "bold")]

# 높이·행 y 는 행 수에서 자동으로 나온다 (행을 늘리거나 줄여도 상자가 따라간다)
# 헤더는 **2줄**(이름 + 단위)이라 row_dy + hdr_extra 를 차지한다.
T = TABLE
_hdr_h = T["row_dy"] + T["hdr_extra"]                      # 헤더 블록 높이(2줄)
_h = 2 * T["pad"] + _hdr_h + len(ROWS) * T["row_dy"]
_top = T["y"] + _h - T["pad"]                              # 상자 안쪽 위 끝
_hdr_y = _top - 0.5 * _hdr_h                               # 헤더 블록 중심
CX = {k: T["x"] + dx for k, dx in T["cols"].items()}

ax.add_patch(Rectangle((T["x"], T["y"]), T["w"], _h,
                       transform=ax.transAxes, fc="white", ec="0.75", lw=0.7,
                       alpha=0.96, zorder=10))
FS = T["fs"]
# 헤더: 이름 + 줄바꿈 + 단위. **한 개의 text 로 그린다** (ma="center" 로 두 줄끼리 정렬).
# 수치 열은 헤더·데이터 모두 ha="center" — cols 값이 열의 **중심**이다.
HDR = (("rate", "quench" + "\n" + r"$\mathrm{(K/s)}$"),
       ("r0",   r"$\rho_0$" + "\n" + r"$\mathrm{(g/cm^3)}$"),
       ("k0",   r"$K_0$" + "\n" + r"$\mathrm{(GPa)}$"),
       ("kx",   rf"$K$ @ {RHO_EXP:.2f}" + "\n" + r"$\mathrm{(GPa)}$"))
for key, lab in HDR:
    ax.text(CX[key], _hdr_y, lab, transform=ax.transAxes, fontsize=FS,
            ha="center", va="center", ma="center", color="0.35",
            linespacing=1.35, zorder=11)
for i, (lab, rate, key, col, wt) in enumerate(ROWS):
    y = _top - _hdr_h - T["row_dy"] * (i + 0.5)
    v = F[key]
    ax.text(CX["lab"], y, lab, transform=ax.transAxes, fontsize=FS,
            ha="left", va="center", color="0.15", fontweight=wt, zorder=11)
    ax.text(CX["rate"], y, rate, transform=ax.transAxes, fontsize=FS,
            ha="center", va="center", color="0.45", fontweight=wt, zorder=11)
    ax.text(CX["r0"], y, f"{v['rho0']:.2f}", transform=ax.transAxes, fontsize=FS,
            ha="center", va="center", color=col, fontweight=wt, zorder=11)
    ax.text(CX["k0"], y, f"{v['K0']:.1f}", transform=ax.transAxes, fontsize=FS,
            ha="center", va="center", color=col, fontweight=wt, zorder=11)
    ax.text(CX["kx"], y, f"{v['Kx']:.1f}  ({100*(v['Kx']-K_EXP)/K_EXP:+.0f}%)",
            transform=ax.transAxes, fontsize=FS,
            ha="center", va="center", color=col, fontweight=wt, zorder=11)

# 냉각률 효과는 표의 두 5e12/2e13 행이 직접 보여준다.
ax.set_xlabel(r"$\rho$ (g/cm$^3$)")
ax.set_ylabel(r"$K = -V\,\mathrm{d}P/\mathrm{d}V$  (GPa)")
ax.set_xlim(2.02, 2.47)
ax.set_ylim(21, 50)
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
print(f"\nBKS망(5e12) -> 자기망 낙차 @rho_exp : "
      f"{F['net_bks1']['Kx']-F['net_own']['Kx']:.2f} GPa"
      f"  (위상 + 냉각률의 **합**. 분해는 없다 — bksnet2e13 스캔 폐기)")
print("⚠ 두 곡선의 이완 수준이 다르다(자기망 전점 수렴 / BKS망 6점 미수렴).")
print("  이 낙차를 '위상 효과 = N GPa' 로 인용하지 말 것. docstring 참조.")
