#!/usr/bin/env python
"""Fig. S4 rings — 7net 이 '스스로 만든' 망 위상 vs BKS 가 만든 망 위상.

★ fig_rings.py 와 혼동하지 말 것.
  fig_rings.py = BKS 가 만든 망을 7net 이 **물려받아 이완만** 한 경우
                 (ring 분포가 비트 단위로 동일 -> "위상은 이완으로 안 바뀐다"의 증거).
  이 그림      = 7net 이 **자기 힘으로 melt-quench** 해서 만든 망.
                 두 그림의 차이가 이 프로젝트가 처음 재는 양, 곧 **위상 형성 효과**다.
  그래서 이 그림은 fig_rings.py 와 같은 형식(단일 패널, 막대그룹)에 7net-self 막대
  하나만 추가한 버전이다 (2026-08-25, 3패널 버전에서 단순화).

비교 설계:
  - BKS 막대 = S4_BKS_{2e13,5e12,5e13}_rings.dat + BKS220_rings.dat(s0, 독립 시드) 4런의
    평균, 오차막대 = 4런의 최소~최대 범위 (project rule: "BKS 4-sample rule", 냉각률
    3종 + 독립 시드 1개를 함께 묶어 BKS 쪽 대표값과 산포를 동시에 추정한다).
  - 7net 막대 = 자체 melt-quench 1 런(시드 1개, 117 h)뿐이라 **오차막대 없음**.
    실현간 산포를 잴 방법이 없다는 뜻이지, 값이 정확하다는 뜻이 아니다 — 참고로 BKS
    5e12의 두 독립 실현(시드 90210 vs 77213)은 3-ring 에서 1.80 % vs 3.07 %로 갈라졌다
    (S4_rings_summary.dat). 7net 도 비슷한 크기의 산포가 있을 수 있다.
  - AIMD = fig_rings.py 와 동일한 Dechant JPCC 2026 Fig. S4(a) 디지타이즈 값 (참고선).

3패널 버전(RCUT 강건성, 냉각률-무관성 σ 주석)에서 뺀 내용은 사라진 게 아니라 이동:
  - RCUT(결합판정) 강건성  -> ring_robust_s4.py, NOTE.md "S4 분석 1"
  - 냉각률 스윕(5e12~5e13)에도 3-ring 순위가 안 뒤집힘 -> S4_rings_summary.dat, NOTE.md
  - 차이의 σ 유의성 표      -> S4_rings_summary.dat (7net-BKS diff, err, sigma 열)

입력: 04_analysis/dat/S4_*_rings.dat, dat/BKS220_rings.dat, 05_doc/dechant_figs/SI_p4_img1.jpeg
출력: 04_analysis/fig/fig_rings_s4.png, dat/S4_rings_summary.dat
"""
from pathlib import Path

import numpy as np
from PIL import Image
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator

ROOT = Path(__file__).resolve().parents[2]
DAT, FIG = ROOT / "04_analysis/dat", ROOT / "04_analysis/fig"
FIG.mkdir(exist_ok=True); DAT.mkdir(exist_ok=True)

plt.rcParams.update({
    "font.size": 10, "axes.labelsize": 11, "xtick.labelsize": 10, "ytick.labelsize": 10,
    "legend.fontsize": 8.5, "legend.handlelength": 1.3,
    "xtick.direction": "in", "ytick.direction": "in",
    "xtick.top": True, "ytick.right": True,
    "xtick.major.size": 5, "ytick.major.size": 5,
    "xtick.minor.size": 2.8, "ytick.minor.size": 2.8,
    "axes.linewidth": 0.9,
})

NET_COL = "#D7292A"
BKS_COL = "#267BB6"
AIMD_COL = "tab:green"
NET_LABEL = "7net-Nano-4.5"
NS = np.arange(3, 10)

