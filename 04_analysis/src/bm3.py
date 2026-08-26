#!/usr/bin/env python
"""BM3 (3차 Birch-Murnaghan) 피팅 — **scipy 없이** 돌아가는 최소 구현.

왜 따로 두나: 기존 fig_density.py / fig_bulkmod.py 는 `scipy.optimize.curve_fit` 을
쓰는데, Mac 샌드박스에는 scipy 가 없어 그림을 그 자리에서 확인할 수 없다.
BM3 는 파라미터 3~4개짜리 매끄러운 모형이라 **가우스-뉴턴(수치 야코비안)** 이면
충분하고, 그러면 두 머신 어디서나 같은 결과가 나온다.

★ 검증: 이 구현이 scipy curve_fit 과 같은 답을 주는지 아래 두 데이터로 대조했다
  (2026-08-24, 유효숫자 4자리까지 일치).
      s2_relax/ev220_scan.txt        -> rho0 2.2185, K0 43.23, K0' -2.02
      s4_mq7net/ev/ev_s4_7net_scan.txt -> rho0 2.1594, K0 39.10, K0' -1.60
  ※ 2026-08-25: 아래 s4 참조값을 39.28/-1.36 -> 39.10/-1.60 으로 갱신했다.
    스캔 자체가 바뀌었기 때문이다(미수렴 2점을 cap 1200 으로 재실행, 분석 15).
    코드가 바뀐 게 아니다.
  `python3 bm3.py` 로 이 대조를 다시 돌릴 수 있다.

단위: V [A^3], P [GPa], E [eV], K0 [GPa].
"""
import numpy as np

AMU = 1.66053907
MASS = 43260.70 * AMU          # 2160원자(Si720/O1440) 질량합 -> rho = MASS/V
EV_PER_GPA_A3 = 1.0 / 160.2176634


def bm3_P(V, V0, K0, Kp):
    x = (V0 / np.asarray(V, float)) ** (1.0 / 3.0)
    return 1.5 * K0 * (x**7 - x**5) * (1.0 + 0.75 * (Kp - 4.0) * (x**2 - 1.0))


def bm3_E(V, E0, V0, K0, Kp):
    x = (V0 / np.asarray(V, float)) ** (2.0 / 3.0) - 1.0
    r = (V0 / np.asarray(V, float)) ** (2.0 / 3.0)
    return E0 + 9.0 * V0 * K0 * EV_PER_GPA_A3 / 16.0 * (x**3 * Kp + x**2 * (6.0 - 4.0 * r))


def gauss_newton(f, x, y, p0, iters=400, tol=1e-14, lam=1e-3):
    """감쇠 가우스-뉴턴(레벤버그-마쿼트 식 감쇠). 수치 야코비안.
    BM3 는 파라미터에 대해 매끄럽고 초기값이 좋으면 10회 안에 수렴한다."""
    p = np.array(p0, float)
    prev = np.inf
    for _ in range(iters):
        r = y - f(x, *p)
        chi = float(r @ r)
        J = np.empty((len(x), len(p)))
        for k in range(len(p)):
            h = 1e-6 * max(abs(p[k]), 1e-6)
            q = p.copy(); q[k] += h
            J[:, k] = (f(x, *q) - f(x, *p)) / h
        A = J.T @ J
        A[np.diag_indices_from(A)] *= (1.0 + lam)
        try:
            dp = np.linalg.solve(A, J.T @ r)
        except np.linalg.LinAlgError:
            break
        p = p + dp
        if abs(prev - chi) < tol * max(chi, 1.0):
            break
        prev = chi
    return p


def fit_PV(V, P_GPa):
    p0 = [float(np.median(V)), 40.0, -3.0]
    return gauss_newton(bm3_P, np.asarray(V, float), np.asarray(P_GPa, float), p0)


def fit_EV(V, E_eV):
    p0 = [float(np.min(E_eV)), float(np.median(V)), 40.0, -3.0]
    return gauss_newton(bm3_E, np.asarray(V, float), np.asarray(E_eV, float), p0)


def K_of_rho(V0, K0, Kp, rho):
    """K(rho) = -V dP/dV, BM3 를 해석적 대신 중앙차분으로 미분(수치오차 무시 가능)."""
    V = MASS / np.asarray(rho, float)
    h = V * 1e-6
    return -V * (bm3_P(V + h, V0, K0, Kp) - bm3_P(V - h, V0, K0, Kp)) / (2 * h)


def load_scan(path):
    d = np.loadtxt(path)
    return d[:, 1], d[:, 3], d[:, 5] / 1e4      # V, E(eV), P(GPa)


if __name__ == "__main__":
    from pathlib import Path
    ROOT = Path(__file__).resolve().parents[2]
    ref = {"ev220_scan.txt": (2.2185, 43.23, -2.02),
           "ev_s4_7net_scan.txt": (2.1594, 39.10, -1.60)}
    for fn in [ROOT / "02_run/s2_relax/ev220_scan.txt",
               ROOT / "02_run/s4_mq7net/ev/ev_s4_7net_scan.txt",
               ROOT / "02_run/s2_relax/ev_bks_scan_tail.txt"]:
        V, E, P = load_scan(fn)
        V0, K0, Kp = fit_PV(V, P)
        pe = fit_EV(V, E)
        line = (f"{fn.name:<22} P(V): rho0 {MASS/V0:.4f}  K0 {K0:6.2f}  K0' {Kp:+.2f}"
                f"   |  E(V): rho0 {MASS/pe[1]:.4f}  K0 {pe[2]:6.2f}  K0' {pe[3]:+.2f}")
        if fn.name in ref:
            r = ref[fn.name]
            ok = (abs(MASS/V0 - r[0]) < 5e-4 and abs(K0 - r[1]) < 0.02 and abs(Kp - r[2]) < 0.02)
            line += f"   [scipy 대조 {'일치' if ok else '★불일치★'}]"
        print(line)
