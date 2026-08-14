#!/usr/bin/env python
"""Fig. S(q) — 중성자 구조인자. 우리 두 포텐셜 vs 중성자 회절 실험.

★ 이 그림이 말하는 것 — 위치와 진폭이 서로 다른 얘기를 한다
  FSDP(first sharp diffraction peak, ~1.5 Å⁻¹)는 유리 **중거리 질서**의 표준 지표다.
  · **위치**는 중거리 주기성(2π/q)이 결정 → 망의 위상이 지배.
    BKS 1.581 / 7net 1.586 로 **사실상 같고** 둘 다 실험(1.500)보다 5 % 높다.
    → 7net 이 위상을 못 바꿨다는 것이 ring 통계에 이어 **산란 지표에서도 확인**된다.
  · **진폭**은 그 주기성이 얼마나 뚜렷한가 → 국소 구조(결합각 폭)도 기여.
    BKS 1.579 → 7net 1.438 로 실험(1.376) 쪽으로 내려온다.
    Si-O-Si 각 분포가 넓어진 것(σ 12.2 → 13.7)과 방향이 맞는다.
  → **7net 은 국소는 고치고 위상은 못 고친다**는 이 프로젝트의 결론을 한 그림으로 보여준다.

★ 왜 sq_direct(절단 없음) 를 쓰나
  sq_analyze.py 의 g(r)→FT 경로는 r 을 15 Å 에서 자르고 Lorch 창을 곱해 **피크를 뭉갠다**
  (FSDP 진폭 1.44 → 1.25). 실험 곡선은 그런 처리가 없으므로 그대로 겹치면 불공정하다.
  두 경로의 FSDP **위치**는 0.3 % 안에서 일치했다 → 창은 폭·높이만 건드린다는 확인.

⚠ 한계
  · 우리 q 는 2π/L = 0.207 Å⁻¹ 간격으로만 존재한다(껍질 평균). 그보다 가는 구조는 못 본다.
  · 실험 곡선은 논문 그림에서 digitize 한 것이다. 고k 평균이 0.985 (1 이어야 정상)로,
    약 1.5 % 의 계통 오차가 있다고 보면 된다. 진폭 비교는 그 정도 여유를 두고 읽을 것.
  · 중성자 산란길이는 문헌값. Zeidler 가 논문에 적은 ND 가중(0.0694:0.3880:0.5427)과
    우리 계산이 소수 넷째 자리까지 일치하는 것으로 검증했다.
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
    "legend.fontsize": 9, "xtick.direction": "in", "ytick.direction": "in",
    "xtick.top": True, "ytick.right": True,
    "xtick.major.size": 5, "ytick.major.size": 5,
    "xtick.minor.size": 2.8, "ytick.minor.size": 2.8,
    "axes.linewidth": 0.9, "lines.linewidth": 1.4,
})

exp = np.loadtxt(ROOT / "04_analysis/dat/zeidler_sq_ambient.dat")
bks = np.loadtxt(ROOT / "02_run/s0_requench/bks220_sqd.dat")
net = np.loadtxt(ROOT / "02_run/s3_md/7net220_sqd.dat")


def fsdp(q, s, lo=1.0, hi=2.2):
    """FSDP 위치·진폭. **잡음에 강한 추정을 쓴다.**

    우리 MD 곡선은 껍질 통계 때문에 거칠어서, 최댓값 3점만 쓰는 포물선 보간은
    잡음 스파이크에 끌려간다(세 추정법이 0.02 Å⁻¹ 어긋났다. 실험 곡선은 0.002).
    → 위치는 **반치폭 위 무게중심**(여러 점 사용), 진폭은 **최댓값 근처 평균**.
    """
    m = (q > lo) & (q < hi) & np.isfinite(s)
    qq, ss = q[m], s[m]
    base = ss.min()
    w = ss >= base + 0.5 * (ss.max() - base)
    qpk = np.sum(qq[w] * (ss[w] - base)) / np.sum(ss[w] - base)
    top = ss >= base + 0.93 * (ss.max() - base)
    return qpk, float(ss[top].mean())


SET = [("Neutron diffraction (exp.)", "k", exp[:, 0], exp[:, 1], 1.8, "-"),
       ("BKS", "tab:blue", bks[:, 0], bks[:, 1], 1.4, "-"),
       ("7net-Nano-4.5", "tab:red", net[:, 0], net[:, 1], 1.4, "-")]
pk = {lab: fsdp(q, s) for lab, _, q, s, _, _ in SET}

fig, ax = plt.subplots(1, 2, figsize=(7.8, 3.5),
                       gridspec_kw={"width_ratios": [1.55, 1]})
a, b = ax

# ---------- (a) 전 구간 ----------
for lab, c, q, s, lw, ls in SET:
    a.plot(q, s, ls, c=c, lw=lw, label=lab, zorder=3 if c == "k" else 2)
a.axhline(1, ls=":", lw=0.8, c="0.6", zorder=1)
a.set_xlim(0.8, 10); a.set_ylim(0.3, 1.9)
a.set_xlabel(r"$q$ ($\rm\AA^{-1}$)"); a.set_ylabel(r"$S_{\rm N}(q)$")
a.legend(loc="upper right", framealpha=0.92, fontsize=8.5,
         borderpad=0.4, labelspacing=0.35)
a.text(0.03, 0.92, "(a)", transform=a.transAxes, fontsize=11.5, fontweight="bold")

# ---------- (b) FSDP 확대 ----------
for lab, c, q, s, lw, ls in SET:
    b.plot(q, s, ls, c=c, lw=lw + 0.3, zorder=3 if c == "k" else 2)
    qp, sp = pk[lab]
    b.plot([qp], [sp], "o", ms=7, mfc=c, mec="w", mew=1.5, zorder=5)
    b.axvline(qp, ls=":", lw=1.0, c=c, alpha=0.8, zorder=1)
b.set_xlim(1.05, 2.15); b.set_ylim(0.80, 2.02)   # 위쪽에 표 자리 확보
b.set_xlabel(r"$q$ ($\rm\AA^{-1}$)")
b.set_title("FSDP", fontsize=10)
b.text(0.05, 0.04, "(b)", transform=b.transAxes, fontsize=11.5,
       fontweight="bold", va="bottom")   # 표가 좌상단이라 태그는 아래로

rows = [("exp.", "k"), ("BKS", "tab:blue"), ("7net-Nano-4.5", "tab:red")]
labs = ["Neutron diffraction (exp.)", "BKS", "7net-Nano-4.5"]
qe = pk[labs[0]][0]
b.text(0.05, 0.955, r"$q_{\rm FSDP}$ ($\rm\AA^{-1}$)", transform=b.transAxes,
       fontsize=8.5, ha="left", va="top", color="0.15")
for j, (nm, c) in enumerate(rows):
    qp, sp = pk[labs[j]]
    txt = f"{nm}  {qp:.2f}" + ("" if j == 0 else f"   ({100*(qp/qe-1):+.0f} %)")
    b.text(0.05, 0.955 - 0.085 * (j + 1), txt, transform=b.transAxes,
           fontsize=8.5, ha="left", va="top", color=c,
           fontweight="bold" if j else "normal")

for a_ in ax:
    a_.xaxis.set_minor_locator(AutoMinorLocator(2))
    a_.yaxis.set_minor_locator(AutoMinorLocator(2))

fig.suptitle("Neutron structure factor of a-SiO$_2$ at 300 K  "
             "(exp.: Zeidler $et\\ al.$, PRL $\\bf 113$, 135501 (2014))",
             fontsize=10, y=1.0)
fig.tight_layout(rect=[0, 0, 1, 1.02])
fig.savefig(FIG / "fig_sq.png", dpi=300)
print(f"-> {FIG}/fig_sq.png\n")

print(f"{'':28s}{'q_FSDP':>9s}{'vs exp':>9s}{'S_FSDP':>9s}{'vs exp':>9s}")
for lab in labs:
    q0, s0 = pk[lab]
    qe_, se_ = pk[labs[0]]
    print(f"{lab:28s}{q0:9.3f}{100*(q0/qe_-1):+8.1f}%{s0:9.3f}{100*(s0/se_-1):+8.1f}%")
