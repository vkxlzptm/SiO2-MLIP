#!/usr/bin/env python
"""dump 궤적 → 부분 g_ab(r) (r ≤ 15 Å) → 중성자 가중 S(q). **원격에서 실행.**

왜 별도 스크립트인가
    traj_analyze.py 는 결합길이·결합각용이라 RMAX = 8 Å 이다. 중거리 구조 지표인
    FSDP(~1.5 Å⁻¹)를 보려면 r 을 더 멀리 봐야 하고(2π/1.5 ≈ 4 Å 주기의 상관을
    여러 주기 담아야 함), 정규화·가중도 다르다. 기존 출력을 건드리지 않으려고 분리했다.

사용:
    cd ~/projects/lammps_tutorial/SiO2-MLIP/02_run/s3_md
    python ../../04_analysis/src/sq_analyze.py traj_7net220.lammpstrj 7net220
    cd ../s0_requench
    python ../../04_analysis/src/sq_analyze.py traj_bks220.lammpstrj bks220

출력 (작은 텍스트 파일이라 sync 해도 됨):
    <접두사>_gr15.dat   r, g_SiO, g_OO, g_SiSi, g_total(중성자 가중)
    <접두사>_sq.dat     q, S_N(q)

⚠ 한계 두 가지 — 그림·문서에 반드시 같이 적을 것
  1. **r 절단이 15 Å 이다.** 박스가 30.4 Å 이라 minimum image 로 갈 수 있는 최대가
     절반인 15.2 Å 이다. FT 의 q 해상도는 Δq ≈ 2π/R_max ≈ 0.42 Å⁻¹ 이므로
     **FSDP 의 위치는 읽을 수 있어도 폭·높이는 뭉개진다.** 위치만 인용할 것.
  2. 절단 리플을 줄이려고 Lorch 창을 곱한다. 이것도 피크를 넓히므로 같은 이유로
     진폭 비교는 하지 말 것.

⚠ 중성자 산란길이는 문헌값이다 (Sears, Neutron News 3, 26 (1992) 로 알려진 표).
  출처 조사 때 확인할 것. 값이 조금 달라져도 **FSDP 위치는 거의 안 움직인다**
  (가중치는 세 부분함수의 배합비만 바꾸므로).
"""
import sys
import numpy as np

TYPE_O, TYPE_SI = 1, 2
B_O, B_SI = 5.803, 4.1491        # fm, 중성자 결맞음 산란길이
RMAX, DR = 15.0, 0.02
QMIN, QMAX, DQ = 0.5, 12.0, 0.02


def read_dump(path):
    """xs ys zs (스케일 좌표) dump 를 프레임 단위로. traj_analyze.py 와 동일 규약."""
    with open(path) as f:
        while True:
            line = f.readline()
            if not line:
                return
            if not line.startswith("ITEM: TIMESTEP"):
                continue
            f.readline(); f.readline()
            n = int(f.readline())
            f.readline()
            L = np.empty(3)
            for k in range(3):
                lo, hi = map(float, f.readline().split()[:2])
                L[k] = hi - lo
            cols = f.readline().split()[2:]
            ix = {c: i for i, c in enumerate(cols)}
            arr = np.array([f.readline().split() for _ in range(n)], dtype=float)
            typ = arr[:, ix["type"]].astype(int)
            s = arr[:, [ix["xs"], ix["ys"], ix["zs"]]]
            yield typ, s * L, L


