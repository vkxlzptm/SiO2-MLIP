#!/usr/bin/env python
"""Fig. S(q) — 중성자 구조인자. 우리 두 포텐셜 vs 중성자 회절 실험.

★ 이 그림이 말하는 것 — 위치와 진폭이 서로 다른 얘기를 한다
  FSDP(first sharp diffraction peak)는 유리 **중거리 질서**의 표준 지표다.
  · **위치**는 중거리 주기성(2π/q)이 결정 → 망의 위상이 지배.
    BKS 1.593 / 7net 1.590 로 **오차 안에서 같고**, 둘 다 실험(1.492)보다 6.7 % 높다.
    → 7net 이 위상을 못 바꿨다는 것이 ring 통계에 이어 **산란 지표에서도 확인**된다.
    우리 망의 중거리 특성 길이가 실물보다 6 % 짧다.
  · **진폭**은 그 주기성이 얼마나 뚜렷한가 → 국소 구조도 기여.
    BKS 1.462 → 7net 1.360 으로 **실험(1.357)과 사실상 일치**한다.
    Si-O-Si 각 분포가 넓어진 것(σ 12.2 → 13.7)과 방향이 맞는다.
  → **국소는 고치고 위상은 못 고친다**를 한 그림으로 보여준다.

★ FSDP 를 어떻게 재나 — **최댓값을 쓰면 안 된다.**
  잡음 있는 곡선의 최댓값은 **항상 위로 편향**된다(스파이크를 집는다).
  실제로 껍질 폭 0.05 → 0.10 으로 바꾸자 BKS 진폭이 1.58 → 1.43 으로 떨어졌다.
  진짜 값이 변한 게 아니라 잡음이 줄어 편향이 줄어든 것이다.
  → **가우시안 + 선형 배경**을 FSDP 구간에 피팅해 꼭짓점을 얻는다. 편향이 없고
    피팅 공분산에서 불확도도 같이 나온다 (실험 ±0.006, 우리 ±0.015).

  ※ 스플라인으로 하면 안 되나? 종류에 따라 답이 갈린다 (직접 확인):
      보간 스플라인(s=0)  exp 1.510 / BKS 1.606 / 7net 1.616  ← 잡음을 그대로 따라가 편향 잔존
      평활 s=0.3Nσ²      1.501 / 1.617 / 1.620
      평활 s=1.0Nσ²      1.493 / 1.589 / 1.588   ← **가우시안과 일치**
      평활 s=3.0Nσ²      1.502 / 1.607 / 1.609
      가우시안 피팅       1.492 / 1.593 / 1.590
    평활도 s 를 고를 원칙이 없어 0.03(가우시안 불확도의 2배)이나 흔들린다.
    다만 s 를 통계적으로 정당한 값(잔차제곱합 ≈ Nσ²)으로 잡으면 가우시안과 수렴한다
    → 서로 독립인 두 방법이 만나므로 가우시안 결과를 믿을 근거가 된다.
    어느 방법이든 우리 1.59~1.62 / 실험 1.49~1.51 이라 **+6 % 결론은 불변**이다.

★ 왜 sq_direct(절단 없음) 를 쓰나
  g(r)→FT 경로(`sq_analyze.py`)는 박스가 30.4 Å 이라 r 을 15 Å 에서 자르고 Lorch 창을
  곱해야 해서 **피크를 뭉갠다**. 실험 곡선엔 그 처리가 없으니 겹치면 불공정하다.
  두 경로의 FSDP 위치는 0.3 % 안에서 일치했다 → 창은 폭·높이만 건드린다는 확인.

⚠ 한계
  · q 는 원리적으로 2π/L = 0.207 Å⁻¹ 간격으로만 존재한다. 껍질 폭 0.10 은 그 절반이라
    이미 충분히 조밀하다. **더 좁히면 껍질당 표본이 줄어 잡음만 커진다.**
  · 음영 = 껍질 안 q 벡터들의 표준오차. **불확도의 하한**이다 —
    3 ps 안의 31 프레임은 서로 독립이 아니어서 실제 불확도는 이보다 크다.
  · 실험 곡선은 논문 그림 digitize. 고k(>14) 평균 0.985 → 계통오차 약 1.5 %.
    실험 곡선 자체가 원 측정치(오차막대 붙은 점)의 **스플라인 피팅**이라 매끈한 것이지,
    날 데이터가 우리보다 깨끗한 게 아니다.
"""
from pathlib import Path

