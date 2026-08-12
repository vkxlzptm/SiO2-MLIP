#!/usr/bin/env python
"""Dechant JPCC 2026 의 partial PDF (Si-O, O-O, Si-Si) 를 색 분리로 digitize.

y축 눈금값이 없고, 게다가 LES(녹색)는 세로로 offset 되어 그려져 있다.
미지수 2개(offset, scale)를 물리 조건 2개로 결정한다:

  (1) 1피크보다 가까운 구간에서 g(r) = 0      → offset
  (2) 1피크 아래 배위수 = 이론값               → scale
        완전한 corner-sharing SiO4 망:  n(Si-O)=4, n(O-O)=6, n(Si-Si)=4
        n_ab = ∫ 4πr² ρ_b g_ab(r) dr

꼬리(g→1)는 쓰지 않는다. 논문 셀이 12.2 Å이라 **L/2 = 6.1 Å 너머는 최소이미지 밖**이고,
실제로 9 Å에서 수렴한 것처럼 보이지 않는다.

출력: dechant_pdf_digitized.dat  (r, g_SiO, g_OO, g_SiSi ; LES only)
"""
import numpy as np
from PIL import Image

# 논문 계: 120 atoms (40 SiO2), ρ = 2.20 g/cm3
MASS = 40 * (28.0855 + 2 * 15.9994)
V = MASS * 1.66053907 / 2.20
N_SI, N_O = 40, 80
RHO = {"Si": N_SI / V, "O": N_O / V}
print(f"논문 계: V = {V:.1f} A^3 (L = {V**(1/3):.2f} A),  L/2 = {V**(1/3)/2:.2f} A")

# (그림파일, 패널 x범위(전체폭 대비), 쌍, 이론 배위수, 중심원자, 상대원자, 0인 구간, 1피크 적분구간)
PANELS = [
    ("../05_doc/dechant_figs/SI_p4_img0.jpeg", (0.00, 0.50), "Si-O", 4.0, "Si", "O", (1.0, 1.30), (1.30, 2.10)),
    ("../05_doc/dechant_figs/SI_p4_img0.jpeg", (0.50, 1.00), "O-O",  6.0, "O",  "O", (1.0, 2.10), (2.10, 3.30)),
    ("../05_doc/dechant_figs/p3_img2.png",     (0.00, 0.51), "Si-Si", 4.0, "Si", "Si", (1.0, 2.20), (2.20, 3.80)),
]
RMIN, RMAX = 1.0, 9.0          # 세 그림 모두 x축 1~9 Å


def find_box(black):
    """축 프레임: 검은 픽셀이 가장 많은 가로선 2개(위/아래)와 그 선의 좌우 끝."""
    rs = black.sum(1)
    cand = np.where(rs > 0.5 * rs.max())[0]
    # 인접 행 묶어 위/아래 두 그룹
    grp, cur = [], [cand[0]]
    for x in cand[1:]:
        if x - cur[-1] <= 3:
            cur.append(x)
        else:
            grp.append(int(np.mean(cur))); cur = [x]
    grp.append(int(np.mean(cur)))
    r0, r1 = min(grp), max(grp)
    # 위/아래 테두리 중 더 길게 잡히는 쪽을 쓴다 (틱 라벨 때문에 한쪽이 잘릴 수 있음)
    ca = np.where(black[r0])[0]
    cb_ = np.where(black[r1])[0]
    c0 = min(ca.min(), cb_.min()); c1 = max(ca.max(), cb_.max())
    return c0, c1, r0, r1


grid = np.arange(RMIN, RMAX + 1e-9, 0.02)
out = [grid]