def main(path, prefix):
    nb = int(RMAX / DR)
    edges = np.linspace(0.0, RMAX, nb + 1)
    r = 0.5 * (edges[:-1] + edges[1:])
    h = {"SiO": np.zeros(nb), "OO": np.zeros(nb), "SiSi": np.zeros(nb)}
    nframe, Vsum = 0, 0.0
    nO = nSi = 0

    for typ, pos, L in read_dump(path):
        if RMAX > 0.5 * L.min() + 1e-9:
            sys.exit(f"RMAX {RMAX} > half-box {0.5*L.min():.3f} — minimum image 불가")
        nframe += 1
        Vsum += float(np.prod(L))
        O = np.where(typ == TYPE_O)[0]
        Si = np.where(typ == TYPE_SI)[0]
        nO, nSi = len(O), len(Si)

        for i in Si:                                   # Si 중심: Si-O, Si-Si
            d = pos - pos[i]
            d -= L * np.round(d / L)
            rr = np.linalg.norm(d, axis=1)
            h["SiO"] += np.histogram(rr[O], bins=edges)[0]
            s = rr[Si]
            h["SiSi"] += np.histogram(s[s > 1e-8], bins=edges)[0]
        for i in O:                                    # O 중심: O-O
            d = pos - pos[i]
            d -= L * np.round(d / L)
            rr = np.linalg.norm(d[O], axis=1)
            h["OO"] += np.histogram(rr[rr > 1e-8], bins=edges)[0]

    V = Vsum / nframe
    N = nO + nSi
    rho0 = N / V                                        # 전체 수밀도
    shell = 4.0 * np.pi * r**2 * DR

    # 부분 g_ab: 중심원자 수 × 상대종 수밀도 × 껍질부피 로 나눈다 → 큰 r 에서 1 로 감.
    #   Si-O 는 Si 중심으로만 셌으므로 중심 수가 nSi. 동종쌍은 순서쌍으로 셌다.
    g = {"SiO":  h["SiO"] / (nframe * nSi * (nO / V) * shell),
         "OO":   h["OO"] / (nframe * nO * (nO / V) * shell),
         "SiSi": h["SiSi"] / (nframe * nSi * (nSi / V) * shell)}

    # ---- Faber-Ziman 중성자 가중 ----
    cO, cSi = nO / N, nSi / N
    bbar = cO * B_O + cSi * B_SI
    w = {"OO":   cO * cO * B_O * B_O / bbar**2,
         "SiSi": cSi * cSi * B_SI * B_SI / bbar**2,
         "SiO":  2.0 * cO * cSi * B_O * B_SI / bbar**2}   # 2× : ab 와 ba
    assert abs(sum(w.values()) - 1.0) < 1e-9

    g_tot = sum(w[k] * g[k] for k in g)                  # 큰 r 에서 1 로 감

    # ---- S(q): Lorch 창으로 절단 리플 억제 ----
    lorch = np.sinc(r / RMAX)                            # np.sinc(x) = sin(pi x)/(pi x)
    q = np.arange(QMIN, QMAX + 1e-9, DQ)
    integ = r * (g_tot - 1.0) * lorch * DR
    Sq = 1.0 + (4.0 * np.pi * rho0 / q) * (np.sin(np.outer(q, r)) @ integ)

    np.savetxt(f"{prefix}_gr15.dat",
               np.column_stack([r, g["SiO"], g["OO"], g["SiSi"], g_tot]),
               header=f"frames {nframe}  V {V:.3f}  rho0 {rho0:.6f}  "
                      f"nO {nO} nSi {nSi}\nr  g_SiO  g_OO  g_SiSi  g_total(neutron)")
    np.savetxt(f"{prefix}_sq.dat", np.column_stack([q, Sq]),
               header=f"frames {nframe}  rho0 {rho0:.6f}  RMAX {RMAX}  Lorch window\nq(1/A)  S_N(q)")

    m = (q > 1.0) & (q < 2.2)
    i = np.argmax(Sq[m])
    print(f"{prefix}: {nframe} frames, V {V:.1f} A^3, rho0 {rho0:.5f} /A^3")
    print(f"  g_total 꼬리 (r 13-15 A) 평균 {g_tot[r > 13].mean():.4f}  (1 이어야 정상)")
    print(f"  FSDP: q = {q[m][i]:.3f} A^-1,  S = {Sq[m][i]:.3f}   (실험 ~1.52)")
    print(f"  -> {prefix}_gr15.dat, {prefix}_sq.dat")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
