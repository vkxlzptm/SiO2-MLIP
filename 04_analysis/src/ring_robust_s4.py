#!/usr/bin/env python
"""S4 ring stats 강건성 검증 — 3-ring 초과가 결합 cutoff 아티팩트인가?

ring_stats.py 는 Si-O 결합을 RCUT = 2.0 A 고정으로 판정한다. 그런데 7net 구조는
Si-O 결합길이가 BKS 보다 길다(RESULTS 3절: 1.635 vs 1.605 A). 고정 cutoff 는
결합길이가 다른 두 구조에 대해 '같은 기준'이 아닐 수 있고, 특히 3-ring 처럼
변형된 작은 고리는 결합 판정 하나에 생겼다 사라진다.

-> RCUT 을 1.85 ~ 2.15 A 로 스윕해 3-ring 비율의 순위가 뒤집히는지 본다.
   순위가 전 구간에서 유지되면 아티팩트가 아니다.

동시에 망 자체의 건전성(다리 O 비율, Si 배위수 분포, 비다리 O)도 함께 뽑는다.
7net 이 스스로 만든 망에 결함이 많다면 3-ring 초과는 위상이 아니라 결함 신호다.

출력: 04_analysis/dat/S4_rings_robust.dat  (표준출력에 요약)
"""
import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "04_analysis/src"))
from ring_stats import read_lmp, shortest_path_len          # noqa: E402
from collections import Counter, deque                       # noqa: E402

RUN = ROOT / "02_run/s4_mq7net"
DAT = ROOT / "04_analysis/dat"

STRUCT = [
    ("7net",      RUN / "prod_7net_mq.data",  2.0e13, "7net"),
    ("BKS_2e13",  RUN / "prod_bks_2e13.data", 2.0e13, "BKS"),
    ("BKS_5e12",  RUN / "prod_bks_5e12.data", 5.0e12, "BKS"),
    ("BKS_5e13",  RUN / "prod_bks_5e13.data", 5.0e13, "BKS"),
    # 독립 시드/독립 용융이력 BKS 참조 (s0_requench, seed 77213, 4000K 200ps melt,
    # 5e12 K/s, 300K NVT 100 ps). S4 BKS_5e12 와 '같은 냉각률·다른 실현'이므로
    # BKS 의 실현간 산포를 재는 유일한 자료다.
    ("BKS220_s0", ROOT / "02_run/s0_requench/sio2_bks220.data", 5.0e12, "BKS"),
]

RCUTS = [1.85, 1.90, 1.95, 2.00, 2.05, 2.10, 2.15]


def graph_and_defects(pos, typ, L, rcut):
    O = np.where(typ == 1)[0]
    Si = np.where(typ == 2)[0]
    adj = [set() for _ in Si]
    ocoord = Counter()
    for o in O:
        d = pos[Si] - pos[o]
        d -= L * np.round(d / L)
        nb = np.where(np.linalg.norm(d, axis=1) < rcut)[0]
        ocoord[len(nb)] += 1
        if len(nb) == 2:
            a, b = nb
            adj[a].add(b); adj[b].add(a)
        elif len(nb) > 2:
            for x in range(len(nb)):
                for y in range(x + 1, len(nb)):
                    adj[nb[x]].add(nb[y]); adj[nb[y]].add(nb[x])
    # Si 배위수 (O 기준)
    sicoord = Counter()
    for s in Si:
        d = pos[O] - pos[s]
        d -= L * np.round(d / L)
        sicoord[int((np.linalg.norm(d, axis=1) < rcut).sum())] += 1
    return [sorted(a) for a in adj], len(Si), len(O), ocoord, sicoord


def rings(adj, nSi, maxring=12):
    hist = Counter()
    for i in range(nSi):
        nb = adj[i]
        for a in range(len(nb)):
            for b in range(a + 1, len(nb)):
                d = shortest_path_len(adj, nb[a], nb[b], i)
                if d is not None and d + 2 <= maxring:
                    hist[d + 2] += 1
    return hist


def distinct_frac(hist, ns=range(3, 10)):
    dis = np.array([hist.get(n, 0) / n for n in ns], float)
    return dis / dis.sum(), np.array([hist.get(n, 0) for n in ns], float)


def main():
    out = open(DAT / "S4_rings_robust.dat", "w")
    out.write("# RCUT sensitivity of King-ring distinct fractions + network defect counts\n")
    out.write("# run  rcut  bridgeO%  O1  O2  O3  Si3  Si4  Si5  f3  f4  f5  f6  f7  f8  f9  mean_n\n")

    print(f"{'run':<11}{'rcut':>6}{'bridgeO%':>10}{'nonbrO':>8}{'3coordO':>9}"
          f"{'Si!=4':>7}{'f(3ring)%':>11}{'f(4ring)%':>11}{'mean_n':>8}")
    store = {}
    for tag, path, rate, fam in STRUCT:
        if not path.exists():
            print(f"!! missing {path}"); continue
        pos, typ, L = read_lmp(path)
        for rc in RCUTS:
            adj, nSi, nO, oc, sc = graph_and_defects(pos, typ, L, rc)
            h = rings(adj, nSi)
            f, cnt = distinct_frac(h)
            ns = np.arange(3, 10)
            mean_n = float((ns * f).sum())
            brid = 100.0 * oc[2] / nO
            si_off = sum(v for k, v in sc.items() if k != 4)
            out.write(f"{tag} {rc:.2f} {brid:.3f} {oc[1]} {oc[2]} {oc[3]} "
                      f"{sc[3]} {sc[4]} {sc[5]} " + " ".join(f"{x:.6f}" for x in f)
                      + f" {mean_n:.4f}\n")
            if abs(rc - 2.00) < 1e-9:
                store[tag] = dict(f=f, cnt=cnt, rate=rate, fam=fam, mean_n=mean_n,
                                  brid=brid, oc=dict(oc), sc=dict(sc), nSi=nSi, nO=nO)
            print(f"{tag:<11}{rc:>6.2f}{brid:>10.3f}{oc[1]:>8d}{oc[3]:>9d}"
                  f"{si_off:>7d}{100*f[0]:>11.2f}{100*f[1]:>11.2f}{mean_n:>8.3f}")
        print()
    out.close()
    print(f"-> {DAT}/S4_rings_robust.dat")

    # ---- RCUT 스윕에서 순위가 유지되는가 ----
    print("\n=== 3-ring distinct fraction (%) vs RCUT — 순위 안정성 ===")
    d = np.genfromtxt(DAT / "S4_rings_robust.dat", dtype=None, encoding=None)
    print(f"{'rcut':>6}" + "".join(f"{t:>12}" for t, *_ in STRUCT))
    for rc in RCUTS:
        row = [f"{rc:>6.2f}"]
        for tag, *_ in STRUCT:
            v = [r for r in d if r[0] == tag and abs(r[1] - rc) < 1e-9]
            row.append(f"{100*v[0][9]:>12.2f}" if v else f"{'-':>12}")
        print("".join(row))

    # ---- 계수 통계오차 (distinct ring 개수 기준 Poisson) ----
    print("\n=== RCUT=2.0 에서의 3-ring: distinct 개수와 Poisson 오차 ===")
    for tag in store:
        s = store[tag]
        n3 = s["cnt"][0] / 3.0
        print(f"  {tag:<11} triplet {s['cnt'][0]:>5.0f}  distinct {n3:6.1f} "
              f"+- {np.sqrt(n3):4.1f}   f3 = {100*s['f'][0]:5.2f}% "
              f"+- {100*s['f'][0]/np.sqrt(n3):4.2f}%p (counting only)")


if __name__ == "__main__":
    main()
