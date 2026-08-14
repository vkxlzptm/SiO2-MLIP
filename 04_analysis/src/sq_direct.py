#!/usr/bin/env python
"""원자 좌표에서 S(q) 직접 계산 (중성자 가중). **원격에서 실행.**

왜 sq_analyze.py 와 따로 만드나
    sq_analyze.py 는 g(r) → 푸리에 변환 경로다. 박스가 30.4 Å 라 r 을 15 Å 에서 잘라야 하고,
    절단 리플을 막으려 Lorch 창까지 곱한다. 그 결과 **피크가 인위적으로 넓어지고 낮아진다.**
    실험 곡선(Zeidler PRL 2014)은 그런 처리가 없으므로 그대로 겹쳐 그리면 불공정하다.

    주기 셀에서는 셀에 정합하는 이산 q 벡터에 대해 S(q) 를 **직접** 계산할 수 있다.
    절단도 창도 없다:

        S(q) = 1 + [ <|sum_j b_j exp(i q.r_j)|^2>/N - <b^2> ] / <b>^2

    큰 q 에서 교차항이 사라져 S → 1 이 된다 (Faber-Ziman 규약, sq_analyze.py 와 동일).
    → 두 경로를 비교하면 **Lorch 창이 얼마나 뭉갰는지**가 그대로 드러난다. 서로 검산이 된다.

한계
    q 는 2π/L = 0.207 Å⁻¹ 간격으로만 존재한다. 껍질 평균으로 매끄럽게 만들지만
    **그보다 가는 구조는 원리적으로 못 본다.** FSDP 폭(FWHM ~0.7)은 3~4 껍질로 샘플된다.

사용:
    cd ~/projects/lammps_tutorial/SiO2-MLIP/02_run/s3_md
    python ../../04_analysis/src/sq_direct.py traj_7net220.lammpstrj 7net220
    cd ../s0_requench
    python ../../04_analysis/src/sq_direct.py traj_bks220.lammpstrj bks220

옵션: 3번째 인자 = 프레임 간격(기본 5), 4번째 = q_max(기본 10.0)
출력: <접두사>_sqd.dat   (q, S_N(q), 껍질당 q벡터 수)
"""
import sys
import numpy as np

TYPE_O, TYPE_SI = 1, 2
B = {TYPE_O: 5.803, TYPE_SI: 4.1491}     # fm (Sears 1992 로 알려진 표)
# 껍질 폭 0.10 — **좁힐수록 좋아지는 게 아니다.**
#   q 는 원리적으로 2π/L = 0.207 Å⁻¹ 간격으로만 존재한다. 그보다 훨씬 좁은 bin 은
#   있지도 않은 해상도를 흉내 내면서 껍질당 표본만 줄여 **잡음만 키운다.**
#   0.05 로 뽑았더니 FSDP 위치가 추정법에 따라 ±0.02 흔들렸다. 0.10 으로 넓힌다.
DQ_SHELL = 0.10
NMAX_PER_SHELL = 400                     # 껍질당 q벡터 상한 — 큰 q 에서 비용 폭증 방지
CHUNK = 20000


def read_dump(path):
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
            yield arr[:, ix["type"]].astype(int), arr[:, [ix["xs"], ix["ys"], ix["zs"]]] * L, L


def build_q(L, qmax, rng):
    """셀에 정합하는 q 벡터. S(-q)=S(q) 이므로 절반만 쓰고, 껍질당 개수를 제한한다."""
    nmax = np.ceil(qmax * L / (2 * np.pi)).astype(int)
    g = np.stack(np.meshgrid(*[np.arange(-m, m + 1) for m in nmax], indexing="ij"), -1)
    n = g.reshape(-1, 3)
    # 반공간만: 첫 비영 성분이 양수인 것
    keep = (n[:, 0] > 0) | ((n[:, 0] == 0) & (n[:, 1] > 0)) | \
           ((n[:, 0] == 0) & (n[:, 1] == 0) & (n[:, 2] > 0))
    n = n[keep]
    q = 2 * np.pi * n / L
    qm = np.linalg.norm(q, axis=1)
    m = (qm > 1e-9) & (qm <= qmax)
    q, qm = q[m], qm[m]
    # 껍질당 상한 적용 (큰 q 에서 벡터가 q^2 로 늘어나 그대로 두면 비용이 터진다)
    idx = (qm / DQ_SHELL).astype(int)
    sel = []
    for s in np.unique(idx):
        w = np.where(idx == s)[0]
        sel.append(w if len(w) <= NMAX_PER_SHELL
                   else rng.choice(w, NMAX_PER_SHELL, replace=False))
    sel = np.concatenate(sel)
    return q[sel], qm[sel], idx[sel]


