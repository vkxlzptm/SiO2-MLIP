#!/usr/bin/env python
"""3-ring 초과가 Si-O-Si 각을 좁히는가 — **기계론 직접 검사**.

왜 이 스크립트가 따로 있나
  3원환(edge-sharing 이 아니라 세 SiO4 가 고리로 닫힌 것)은 기하가 Si-O-Si 를
  좁히도록 강제한다. 7net 자기망은 BKS 망보다 3-ring 이 2.4배 많다(분석 1).
  그렇다면 Si-O-Si 분포에 **저각 어깨**가 있어야 한다. 없으면 ring 결론을 다시 봐야 한다.

  ★ traj_analyze.py 를 기다릴 필요가 없다: prod_*.data 한 프레임에 다리 산소가
    이미 ~1,436개다. 분포의 '모양'을 보는 데는 충분하다.
    (traj_analyze 는 250프레임 평균이라 최종 보고 수치의 잡음을 줄이는 용도.
     여기 수치는 **단일 스냅샷**임을 항상 병기할 것.)

  ★ 그리고 여기서만 할 수 있는 것: 다리 산소를 **3원환 소속 / 비소속**으로 갈라
    각 분포를 따로 낸다. 전체 분포 비교보다 훨씬 직접적인 인과 검사다 —
    "3원환 산소가 실제로 좁은가" 와 "그 초과분이 전체 평균을 얼마나 끌어내리는가"
    를 분리해서 답한다.

정의
  - 다리 산소 = Si 두 개와만 RCUT(2.0 Å) 안에서 이웃인 O (ring_stats.py 와 동일)
  - Si-O-Si 각 = 그 두 Si 를 향한 벡터 사이 각 (최소이미지)
  - 3원환 산소 = 그 산소가 잇는 두 Si 가 **제3의 Si 를 공유**하는 경우
    (Si-Si 인접그래프에서 삼각형을 이룸 = ring_stats 의 3-ring 과 같은 대상)

출력: 04_analysis/dat/S4_angles_by_ring.dat  (+ 표준출력 요약)
"""
import sys
from pathlib import Path
from collections import Counter

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ring_stats import read_lmp, RCUT                       # noqa: E402

RUN = ROOT / "02_run/s4_mq7net"
DAT = ROOT / "04_analysis/dat"

STRUCT = [
    # ★ RESULTS 3절의 사다리와 잇기 위해 기존 두 구조도 같은 방법으로 잰다.
    #   s0 BKS220 은 RESULTS 가 151.89 로 보고한 바로 그 구조 -> 방법 검증용.
    #   s3 7net220 은 RESULTS 가 145.05 로 보고한 "BKS 위상 위 7net" 구조.
    ("7net_own",   RUN / "prod_7net_mq.data"),
    ("7net_BKSnet", ROOT / "02_run/s3_md/prod_7net220.data"),
    ("BKS_2e13",   RUN / "prod_bks_2e13.data"),
    ("BKS_5e12",   RUN / "prod_bks_5e12.data"),
    ("BKS_5e13",   RUN / "prod_bks_5e13.data"),
    ("BKS220_s0",  ROOT / "02_run/s0_requench/sio2_bks220.data"),
]


def bridging_angles(pos, typ, L):
    """다리 산소마다 (Si-O-Si 각, 3원환 소속 여부) 를 낸다."""
    O = np.where(typ == 1)[0]
    Si = np.where(typ == 2)[0]
    loc = {g: i for i, g in enumerate(Si)}

    # 1) 다리 산소 찾기 + 각 계산
    pairs, angles = [], []
    for o in O:
        d = pos[Si] - pos[o]
        d -= L * np.round(d / L)
        r = np.linalg.norm(d, axis=1)
        nb = np.where(r < RCUT)[0]
        if len(nb) != 2:
            continue                       # 다리 산소만 (비다리·3배위 제외)
        a, b = nb
        u, v = d[a] / r[a], d[b] / r[b]
        angles.append(np.degrees(np.arccos(np.clip(u @ v, -1.0, 1.0))))
        pairs.append((a, b))

    # 2) Si-Si 인접그래프 (다리 산소 기준) -> 삼각형 = 3원환
    adj = [set() for _ in Si]
    for a, b in pairs:
        adj[a].add(b); adj[b].add(a)
    in3 = [len(adj[a] & adj[b]) > 0 for a, b in pairs]   # 제3의 Si 를 공유하면 3원환
    return np.array(angles), np.array(in3, bool), len(Si), len(O)


