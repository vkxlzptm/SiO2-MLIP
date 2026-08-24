#!/usr/bin/env python
"""S4 E-V 결과 요약 — 밀도·체적탄성률에서의 **위상 형성 효과**.

세 구조를 같은 자(0 K E-V 스캔 + BM3)로 재서 비교한다:
  1) BKS 가 만든 망 위에서 BKS 가 읽은 값        (s2_relax/ev_bks_scan_tail.txt)
  2) BKS 가 만든 망 위에서 7net 이 읽은 값        (s2_relax/ev220_scan.txt)   <- 기존 보고값
  3) 7net 이 **자기 힘으로 만든** 망에서 7net     (s4_mq7net/ev/ev_s4_7net_scan.txt)
(2)->(3) 의 차이가 위상 형성 효과다. 포텐셜은 같고 망만 다르다.

★ K 는 반드시 **같은 밀도에서** 비교한다. RESULTS 2절의 함정 — 각자의 평형에서 읽은 K0 를
  나란히 놓으면 V0 의 오차와 K(V) 의 오차가 섞인다. 실리카는 K0' < 0 이라 조밀할수록
  무르므로 두 오차가 상쇄되는 방향이고, 그래서 함정이 유독 깊다.

출력: 04_analysis/dat/ev_s4_summary.dat
"""
import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from bm3 import MASS, fit_PV, fit_EV, K_of_rho, load_scan   # noqa: E402

K_EXP, RHO_EXP = 37.0, 2.20        # Deschamps 2014 / Yokoyama 2010 · fused silica

# (reader potential, network maker, quench rate, file)
# 없는 파일은 조용히 건너뛴다 — 계산이 순차적으로 들어오므로.
SET_ALL = [
    ("BKS  / BKS net 5e12",  "02_run/s2_relax/ev_bks_scan_tail.txt"),
    ("BKS  / BKS net 2e13",  "02_run/s4_mq7net/ev/ev_s4_bks2e13_scan.txt"),
    ("7net / BKS net 5e12",  "02_run/s2_relax/ev220_scan.txt"),
    ("7net / BKS net 2e13",  "02_run/s4_mq7net/ev/ev_s4_bksnet2e13_scan.txt"),
    ("7net / OWN net 2e13",  "02_run/s4_mq7net/ev/ev_s4_7net_scan.txt"),
]
SET = [(lab, fn) for lab, fn in SET_ALL if (ROOT / fn).exists()]
MISSING = [lab for lab, fn in SET_ALL if not (ROOT / fn).exists()]
GRID = [2.0762, 2.1595, 2.2000, 2.2185, 2.2500, 2.3000, 2.3442]

out, fits = [], {}
w = out.append
w("# S4 E-V summary — BM3 fits (bm3.py, scipy-free; scipy 대조 검증됨)")
w(f"# experiment: rho = {RHO_EXP} g/cc, K = {K_EXP} GPa")
w("#")
w(f"# {'structure':<24}{'rho0':>8}{'vs exp':>9}{'K0':>8}{'vs exp':>9}"
  f"{'K@2.20':>9}{'vs exp':>9}{'K0p':>7}{'Pres(bar)':>11}")
for lab, fn in SET:
    V, E, P = load_scan(ROOT / fn)
    V0, K0, Kp = fit_PV(V, P)
    fits[lab] = (V0, K0, Kp)
    r0 = MASS / V0
    k22 = float(K_of_rho(V0, K0, Kp, RHO_EXP))
    from bm3 import bm3_P
    res = (P - bm3_P(V, V0, K0, Kp)) * 1e4
    w(f"{lab:<26}{r0:>8.4f}{100*(r0-RHO_EXP)/RHO_EXP:>+8.2f}%{K0:>8.2f}"
      f"{100*(K0-K_EXP)/K_EXP:>+8.1f}%{k22:>9.2f}{100*(k22-K_EXP)/K_EXP:>+8.1f}%"
      f"{Kp:>7.2f}{np.sqrt((res**2).mean()):>11.0f}")

w("#")
w("# K(rho) — same-density comparison (the only fair one)")
w(f"# {'rho':>7}" + "".join(f"{lab:>24}" for lab, _ in SET))
for rho in GRID:
    w(f"{rho:>9.4f}" + "".join(f"{float(K_of_rho(*fits[lab], rho)):>24.2f}" for lab, _ in SET))

w("#")


def delta(w, title, k_from, k_to, note=""):
    """두 행의 차이. 같은 reader 포텐셜끼리만 뺄 것 —
    7net 행과 BKS 행은 minimize 상한이 달라(150 vs 20000 eval) 직접 빼면 안 된다."""
    if k_from not in fits or k_to not in fits:
        w(f"# {title}: 자료 부족 ({k_from} 또는 {k_to} 미실행)")
        return
    a, b = fits[k_from], fits[k_to]
    ra, rb = MASS / a[0], MASS / b[0]
    ka = float(K_of_rho(*a, RHO_EXP)); kb = float(K_of_rho(*b, RHO_EXP))
    w(f"# {title}")
    if note:
        w(f"#   {note}")
    w(f"#   {k_from}  ->  {k_to}")
    w(f"#   rho0   : {ra:.4f} -> {rb:.4f}  ({rb-ra:+.4f} g/cc, {100*(rb-ra)/ra:+.2f} %)"
      f"   |  vs exp {100*(ra-RHO_EXP)/RHO_EXP:+.2f} % -> {100*(rb-RHO_EXP)/RHO_EXP:+.2f} %")
    w(f"#   K@2.20 : {ka:.2f} -> {kb:.2f} GPa ({kb-ka:+.2f}, {100*(kb-ka)/ka:+.1f} %)"
      f"   |  vs exp {100*(ka-K_EXP)/K_EXP:+.1f} % -> {100*(kb-K_EXP)/K_EXP:+.1f} %")
    if (ka - K_EXP) != 0:
        w(f"#   K 간극 중 사라진 비율: {100*(1-(kb-K_EXP)/(ka-K_EXP)):.0f} %")
    w("#")


# 냉각률 효과와 위상 형성 효과를 **분리**한다. 둘 다 reader 는 7net 으로 고정.
delta(w, "[A] QUENCH-RATE EFFECT  (BKS 가 만든 망, 5e12 -> 2e13, 읽는 건 7net)",
      "7net / BKS net 5e12", "7net / BKS net 2e13",
      "망 생성자는 BKS 로 같고 냉각률만 4배 다르다 -> 순수 냉각률 효과")
delta(w, "[B] TOPOLOGY-FORMATION EFFECT  (냉각률 2e13 고정, 망 생성자 BKS -> 7net)",
      "7net / BKS net 2e13", "7net / OWN net 2e13",
      "★ 냉각률까지 맞춘 순수 위상 효과. 이게 최종 수치다.")
delta(w, "[B'] (임시) 냉각률 미매칭 위상 효과 — [A] 가 나오기 전까지의 근사",
      "7net / BKS net 5e12", "7net / OWN net 2e13",
      "냉각률 4배 차이가 섞여 있다. [B] 가 나오면 폐기할 것.")
if MISSING:
    w("# 미실행: " + ", ".join(MISSING))

txt = "\n".join(out) + "\n"
(ROOT / "04_analysis/dat/ev_s4_summary.dat").write_text(txt)
print(txt)
print(f"-> 04_analysis/dat/ev_s4_summary.dat")