import numpy as np
from scipy.optimize import curve_fit
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator

ROOT = Path(__file__).resolve().parents[2]
FIG = ROOT / "04_analysis/fig"; FIG.mkdir(exist_ok=True)

QMAX_PLOT = 10.0        # sq_direct.py 의 qmax 와 맞출 것 (그 이상은 데이터가 없다)

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


FIT_LO, FIT_HI = 1.05, 2.15


def gmodel(x, A, q0, w, c0, c1):
    return A * np.exp(-0.5 * ((x - q0) / w)**2) + c0 + c1 * (x - 1.6)


def peak(q, s, lo=FIT_LO, hi=FIT_HI):
    """가우시안 + 선형 배경 피팅으로 FSDP 위치·높이. 최댓값은 위로 편향돼 못 쓴다.

    반환: (q0, sigma_q0, S(q0), 피팅 파라미터, 잔차 RMS)
    잔차 RMS 는 SEM 과 비교해 **밴드가 정직한 크기인지** 확인하는 데 쓴다
    (실측: 잔차 0.041 vs SEM 0.035 → 20 % 안에서 일치, 밴드가 실제 요동을 대표한다).
    """
    m = (q > lo) & (q < hi) & np.isfinite(s)
    qq, ss = q[m], s[m]
    p0 = [ss.max() - ss.min(), qq[np.argmax(ss)], 0.25, ss.min(), 0.0]
    p, cov = curve_fit(gmodel, qq, ss, p0=p0, maxfev=200000)
    res = float(np.sqrt(((ss - gmodel(qq, *p))**2).mean()))
    return p[1], float(np.sqrt(np.diag(cov))[1]), float(gmodel(p[1], *p)), p, res


SET = [("Neutron diffraction (exp.)", "k", exp[:, 0], exp[:, 1], None, 1.9),
       ("BKS", "tab:blue", bks[:, 0], bks[:, 1], bks[:, 2], 1.3),
       ("7net-Nano-4.5", "tab:red", net[:, 0], net[:, 1], net[:, 2], 1.3)]
pk = {lab: peak(q, s) for lab, _, q, s, _, _ in SET}
qe = pk["Neutron diffraction (exp.)"][0]
QFIT = np.linspace(FIT_LO, FIT_HI, 400)

fig, ax = plt.subplots(1, 2, figsize=(7.8, 3.5),
                       gridspec_kw={"width_ratios": [1.6, 1]})
a, b = ax


def draw(axis, mode="raw"):
    """mode="raw"  : 데이터 꺾은선 + SEM 밴드  (패널 a)
       mode="fit"  : 데이터는 점, **FSDP 를 실제로 뽑은 가우시안 피팅**이 굵은 곡선 (패널 b)

    ★ 매끄러운 곡선을 그리려고 평활 스플라인·Savitzky-Golay 를 시도했으나 **둘 다 쓰면 안 된다.**
      평활 스플라인은 곡률에 벌점을 매기는데 진짜 뾰족한 피크도 곡률이 커서
      같이 깎인다 (s=N 에서 진폭 −4 %, s=2N 에서 −14 %).
      SG 는 창 5 에서 잡음을 10 % 밖에 못 줄이고, 창 9 부터 피크가 −6 % 다.
      → 삐쭉거림은 표시 문제가 아니라 **실제 통계 요동**이다. 매끄럽게 만들면
        없는 정밀도를 그리는 셈이라, 정량 주장을 하는 FSDP 구간에서만 피팅을 보인다.
    """
    for lab, c, q, s, e, lw in SET:
        z = 4 if c == "k" else 3
        if e is not None:
            ok = np.isfinite(e)
            axis.fill_between(q[ok], (s - e)[ok], (s + e)[ok],
                              color=c, alpha=0.28, lw=0, zorder=z - 1)
        if mode == "raw" or c == "k":
            axis.plot(q, s, "-", c=c, lw=lw, label=lab, zorder=z)
        else:
            m = (q > FIT_LO - 0.15) & (q < FIT_HI + 0.15)
            axis.plot(q[m], s[m], "o", ms=3.2, mfc="w", mec=c, mew=0.9,
                      alpha=0.9, zorder=z)
            axis.plot(QFIT, gmodel(QFIT, *pk[lab][3]), "-", c=c, lw=1.9, zorder=z + 1)