for path, (fx0, fx1), pair, cn_ref, ca, cb, zero_rng, peak_rng in PANELS:
    im = np.array(Image.open(path).convert("RGB")).astype(int)
    W = im.shape[1]
    sub = im[:, int(fx0 * W):int(fx1 * W)]
    r_, g_, b_ = sub[:, :, 0], sub[:, :, 1], sub[:, :, 2]
    black = (r_ < 110) & (g_ < 110) & (b_ < 110)
    c0, c1, r0, r1 = find_box(black)
    green = (g_ > 90) & (g_ > r_ + 35) & (g_ > b_ + 35)
    green[: r0 + 3, :] = False
    green[:, : c0] = False; green[:, c1 + 1:] = False

    # ★ 범례가 플롯 박스 **안쪽** 우상단에 있다. 열마다 녹색 픽셀을 세로로 군집화한 뒤
    #   군집이 둘 이상이면 **아래쪽(= g 가 작은 쪽) 군집**을 곡선으로 채택한다.
    #   이 그림들에서 범례는 항상 해당 r 구간의 곡선보다 위에 있다.
    xs, ys, nsplit = [], [], 0
    for c in range(c0, c1 + 1):
        rows = np.where(green[:, c])[0]
        rows = rows[(rows > r0) & (rows <= r1)]
        if len(rows) == 0:
            continue
        cl, cur = [], [rows[0]]
        for x in rows[1:]:
            if x - cur[-1] <= 6:
                cur.append(x)
            else:
                cl.append(cur); cur = [x]
        cl.append(cur)
        if len(cl) > 1:
            nsplit += 1
        sel = cl[-1]                          # 가장 아래 군집
        xs.append(RMIN + (c - c0) / (c1 - c0) * (RMAX - RMIN))
        ys.append(r1 - float(np.mean(sel)))   # 픽셀 높이 (위로 +)
    xs, ys = np.array(xs), np.array(ys)

    # 점선 gap 이 있는 열에서는 범례 조각만 녹색으로 남아 그것이 곡선으로 잡힌다.
    # 국소 중앙값 대비 큰 이상치를 버리고 다시 보간한다 (MAD 기준).
    # ※ 1피크는 진짜로 뾰족하므로 이상치로 오인된다. **꼬리 구간에만** 적용한다.
    keep = np.ones(len(ys), bool)
    W_ = 21
    for i in np.where(xs > peak_rng[1])[0]:
        lo, hi = max(0, i - W_), min(len(ys), i + W_ + 1)
        nb = np.delete(ys[lo:hi], i - lo)
        med = np.median(nb)
        mad = np.median(np.abs(nb - med)) + 1e-9
        if abs(ys[i] - med) > 6 * mad:
            keep[i] = False
    nrej = (~keep).sum()
    xs, ys = xs[keep], ys[keep]

    y = np.interp(grid, xs, ys, left=np.nan, right=np.nan)
    y = np.where(np.isnan(y), np.nanmin(y), y)

    # (1) offset: 1피크 앞 구간 평균
    m0 = (grid >= zero_rng[0]) & (grid < zero_rng[1])
    y = y - y[m0].mean()

    # (2) scale: 두 가지 독립 기준으로 구해 서로 대조한다 (digitize 불확실성의 척도)
    mp = (grid >= peak_rng[0]) & (grid < peak_rng[1])
    dr = grid[1] - grid[0]
    integ = (np.clip(y[mp], 0, None) * 4 * np.pi * grid[mp] ** 2 * dr).sum() * RHO[cb]
    s_cn = cn_ref / integ                       # (a) 1차 배위수 = 이론값
    mt = (grid > 3.5) & (grid < 6.1)            # (b) g -> 1 (L/2=6.1 A 안쪽만)
    s_tail = 1.0 / y[mt].mean()

    g = np.clip(y * s_tail, 0, None)            # 본 곡선은 (b) 기준. g(r) 정의에 충실.
    cn_got = (g[mp] * 4 * np.pi * grid[mp] ** 2 * dr).sum() * RHO[cb]
    pk = grid[mp][np.argmax(g[mp])]
    print(f"{pair:6s} box=({c0},{c1},{r0},{r1})  1피크 {pk:.3f} A  g_max={g[mp].max():6.2f}"
          f"  |  배위수 {cn_got:.2f} (이론 {cn_ref:.0f})"
          f"  두 규격화 비 {s_cn/s_tail:.2f}   군집분리 {nsplit}열, 이상치제거 {nrej}점")
    out.append(g)

np.savetxt("dechant_pdf_digitized.dat", np.c_[tuple(out)],
           header="r(A)  g_SiO  g_OO  g_SiSi   [Dechant JPCC2026 LES, colour-digitized, "
                  "offset=0 below 1st peak, scale set by 1st-shell CN = 4/6/4]")
print("-> dechant_pdf_digitized.dat")
