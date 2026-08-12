#!/usr/bin/env python
"""Dechant JPCC 2026 Fig. 4(b) — Si-O-Si 결합각 분포를 색 분리로 자동 digitize.

논문 그림은 y축 눈금값이 없다. 그래서 **면적 규격화**로 비교한다:
결합각 분포는 ∫P(θ)dθ = 1 이므로, 임의 스케일로 뽑아 면적으로 나누면
우리 데이터(traj_analyze.py 출력, 이미 density=True)와 직접 겹칠 수 있다.

축 보정 (오른쪽 패널, 픽셀):
  x tick  col 67.5=40°, 190=80°, 312.5=120°, 435=160°   (0.32653 deg/px)
  y=0     row 280 (축선).  y 스케일은 임의 → 면적 규격화로 흡수.
"""
import numpy as np
from PIL import Image

IMG = "../05_doc/dechant_figs/p3_img1.png"
COL0, ANG0, DEGPX = 67.5, 40.0, (160 - 40) / (435 - 67.5)
ROW0 = 280.0           # y = 0
TOP = 28.0             # 박스 위쪽 (클리핑용)


def extract(mask, name):
    """열마다 곡선 픽셀의 중앙 행 → (angle, height_px)."""
    xs, ys = [], []
    for c in range(int(COL0), 497):
        rows = np.where(mask[:, c])[0]
        rows = rows[(rows > TOP) & (rows < ROW0)]
        if len(rows) == 0:
            continue
        xs.append(ANG0 + (c - COL0) * DEGPX)
        ys.append(ROW0 - rows.mean())        # 위로 갈수록 큰 값
    xs, ys = np.array(xs), np.array(ys)
    print(f"  {name}: {len(xs)}개 열에서 검출, θ = {xs.min():.1f}~{xs.max():.1f}°")
    return xs, ys


im = np.array(Image.open(IMG).convert("RGB")).astype(int)
right = im[:, im.shape[1] // 2:]
r, g, b = right[:, :, 0], right[:, :, 1], right[:, :, 2]
green = (g > 90) & (g > r + 40) & (g > b + 40)      # LES (녹색 점선)
red = (r > 120) & (r > g + 50) & (r > b + 50)       # HES (빨간 실선)

# 범례(좌상단 rows<105, cols<270)를 곡선으로 오인하지 않도록 제거.
# 그 영역은 θ < 100° 에 해당해 실제 Si-O-Si 분포가 존재할 수 없는 구간이기도 하다.
for m in (green, red):
    m[:105, :270] = False

print("digitize:")
xg, yg = extract(green, "LES (녹색 점선)")
xr, yr = extract(red, "HES (빨간 실선)")

# 점선 gap 을 1° 격자로 보간 후 면적 규격화
grid = np.arange(100.0, 180.1, 1.0)
out = [grid]
for x, y, nm in [(xg, yg, "LES"), (xr, yr, "HES")]:
    yi = np.interp(grid, x, y, left=0.0, right=0.0)
    yi = np.clip(yi, 0, None)
    yi /= np.trapezoid(yi, grid)
    out.append(yi)
    mean = np.trapezoid(grid * yi, grid)
    print(f"  {nm}  면적규격화 후 평균각 = {mean:.2f}°   피크 {grid[np.argmax(yi)]:.0f}°")

np.savetxt("dechant_bad_digitized.dat", np.c_[tuple(out)],
           header="angle(deg)  P_LES  P_HES   [Dechant JPCC 2026 Fig.4b, 색분리 digitize, 면적규격화]")
print("-> dechant_bad_digitized.dat")
print("\n※ 논문 Table 1 의 average Si-O-Si = 138.5° 와 위 LES 평균을 대조해 digitize 품질을 검증할 것.")