# ---------- Dechant Fig. S4(a) LES digitize (fig_rings.py 와 동일) ----------
im = np.array(Image.open(ROOT / "05_doc/dechant_figs/SI_p4_img1.jpeg").convert("RGB")).astype(int)
sub = im[:, : im.shape[1] // 2]
r_, g_, b_ = sub[:, :, 0], sub[:, :, 1], sub[:, :, 2]
black = (r_ < 110) & (g_ < 110) & (b_ < 110)
rs = black.sum(1)
rows = np.where(rs > 0.5 * rs.max())[0]
r0, r1 = rows.min(), rows.max()
ccols = np.where(black[r1])[0]
c0, c1 = ccols.min(), ccols.max()
green = (g_ > 90) & (g_ > r_ + 35) & (g_ > b_ + 35)

to_x = lambda cc: 0.0 + (cc - c0) / (c1 - c0) * 10.0
xs, ys = [], []
for cc in range(c0, c1 + 1):
    rr = np.where(green[:, cc])[0]
    rr = rr[(rr > r0) & (rr < r1)]
    if len(rr) == 0:
        continue
    cl, cu = [], [rr[0]]
    for x in rr[1:]:
        (cu.append(x) if x - cu[-1] <= 6 else (cl.append(list(cu)), cu.clear(), cu.append(x)))
    cl.append(list(cu))
    xs.append(to_x(cc)); ys.append(r1 - float(np.mean(cl[-1])))
xs, ys = np.array(xs), np.array(ys)

nring_full = np.arange(2, 10)
ai_full = np.clip(np.interp(nring_full, xs, ys, left=0, right=0), 0, None)
ai_full = ai_full / ai_full.sum()
aimd = ai_full[np.isin(nring_full, NS)]              # n=3..9 만 취해 NS 와 정렬


def load_rings(path):
    """S4_*_rings.dat: n count f_triplet f_distinct.
    BKS220_rings.dat 는 구판이라 (n count fraction=triplet) 3열뿐 -> distinct 재계산."""
    d = np.loadtxt(path)
    n, cnt = d[:, 0].astype(int), d[:, 1]
    if d.shape[1] >= 4:
        f = d[:, 3]
    else:
        f = cnt / n
        f = f / f.sum()
    out_f, out_c = np.zeros(len(NS)), np.zeros(len(NS))
    for i, nn in enumerate(NS):
        m = n == nn
        if m.any():
            out_f[i], out_c[i] = f[m][0], cnt[m][0]
    return out_f, out_c


net_f, net_cnt = load_rings(DAT / "S4_7net_rings.dat")

bks_files = ["S4_BKS_2e13_rings.dat", "S4_BKS_5e12_rings.dat",
             "S4_BKS_5e13_rings.dat", "BKS220_rings.dat"]
B = np.array([load_rings(DAT / f)[0] for f in bks_files])   # (4, 7)
b_mean, b_lo, b_hi = B.mean(0), B.min(0), B.max(0)

# ------------------------------------------------------------------ figure
fig, ax = plt.subplots(figsize=(3.8, 3.0))
w = 0.27
ax.bar(NS - w, b_mean, width=w, color=BKS_COL, alpha=0.85, edgecolor="k", lw=0.7,
       zorder=2, yerr=[b_mean - b_lo, b_hi - b_mean],
       error_kw=dict(lw=0.9, capsize=2.0, ecolor="0.2"))
ax.bar(NS, net_f, width=w, color=NET_COL, alpha=0.85, edgecolor="k", lw=0.7, zorder=2)
ax.bar(NS + w, aimd, width=w, color=AIMD_COL, alpha=0.85, edgecolor="k", lw=0.7, zorder=2)

ax.set_xlabel("Ring size  (number of Si)")
ax.set_ylabel("Fraction  (distinct rings)")
ax.set_xticks(NS); ax.set_xlim(2.4, 9.6); ax.set_ylim(0, 0.46)
ax.yaxis.set_minor_locator(AutoMinorLocator(2))

h_bks, = ax.plot([], [], "s", c=BKS_COL, ms=8, mec="k", mew=0.7, label="BKS (4 runs)")
h_net, = ax.plot([], [], "s", c=NET_COL, ms=8, mec="k", mew=0.7, label=f"{NET_LABEL} (self-quenched)")
h_aimd, = ax.plot([], [], "s", c=AIMD_COL, ms=8, mec="k", mew=0.7,
                  label="AIMD PBE (Dechant 2026, 120 atoms)")
leg1 = ax.legend(handles=[h_bks, h_net], loc="upper left", frameon=False, fontsize=8.0,
                  ncols=2, bbox_to_anchor=(0.007, 1.0), columnspacing=0.9, handletextpad=0.4)
ax.add_artist(leg1)
ax.legend(handles=[h_aimd], loc="upper left", frameon=False, fontsize=8.0,
          bbox_to_anchor=(0.007, 0.905), handletextpad=0.4)
ax.set_title("Ring size distribution  (King criterion)", fontsize=10.5)

fig.tight_layout()
fig.savefig(FIG / "fig_rings_s4.png", dpi=300)
print(f"-> {FIG}/fig_rings_s4.png")

# ------------------------------------------------------------------ summary
# 계수오차(Poisson) + BKS 실현간 산포(5e12 두 실현 차이/sqrt2) 를 합쳐 diff 의 유의성만 표로 남긴다.
ndist_net = np.maximum(net_cnt / NS, 1e-9)
sig_net = net_f / np.sqrt(ndist_net)
Bc = np.array([load_rings(DAT / f)[1] for f in bks_files])
ndist_b = np.maximum(Bc / NS, 1e-9)
sig_b_count = (B / np.sqrt(ndist_b)).mean(0)
sig_b_real = np.abs(B[1] - B[3]) / np.sqrt(2)          # 5e12 (S4) vs 5e12* (s0), n=2 보수적 추정
sig_b_tot = np.sqrt(sig_b_count**2 + sig_b_real**2)
d_tot = np.sqrt(sig_net**2 + sig_b_tot**2)
diff = 100 * (net_f - b_mean)
err = 100 * d_tot

with open(DAT / "S4_rings_summary.dat", "w") as f:
    hdr = (f"{'n':>3}{'7net%':>9}{'BKSmean%':>10}{'BKSmin%':>9}{'BKSmax%':>9}"
           f"{'diff%p':>9}{'err%p':>8}{'sigma':>7}\n")
    f.write("# King ring, distinct fraction. BKS = 4 runs (5e12 x2 seeds, 2e13, 5e13)\n")
    f.write("# err = Poisson(7net) (+) Poisson(BKS) (+) BKS run-to-run scatter (7net: no own scatter term)\n")
    f.write("# 참고: 냉각률 스윕(5e12~5e13)에서도 3-ring 순위는 안 뒤집힘 (아래 BKSmin/BKSmax 참고;\n")
    f.write("#       상세 강건성은 ring_robust_s4.py, NOTE.md 'S4 분석 1' 참고)\n")
    f.write("# " + hdr)
    print("\n" + hdr, end="")
    for i, nn in enumerate(NS):
        line = (f"{nn:>3d}{100*net_f[i]:>9.2f}{100*b_mean[i]:>10.2f}"
                f"{100*b_lo[i]:>9.2f}{100*b_hi[i]:>9.2f}{diff[i]:>9.2f}"
                f"{err[i]:>8.2f}{abs(diff[i])/err[i]:>7.1f}\n")
        f.write(line); print(line, end="")
    mn = lambda fr: float((NS * fr).sum())
    tail = (f"\n# mean ring size (distinct):  7net {mn(net_f):.3f}   BKS mean {mn(b_mean):.3f}\n")
    f.write(tail); print(tail, end="")
print(f"-> {DAT}/S4_rings_summary.dat")
