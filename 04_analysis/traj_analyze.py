#!/usr/bin/env python
"""LAMMPS dump 궤적에서 결합각 분포·배위수·결합길이 통계를 뽑는다. **원격에서 실행.**

궤적 파일(.lammpstrj)은 수십 MB라 git으로 안 옮긴다. 이 스크립트를 원격에서 돌려
작은 요약 파일(*.dat)만 만들고, 그것만 sync 한다.

사용:
    python traj_analyze.py <dump파일> <출력접두사>
예:
    cd ~/projects/lammps_tutorial/SiO2-MLIP/02_run/s3_md
    python ../../04_analysis/traj_analyze.py traj_7net220.lammpstrj 7net220
    cd ../s0_requench
    python ../../04_analysis/traj_analyze.py traj_bks220.lammpstrj bks220

출력:
    <접두사>_angles.dat   결합각 히스토그램 (Si-O-Si, O-Si-O)
    <접두사>_stats.dat    배위수 분포·결합길이·Si-Si 최소거리 등 요약
"""
import sys
import numpy as np

RCUT = 2.0          # Si-O 1차 배위 판정 (g(r) 1피크와 2피크 사이 골)
TYPE_O, TYPE_SI = 1, 2


def read_dump(path):
    """xs ys zs (스케일 좌표) 형식의 dump를 프레임 단위로 넘겨준다."""
    with open(path) as f:
        while True:
            line = f.readline()
            if not line:
                return
            if not line.startswith("ITEM: TIMESTEP"):
                continue
            f.readline()                                   # timestep 값
            f.readline()                                   # ITEM: NUMBER OF ATOMS
            n = int(f.readline())
            f.readline()                                   # ITEM: BOX BOUNDS
            L = np.empty(3)
            for k in range(3):
                lo, hi = map(float, f.readline().split()[:2])
                L[k] = hi - lo
            cols = f.readline().split()[2:]                # ITEM: ATOMS id type xs ys zs
            ix = {c: i for i, c in enumerate(cols)}
            arr = np.array([f.readline().split() for _ in range(n)], dtype=float)
            typ = arr[:, ix["type"]].astype(int)
            s = arr[:, [ix["xs"], ix["ys"], ix["zs"]]]
            yield typ, s * L, L                            # 데카르트 좌표로 환산


def mic(d, L):
    return d - L * np.round(d / L)


def analyze(path, prefix):
    ang_sios, ang_osio, r_sio, r_oo, r_sisi = [], [], [], [], []
    nO_all, nSi_all, sisi_min = [], [], []
    nframe = 0

    for typ, pos, L in read_dump(path):
        nframe += 1
        O = np.where(typ == TYPE_O)[0]
        Si = np.where(typ == TYPE_SI)[0]

        # --- Si 중심: O 이웃 → 배위수 + O-Si-O 각 ---
        for i in Si:
            d = mic(pos[O] - pos[i], L)
            r = np.linalg.norm(d, axis=1)
            nb = np.where(r < RCUT)[0]
            nO_all.append(len(nb))
            r_sio.extend(r[nb])
            u = d[nb] / r[nb][:, None]
            for a in range(len(nb)):
                for b in range(a + 1, len(nb)):
                    ang_osio.append(np.degrees(np.arccos(np.clip(u[a] @ u[b], -1, 1))))

        # --- O 중심: Si 이웃 → 배위수 + Si-O-Si 각 ---
        for o in O:
            d = mic(pos[Si] - pos[o], L)
            r = np.linalg.norm(d, axis=1)
            nb = np.where(r < RCUT)[0]
            nSi_all.append(len(nb))
            if len(nb) == 2:
                u = d[nb] / r[nb][:, None]
                ang_sios.append(np.degrees(np.arccos(np.clip(u[0] @ u[1], -1, 1))))

        # --- Si-Si 최소거리 (Dechant 결함 지표) ---
        m = 1e9
        for i in Si:
            r = np.linalg.norm(mic(pos[Si] - pos[i], L), axis=1)
            m = min(m, r[r > 1e-6].min())
        sisi_min.append(m)

    ang_sios = np.array(ang_sios); ang_osio = np.array(ang_osio)
    nO_all = np.array(nO_all); nSi_all = np.array(nSi_all)
    r_sio = np.array(r_sio); sisi_min = np.array(sisi_min)

    # 히스토그램 (1도 bin)
    bins = np.arange(60.5, 180.5, 1.0)
    c = 0.5 * (bins[1:] + bins[:-1])
    h1, _ = np.histogram(ang_sios, bins=bins, density=True)
    h2, _ = np.histogram(ang_osio, bins=bins, density=True)
    np.savetxt(f"{prefix}_angles.dat", np.c_[c, h1, h2],
               header="angle(deg)  P(Si-O-Si)  P(O-Si-O)   [1 deg bin, normalized]")

    with open(f"{prefix}_stats.dat", "w") as f:
        w = lambda s: (print(s), f.write(s + "\n"))
        w(f"# {path}   frames = {nframe}")
        w(f"Si-O-Si   mean {ang_sios.mean():8.3f}  std {ang_sios.std():7.3f}  "
          f"median {np.median(ang_sios):8.3f}  peak {c[np.argmax(h1)]:.1f}   n={len(ang_sios)}")
        w(f"O-Si-O    mean {ang_osio.mean():8.3f}  std {ang_osio.std():7.3f}  "
          f"median {np.median(ang_osio):8.3f}  peak {c[np.argmax(h2)]:.1f}   n={len(ang_osio)}")
        w(f"Si-O      mean {r_sio.mean():8.4f}  std {r_sio.std():7.4f} A   n={len(r_sio)}")
        w(f"Si-Si min per frame:  mean {sisi_min.mean():.4f}  min {sisi_min.min():.4f} A")
        w(f"Si 배위수  <n> {nO_all.mean():.4f}   " +
          "  ".join(f"{k}:{100*(nO_all==k).mean():.3f}%" for k in sorted(set(nO_all))))
        w(f"O  배위수  <n> {nSi_all.mean():.4f}   " +
          "  ".join(f"{k}:{100*(nSi_all==k).mean():.3f}%" for k in sorted(set(nSi_all))))
    print(f"-> {prefix}_angles.dat, {prefix}_stats.dat")


if __name__ == "__main__":
    analyze(sys.argv[1], sys.argv[2])
