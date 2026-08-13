#!/usr/bin/env python
"""정적 구조에서 결합길이·배위수·Si-O-Si 각 비교.

목적: "PBE 기반 MLIP면 결합이 길어지고 밀도는 낮아져야 하지 않나?"를 데이터로 검증.
      0 K 구조라 열적 broadening이 없어 결합길이를 깨끗하게 잴 수 있다.
"""
import numpy as np
from itertools import product

from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
DAT, FIG = ROOT / "04_analysis/dat", ROOT / "04_analysis/fig"
FIG.mkdir(exist_ok=True); DAT.mkdir(exist_ok=True)


FILES = [
    ("BKS quench (rho=2.607)",       f"{ROOT}/01_input/sio2_quenched.data"),
    ("7net relax @V_BKS (2.607)",    f"{ROOT}/02_run/s2_relax/relaxed_s1_atoms.data"),
    ("7net relax @V=28552 (2.516)",  f"{ROOT}/02_run/s2_relax/relaxed_final.data"),
]
RCUT_SIO = 2.0   # Si-O 1차 배위 판정 (1피크와 2피크 사이 골)


def read_lmp(path):
    box, pos, typ = [], [], []
    with open(path) as f:
        lines = f.readlines()
    i = 0
    lo = np.zeros(3); hi = np.zeros(3)
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


def mic(d, L):
    return d - L * np.round(d / L)


def pairs_within(pos, L, ia, ib, rmax, same=False):
    """ia, ib: 인덱스 배열. 최소이미지로 rmax 이내 거리 목록."""
    out = []
    for i in ia:
        d = mic(pos[ib] - pos[i], L)
        r = np.linalg.norm(d, axis=1)
        m = (r < rmax) & (r > 1e-6)
        out.append(r[m])
    return np.concatenate(out)


for label, path in FILES:
    pos, typ, L = read_lmp(path)
    O = np.where(typ == 1)[0]; Si = np.where(typ == 2)[0]
    V = L.prod()
    rho = 43260.70 * 1.66053907 / V

    r_sio = pairs_within(pos, L, Si, O, RCUT_SIO)
    nSiO = len(r_sio) / len(Si)                      # Si당 O 배위수
    r_oo = pairs_within(pos, L, O, O, 3.2)
    r_sisi = pairs_within(pos, L, Si, Si, 3.8)

    # Si-O-Si 각: 각 O에 대해 Si 이웃 2개면 각도
    ang = []
    for o in O:
        d = mic(pos[Si] - pos[o], L)
        r = np.linalg.norm(d, axis=1)
        nb = np.where(r < RCUT_SIO)[0]
        if len(nb) == 2:
            v1, v2 = d[nb[0]] / r[nb[0]], d[nb[1]] / r[nb[1]]
            ang.append(np.degrees(np.arccos(np.clip(v1 @ v2, -1, 1))))
    ang = np.array(ang)

    print(f"\n=== {label} ===  V={V:.1f} A^3, rho={rho:.4f} g/cm3")
    print(f"  Si-O  mean {r_sio.mean():.4f} +- {r_sio.std():.4f} A   (n={len(r_sio)})")
    print(f"  O-O   mean {r_oo.mean()/1:.4f} A  (r<3.2, n={len(r_oo)//2})")
    print(f"  Si-Si mean {r_sisi.mean():.4f} A  (r<3.8, n={len(r_sisi)//2})")
    print(f"  Si 배위수 <n_O>  = {nSiO:.4f}   (완벽한 사면체망 = 4.000)")
    print(f"  Si-O-Si  {ang.mean():.2f} +- {ang.std():.2f} deg   (2배위 O {len(ang)}/{len(O)}개)")
