#!/usr/bin/env python
"""Zeidler PRL 113, 135501 (2014) Fig. 1(a) ambient 곡선 digitize.

무엇을 뽑나 — **색이 곧 의미다. 헷갈리면 결과가 뒤집힌다.**
    캡션: "solid (black) curves ... give spline fits to the **measured data**"
          "the solid light (red) curves show the **TS MD results**"
    → 검정 = 중성자 회절 **실험**,  빨강 = Tangney-Scandolo 포텐셜 **MD 계산**
    (빨강이 노이즈가 있어 실험처럼 보이지만 반대다. MD 의 S(q) 가 유한 셀 때문에 거친 것.)

★ 빨강(TS MD)은 **뽑지 않는다.** TS 가 실험과 잘 맞아서 빨간 곡선이 검은 곡선 **아래
  깔려 대부분 안 보인다.** 억지로 추적하면 409점 중 269점만 잡히고 FSDP 꼭짓점을
  놓쳐 진폭이 1.09 로 나온다(실제로는 실험과 비슷할 것). 잘못된 숫자를 만드느니 뺀다.
  "TS 가 실험을 잘 재현한다"는 논문 본문 문장으로 인용하면 충분하다:
  "The simulations give a good account of the neutron diffraction results."
  → 역설적이지만 **digitize 가 안 되는 것 자체가 둘이 겹친다는 증거**다.

    ambient 는 패널 (a) 의 **맨 아래 곡선**이고 offset 0 이다 (고 k 에서 1 로 수렴).
    위 곡선(3.0 GPa)은 +1 오프셋. 그래서 열마다 **가장 아래 덩어리**를 잡으면 분리된다.
    (패널 안 "ambient" 글자도 곡선보다 위에 있어 같은 규칙으로 걸러진다.)

입력: 05_doc/zeidler_figs/Fig1a_neutron_Sk.png  (원논문 PDF 를 4배로 렌더해 패널만 자른 것)
출력: 04_analysis/dat/zeidler_sq_ambient.dat   (k, S_exp)

축 보정 — 잘라낸 이미지 기준 (원 페이지 좌표에서 370, 180 을 뺀 값)
    x: 주눈금 11개가 62.12 px 간격, 2 Å⁻¹ 마다  → 31.06 px / Å⁻¹, k=0 이 x=22
    y: 주눈금 9개가 49.25 px 간격, S 1 마다     → S=0 이 y=481.25
"""
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "05_doc/zeidler_figs/Fig1a_neutron_Sk.png"
OUT = ROOT / "04_analysis/dat/zeidler_sq_ambient.dat"

X_K0, PX_PER_K = 22.0, 31.06          # 잘라낸 이미지 기준
Y_S0, PX_PER_S = 481.25, 49.25
KMIN, KMAX = 0.8, 21.2                # 양끝은 축 눈금(안쪽으로 뻗음)이 곡선과 섞인다

im = np.array(Image.open(SRC).convert("RGB")).astype(int)
H, W, _ = im.shape
r, g, b = im[:, :, 0], im[:, :, 1], im[:, :, 2]

black = (r < 120) & (g < 120) & (b < 120)
red = (r > 130) & (r - g > 60) & (r - b > 60)
# 패널 안쪽만 (테두리 제외)
# ★ 탐색 영역은 **눈금선을 확실히 뺀** 안쪽이어야 한다.
#   이 그림의 눈금은 축에서 **안쪽으로** 뻗어 있어, 넉넉히 잡으면 곡선으로 오인된다.
#   실제로 씨앗 열이 하필 k=5.0 눈금 위라 실험 곡선 추적이 통째로 실패했다.
inside = np.zeros_like(black)
inside[15:462, 45:686] = True          # 아래 눈금(S<0.4)·좌우 눈금 제외
black &= inside
red &= inside


def clusters(mask, x, gap=6):
    """열 x 의 모든 덩어리 중심을 S 값으로 (아래→위 순)."""
    ys = np.where(mask[:, x])[0]
    if len(ys) == 0:
        return []
    cl, cur = [], [ys[0]]
    for y in ys[1:]:
        if y - cur[-1] <= gap:
            cur.append(y)
        else:
            cl.append(cur); cur = [y]
    cl.append(cur)
    return sorted([(Y_S0 - float(np.mean(c))) / PX_PER_S for c in cl])


def track(mask, k_grid, cols, seed_k=5.3, dmax=0.18):   # 씨앗은 눈금(정수 k) 피해서
    """연속성 추적. 씨앗 열에서 **맨 아래** 덩어리로 시작해 양방향으로 따라간다.

    맨 아래만 보면 안 되는 이유: ambient 빨간 곡선이 검은 스플라인에 가려지는 열에서는
    **위 압력(3.0 GPa, offset +1)의 빨간 곡선을 잘못 집는다.** 실제로 k>14 에서 S≈1.9 가
    섞여 들어갔다. 직전 열 값에 가장 가까운 덩어리를 고르면 그 도약이 걸러진다.
    """
    n = len(k_grid)
    i0 = int(np.argmin(np.abs(k_grid - seed_k)))
    v = np.full(n, np.nan)
    c0 = clusters(mask, cols[i0])
    if not c0:
        return v
    v[i0] = c0[0]
    for rng_ in (range(i0 + 1, n), range(i0 - 1, -1, -1)):
        prev = v[i0]
        for i in rng_:
            cs = clusters(mask, cols[i])
            if cs:
                cand = min(cs, key=lambda s: abs(s - prev))
                if abs(cand - prev) <= dmax:
                    v[i] = cand
                    prev = cand
    return v


k_grid = np.arange(KMIN, KMAX + 1e-9, 0.05)
cols = np.clip(np.round(X_K0 + k_grid * PX_PER_K).astype(int), 0, W - 1)
out = np.column_stack([k_grid, track(black, k_grid, cols)])

# 튀는 점 제거: 이웃 중앙값에서 크게 벗어나면 버린다 (글자·눈금 잔재)
v = out[:, 1]
med = np.array([np.nanmedian(v[max(0, i-4):i+5]) for i in range(len(v))])
v[np.abs(v - med) > 0.25] = np.nan

np.savetxt(OUT, out, fmt="%.4f",
           header="Zeidler PRL 113, 135501 (2014) Fig.1(a) ambient 에서 digitize\n"
                  "검정 곡선 = 중성자 회절 실험(스플라인 피팅)\n"
                  "k(1/A)  S_exp")
print(f"-> {OUT}")

for c, nm in ((1, "실험"),):
    v = out[:, c]
    ok = np.isfinite(v)
    m = ok & (out[:, 0] > 1.0) & (out[:, 0] < 2.2)
    kk, ss = out[m, 0], v[m]
    i = np.argmax(ss)
    d = (ss[i-1] - ss[i+1]) / (2 * (ss[i-1] - 2*ss[i] + ss[i+1]))
    qpk = kk[i] + d * (kk[i+1] - kk[i-1]) / 2
    hi = ok & (out[:, 0] > 14)
    print(f"  {nm:6s}: 유효 {ok.sum()}/{len(v)}점,  FSDP q={qpk:.3f} S={ss[i]:.3f},  "
          f"고k(>14) 평균 {v[hi].mean():.3f} (1 이어야 정상)")
