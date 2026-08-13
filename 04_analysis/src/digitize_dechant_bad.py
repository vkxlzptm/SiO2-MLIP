#!/usr/bin/env python
"""Dechant JPCC 2026 Fig. 4 — 결합각 분포(O-Si-O, Si-O-Si)를 색 분리로 자동 digitize.

논문 그림은 y축 눈금값이 없다. 결합각 분포는 ∫P(θ)dθ = 1 이므로 **면적 규격화**로
우리 데이터(traj_analyze.py 출력, density=True)와 직접 겹칠 수 있다.

축 보정은 아래 축의 안쪽 tick 픽셀 위치에서 자동 검출한다 (라벨 40/80/120/160).
범례가 플롯 박스 안에 있으므로, 열마다 녹색 픽셀을 세로 군집화해 **아래쪽 군집**을 택한다.

검증: LES 평균이 논문 Table 1 의 average Si-O-Si = 138.5°, O-Si-O = 109.4° 와 맞아야 한다.
"""
import numpy as np
from PIL import Image

from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
DAT, FIG = ROOT / "04_analysis/dat", ROOT / "04_analysis/fig"
FIG.mkdir(exist_ok=True); DAT.mkdir(exist_ok=True)

IMG = ROOT / "05_doc/dechant_figs/p3_img1.png"
TICK_DEG = [40.0, 80.0, 120.0, 160.0]
# (패널 슬라이스 비율, 이름, 물리적으로 가능한 각 범위, 논문 Table 1 평균)
PANELS = [((0.00, 0.50), "O-Si-O", (70.0, 150.0), 109.4),
          ((0.50, 1.00), "Si-O-Si", (95.0, 180.0), 138.5)]


def panel_curve(sub, name, arange):
    r, g, b = sub[:, :, 0], sub[:, :, 1], sub[:, :, 2]
    black = (r < 120) & (g < 120) & (b < 120)
    rs = black.sum(1)
    rows = np.where(rs > 0.5 * rs.max())[0]
    r0, r1 = rows.min(), rows.max()

    # 아래 축 안쪽 tick → x 보정
    seg = black[r1 - 8:r1 - 1, :].sum(0)
    tc = np.where(seg >= 6)[0]
    grp, cur = [], [tc[0]]
    for c in tc[1:]:
        (cur.append(c) if c - cur[-1] <= 2
         else (grp.append(int(np.mean(cur))), cur.clear(), cur.append(c)))
    grp.append(int(np.mean(cur)))
    ticks = grp[:len(TICK_DEG)]
    slope = (TICK_DEG[-1] - TICK_DEG[0]) / (ticks[-1] - ticks[0])
    to_deg = lambda c: TICK_DEG[0] + (c - ticks[0]) * slope

    masks = {"LES": (g > 90) & (g > r + 40) & (g > b + 40),
             "HES": (r > 120) & (r > g + 50) & (r > b + 50)}
    out = {}
    for key, m in masks.items():
        xs, ys = [], []
        for c in range(sub.shape[1]):
            rr = np.where(m[:, c])[0]
            rr = rr[(rr > r0) & (rr < r1)]
            if len(rr) == 0:
                continue
            ang = to_deg(c)
            if not (arange[0] <= ang <= arange[1]):     # 범례 영역 등 물리 범위 밖 제거
                continue
            cl, cu = [], [rr[0]]
            for x in rr[1:]:
                (cu.append(x) if x - cu[-1] <= 6
                 else (cl.append(list(cu)), cu.clear(), cu.append(x)))
            cl.append(list(cu))
            xs.append(ang); ys.append(r1 - float(np.mean(cl[-1])))   # 아래쪽 군집
        out[key] = (np.array(xs), np.array(ys))
    return out


im = np.array(Image.open(IMG).convert("RGB")).astype(int)
W = im.shape[1]
grid = np.arange(60.0, 180.1, 1.0)
cols, hdr = [grid], ["angle(deg)"]

for (f0, f1), name, arange, ref in PANELS:
    cur = panel_curve(im[:, int(f0 * W):int(f1 * W)], name, arange)
    print(f"[{name}]")
    for key in ("LES", "HES"):
        xs, ys = cur[key]
        y = np.clip(np.interp(grid, xs, ys, left=0.0, right=0.0), 0, None)
        y /= np.trapezoid(y, grid)
        mean = np.trapezoid(grid * y, grid)
        tag = f"{name}_{key}"
        cols.append(y); hdr.append(tag)
        flag = ""
        if key == "LES":
            flag = f"   <- 논문 Table 1: {ref:.1f}°,  차이 {mean-ref:+.2f}°"
        print(f"  {key}  평균 {mean:7.2f}°  피크 {grid[np.argmax(y)]:5.0f}°"
              f"  검출 {len(xs):3d}열{flag}")

np.savetxt(DAT / "dechant_bad_digitized.dat", np.c_[tuple(cols)],
           header="  ".join(hdr) + "   [Dechant JPCC2026 Fig.4, colour-digitized, area-normalised]")
print(f"-> {DAT}/dechant_bad_digitized.dat")