def main(path, prefix, stride=5, qmax=10.0):
    rng = np.random.default_rng(0)
    q = qm = shell = None
    acc = None
    nframe = 0
    bvec = None

    for f, (typ, pos, L) in enumerate(read_dump(path)):
        if f % stride:
            continue
        if q is None:
            q, qm, shell = build_q(L, qmax, rng)
            acc = np.zeros(len(q))
            bvec = np.array([B[t] for t in typ])
            N = len(typ)
            cO = np.mean(typ == TYPE_O); cSi = 1 - cO
            b1 = cO * B[TYPE_O] + cSi * B[TYPE_SI]          # <b>
            b2 = cO * B[TYPE_O]**2 + cSi * B[TYPE_SI]**2    # <b^2>
            print(f"  q벡터 {len(q):,}개 (qmax {qmax}, 껍질폭 {DQ_SHELL}, 껍질당 ≤{NMAX_PER_SHELL})")
        nframe += 1
        for c0 in range(0, len(q), CHUNK):
            qc = q[c0:c0 + CHUNK]
            ph = qc @ pos.T                                  # (nq, natom)
            acc[c0:c0 + CHUNK] += (np.cos(ph) @ bvec)**2 + (np.sin(ph) @ bvec)**2

    F = acc / (nframe * N)                                   # <|sum b e^{iqr}|^2>/N
    Sq_vec = 1.0 + (F - b2) / b1**2

    # 껍질 평균 + **표준오차**. 밴드로 그려서 "이만큼이 통계 요동"임을 보이려면 필요하다.
    #   껍질 안 q 벡터들의 S 값 흩어짐 / sqrt(n).  프레임 간 상관 때문에 실제 불확도는
    #   이보다 다소 크지만, 하한으로는 정직한 값이다.
    out = []
    for s in np.unique(shell):
        m = shell == s
        v = Sq_vec[m]
        out.append((qm[m].mean(), v.mean(), v.std(ddof=1) / np.sqrt(m.sum()), m.sum()))
    out = np.array(out)

    np.savetxt(f"{prefix}_sqd.dat", out,
               header=f"frames {nframe} (stride {stride})  N {N}  L {L}  dq_shell {DQ_SHELL}\n"
                      f"직접 계산 (절단·창 없음). q(1/A)  S_N(q)  SEM  n_qvec")

    sel = (out[:, 0] > 1.0) & (out[:, 0] < 2.2)
    qq, ss = out[sel, 0], out[sel, 1]
    i = np.argmax(ss)
    # 꼭짓점 3점 포물선 보간
    if 0 < i < len(qq) - 1:
        d = (ss[i-1] - ss[i+1]) / (2 * (ss[i-1] - 2*ss[i] + ss[i+1]))
        qpk = qq[i] + d * (qq[i+1] - qq[i-1]) / 2
    else:
        qpk = qq[i]
    wide = (out[:, 0] >= 2) & (out[:, 0] <= 10)
    # ※ "q>8 이면 S=1" 은 틀린 기준이다. 실리카 S(q) 는 22 A^-1 까지 진동한다.
    #   제대로 된 검사는 (a) 넓은 구간 평균이 1 인가, (b) g(r) 경로와 일치하는가 두 가지다.
    print(f"{prefix}: {nframe} frames, S(q) 평균(q 2-10) {out[wide, 1].mean():.4f} (1 이어야 정상)")
    print(f"  FSDP: q = {qpk:.3f} A^-1,  S = {ss[i]:.3f}   (실험 ~1.52)")
    print(f"  -> {prefix}_sqd.dat")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2],
         int(sys.argv[3]) if len(sys.argv) > 3 else 5,
         float(sys.argv[4]) if len(sys.argv) > 4 else 10.0)