# ---------- (a) 전 구간 ----------
draw(a, "raw")
a.axhline(1, ls=":", lw=0.8, c="0.6", zorder=1)
a.set_xlim(0, QMAX_PLOT); a.set_ylim(0.0, 2)
a.set_xlabel(r"$q$ ($\rm\AA^{-1}$)"); a.set_ylabel(r"$S_{\rm N}(q)$")
a.legend(loc="upper right", framealpha=0.92, fontsize=8.5,
         handlelength=1.6, borderpad=0.4, labelspacing=0.35)
a.text(0.025, 0.955, "(a)", transform=a.transAxes, fontsize=11.5, fontweight="bold", ha='left', va='top')
# FSDP 를 화살표로 지시
a.annotate("FSDP", xy=(qe+0.1, 1.44), xytext=(qe+0.4, 1.7),
           fontsize=9, ha="center", va="bottom", color="0.15",
           arrowprops=dict(arrowstyle="->", lw=1.1, color="0.15"))

# ---------- (b) FSDP 확대 ----------
draw(b, "fit")
for lab, c, *_ in SET:
    qp, _, sp = pk[lab][:3]
    b.plot([qp], [sp], "o", ms=7, mfc=c, mec="w", mew=1.5, zorder=6)
    b.axvline(qp, ls=":", lw=1.0, c=c, alpha=0.85, zorder=1)
b.set_xlim(1.05, 2.15); b.set_ylim(0.80, 2.02)
b.set_xlabel(r"$q$ ($\rm\AA^{-1}$)")
b.set_title("FSDP", fontsize=10)
b.text(0.955, 0.955, "(b)", transform=b.transAxes, fontsize=11.5,
       fontweight="bold", ha="right", va="top")

b.text(0.05, 0.955, r"$q_{\rm FSDP}$ ($\rm\AA^{-1}$)", transform=b.transAxes,
       fontsize=7.5, ha="left", va="top", color="0.15")
for j, (nm, c, lab) in enumerate([("exp.", "k", SET[0][0]),
                                  ("BKS", "tab:blue", "BKS"),
                                  ("7net-Nano-4.5", "tab:red", "7net-Nano-4.5")]):
    qp = pk[lab][0]
    txt = f"{nm}: {qp:.2f}" + ("" if j == 0 else f"   ({100*(qp/qe-1):+.0f} %)")
    b.text(0.05, 0.955 - 0.082 * (j + 1), txt, transform=b.transAxes,
           fontsize=7.5, ha="left", va="top", color=c,
           fontweight="bold" if j else "normal")

for a_ in ax:
    a_.xaxis.set_minor_locator(AutoMinorLocator(2))
    a_.yaxis.set_minor_locator(AutoMinorLocator(2))

fig.suptitle("Neutron structure factor of a-SiO$_2$ at 300 K  "
             "(exp.: Zeidler $et\\ al.$, PRL $\\bf 113$, 135501 (2014))",
             fontsize=10, y=0.995)
fig.tight_layout(rect=[0, 0, 1, 0.965])
fig.savefig(FIG / "fig_sq.png", dpi=300)
print(f"-> {FIG}/fig_sq.png\n")

print(f"{'':28s}{'q_FSDP':>9s}{'±':>7s}{'vs exp':>9s}{'S_peak':>9s}{'vs exp':>9s}")
se = pk[SET[0][0]][2]
for lab, _, q, s, e, _ in SET:
    q0, e0, s0, _, res = pk[lab]
    sem = np.nanmedian(e) if e is not None else np.nan
    extra = f"   잔차 {res:.4f} vs SEM {sem:.4f}" if e is not None else f"   잔차 {res:.4f}"
    print(f"{lab:28s}{q0:9.3f}{e0:7.3f}{100*(q0/qe-1):+8.1f}%{s0:9.3f}{100*(s0/se-1):+8.1f}%{extra}")
