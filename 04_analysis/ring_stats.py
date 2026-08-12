#!/usr/bin/env python
"""SiO2 네트워크의 ring size 분포 (King 기준, shortest-path ring).

정의: n-ring = Si n개가 Si-O-Si-O... 로 닫힌 고리 (Dechant/King 정의와 동일).
알고리즘: Si-Si 인접그래프(다리 O를 공유하면 인접)를 만든 뒤,
          각 Si i 의 이웃쌍 (j,k) 에 대해 i 를 제외한 최단 j→k 경로를 BFS로 찾는다.
          고리 크기 = (경로 간선수) + 2.

⚠ 주의: ring 통계는 정의(King / Guttman / primitive)에 따라 결과가 달라진다.
   문헌 그림과 대조할 때는 정의가 같은지 확인해야 하며, 다르면 **정성 비교만** 하라.
   우리 구조끼리(BKS vs 7net)의 비교는 같은 알고리즘이므로 항상 유효하다.

사용: python ring_stats.py <lammps .data 파일> [라벨]
"""
import sys
from collections import deque, Counter
import numpy as np

RCUT = 2.0


def read_lmp(path):
    lo, hi, pos, typ = np.zeros(3), np.zeros(3), [], []
    lines = open(path).readlines()
    i = 0
    while i < len(lines):
        L = lines[i]
        for k, tag in enumerate(("xlo xhi", "ylo yhi", "zlo zhi")):
            if tag in L:
                a, b = L.split()[:2]; lo[k], hi[k] = float(a), float(b)
        if L.strip().startswith("Atoms"):
            i += 2
            while i < len(lines) and lines[i].strip():
                p = lines[i].split()
                typ.append(int(p[1])); pos.append([float(p[3]), float(p[4]), float(p[5])])
                i += 1
            break
        i += 1
    return np.array(pos), np.array(typ), hi - lo


def build_graph(pos, typ, L):
    """다리 산소를 공유하는 Si끼리 연결. 반환: adjacency list (Si 로컬 인덱스)."""
    O = np.where(typ == 1)[0]
    Si = np.where(typ == 2)[0]
    loc = {g: i for i, g in enumerate(Si)}
    adj = [set() for _ in Si]
    n_bridge = 0
    for o in O:
        d = pos[Si] - pos[o]
        d -= L * np.round(d / L)
        nb = np.where(np.linalg.norm(d, axis=1) < RCUT)[0]
        if len(nb) == 2:                       # 다리 산소만
            a, b = nb
            adj[a].add(b); adj[b].add(a)
            n_bridge += 1
        elif len(nb) > 2:                      # 3배위 O — 모든 쌍 연결
            for x in range(len(nb)):
                for y in range(x + 1, len(nb)):
                    adj[nb[x]].add(nb[y]); adj[nb[y]].add(nb[x])
    return [sorted(a) for a in adj], len(Si), n_bridge, len(O)


def shortest_path_len(adj, s, t, banned):
    """banned 노드를 피해 s→t 최단 경로의 간선 수. 없으면 None."""
    if s == t:
        return 0
    seen = {s, banned}
    q = deque([(s, 0)])
    while q:
        u, d = q.popleft()
        for v in adj[u]:
            if v in seen:
                continue
            if v == t:
                return d + 1
            seen.add(v); q.append((v, d + 1))
    return None


def ring_stats(adj, nSi, maxring=12):
    """King 기준. 서로 다른 고리 크기의 (i,j,k) 등장 횟수를 센다."""
    hist = Counter()
    for i in range(nSi):
        nb = adj[i]
        for a in range(len(nb)):
            for b in range(a + 1, len(nb)):
                d = shortest_path_len(adj, nb[a], nb[b], i)
                if d is not None and d + 2 <= maxring:
                    hist[d + 2] += 1
    return hist


if __name__ == "__main__":
    path = sys.argv[1]
    label = sys.argv[2] if len(sys.argv) > 2 else path
    pos, typ, L = read_lmp(path)
    adj, nSi, nbr, nO = build_graph(pos, typ, L)
    deg = np.array([len(a) for a in adj])
    hist = ring_stats(adj, nSi)
    tot = sum(hist.values())

    print(f"=== {label}   rho = {43260.70*1.66053907/L.prod():.4f} g/cm3")
    print(f"  Si {nSi}개, O {nO}개, 다리 O {nbr}개 ({100*nbr/nO:.2f}%)")
    print(f"  Si-Si 연결도 <k> = {deg.mean():.4f}   " +
          "  ".join(f"{k}:{(deg==k).sum()}" for k in sorted(set(deg))))
    print(f"  King ring 통계 (총 {tot}개 탐색)")
    for n in sorted(hist):
        print(f"    {n:2d}-ring  {hist[n]:6d}   {100*hist[n]/tot:6.2f}%   "
              f"{'#'*int(60*hist[n]/max(hist.values()))}")
    out = f"{label}_rings.dat"
    with open(out, "w") as f:
        f.write("# n_ring  count  fraction\n")
        for n in sorted(hist):
            f.write(f"{n} {hist[n]} {hist[n]/tot:.6f}\n")
    print(f"  -> {out}")