rows = []
print(f"{'structure':<12}{'bridgO':>7}{'in 3-ring':>11}{'%':>7}"
      f"{'<ang> all':>11}{'<ang> in3':>11}{'<ang> not':>11}{'diff':>8}{'sd all':>8}")
for tag, path in STRUCT:
    if not path.exists():
        print(f"!! 없음 {path}"); continue
    pos, typ, L = read_lmp(path)
    ang, in3, nSi, nO = bridging_angles(pos, typ, L)
    m3, mo = ang[in3], ang[~in3]
    rows.append((tag, ang, in3))
    print(f"{tag:<12}{len(ang):>7d}{in3.sum():>11d}{100*in3.mean():>6.2f}%"
          f"{ang.mean():>11.2f}{m3.mean():>11.2f}{mo.mean():>11.2f}"
          f"{m3.mean()-mo.mean():>8.2f}{ang.std(ddof=1):>8.2f}")

# ---- 저각 꼬리 (어깨) 정량 ----
print(f"\n{'structure':<12}" + "".join(f"{f'<{t}deg':>10}" for t in (120, 130, 140))
      + f"{'p05':>9}{'median':>9}")
for tag, ang, in3 in rows:
    print(f"{tag:<12}" + "".join(f"{100*(ang < t).mean():>9.2f}%" for t in (120, 130, 140))
          + f"{np.percentile(ang, 5):>9.2f}{np.median(ang):>9.2f}")

# ---- 전체 평균 이동 중 3원환이 설명하는 몫 ----
print("\n=== 7net 의 전체 평균 하락 중 3원환 초과분이 설명하는 몫 ===")
ref = dict((t, (a, i)) for t, a, i in rows)
if "7net_own" in ref and "BKS_2e13" in ref:
    a7, i7 = ref["7net_own"]; ab, ib = ref["BKS_2e13"]
    d_tot = a7.mean() - ab.mean()
    # BKS 의 소속별 평균을 그대로 두고 7net 의 3원환 '비율'만 적용했을 때의 예측 이동
    d_pred = (i7.mean() - ib.mean()) * (ab[ib].mean() - ab[~ib].mean())
    print(f"  실측 전체 평균 이동 (7net - BKS_2e13) : {d_tot:+.2f} deg")
    print(f"  3원환 비율 증가만으로 예측되는 이동   : {d_pred:+.2f} deg"
          f"   ({100*d_pred/d_tot:.0f} %)" if d_tot else "")
    print(f"  나머지 {d_tot-d_pred:+.2f} deg 는 비3원환 산소 자체가 이동한 몫")

with open(DAT / "S4_angles_by_ring.dat", "w") as f:
    f.write("# Si-O-Si angle by 3-ring membership, single 300K snapshot (prod_*.data)\n")
    f.write("# structure n_bridgeO n_in3ring pct_in3 mean_all mean_in3 mean_not sd_all "
            "p05 median frac_lt120 frac_lt130 frac_lt140\n")
    for tag, ang, in3 in rows:
        f.write(f"{tag} {len(ang)} {int(in3.sum())} {100*in3.mean():.3f} "
                f"{ang.mean():.3f} {ang[in3].mean():.3f} {ang[~in3].mean():.3f} "
                f"{ang.std(ddof=1):.3f} {np.percentile(ang,5):.3f} {np.median(ang):.3f} "
                + " ".join(f"{100*(ang<t).mean():.3f}" for t in (120,130,140)) + "\n")
print(f"\n-> {DAT}/S4_angles_by_ring.dat")
