#!/usr/bin/env python
"""S1-2  ASE 교차검증.

목적: LAMMPS pair_style e3gnn (deployed_serial.pt) 경로와
      ASE SevenNetCalculator (원본 체크포인트) 경로가 같은 에너지/힘을 주는지 확인.
      -> 배포(deploy) 과정에서 조용히 뭔가 틀어지지 않았는지 검증.

비교 기준은 in.sp_check (run 0, 속도 없음)의 출력값을 쓴다.
LAMMPS 값을 아래 REF에 직접 붙여넣고 재실행하면 diff까지 출력한다.
"""
import numpy as np
from ase.io import read

try:  # sevenn >= 0.10 계열
    from sevenn.calculator import SevenNetCalculator
except ImportError:  # 구버전
    from sevenn.sevennet_calculator import SevenNetCalculator

DATA = "../../01_input/sio2_quenched.data"
MODEL = "7net-nano-5.5"

# in.sp_check 결과를 여기에 채워 넣으면 diff 출력 (None이면 생략)
REF = {"E": None, "P_bar": None, "fmax": None}

EV_A3_TO_BAR = 1.602176634e6  # 1 eV/A^3 = 1.602176634e11 Pa = 1.602176634e6 bar

at = read(DATA, format="lammps-data", style="charge",
          Z_of_type={1: 8, 2: 14}, sort_by_id=True)
at.pbc = True

print(f"natoms   {len(at)}  ({sum(at.numbers == 14)} Si, {sum(at.numbers == 8)} O)")
print("cell     " + "  ".join(f"{x:.4f}" for x in at.cell.lengths()))
vol = at.get_volume()
mass = at.get_masses().sum()
print(f"volume   {vol:.3f} A^3   density {mass/vol*1.66053907:.4f} g/cm^3")

at.calc = SevenNetCalculator(MODEL)
E = at.get_potential_energy()
F = at.get_forces()
S = at.get_stress(voigt=True)          # eV/A^3, ASE 부호규약: 양수 = 인장
P = -np.mean(S[:3]) * EV_A3_TO_BAR     # LAMMPS 부호(양수 = 압축)로 변환
fmax = np.linalg.norm(F, axis=1).max()

print(f"\nE_total  {E:.6f} eV")
print(f"E/atom   {E/len(at):.6f} eV")
print(f"|F|max   {fmax:.4f} eV/A")
print(f"|F|mean  {np.linalg.norm(F, axis=1).mean():.4f} eV/A")
print(f"sum(F)   {np.abs(F.sum(axis=0)).max():.2e} eV/A   (0이어야 정상)")
print(f"P_virial {P:.1f} bar   (= {P/1e4:.3f} GPa, 운동에너지 항 없음)")

for k, v in REF.items():
    if v is None:
        continue
    got = {"E": E, "P_bar": P, "fmax": fmax}[k]
    print(f"diff[{k}] {got - v:+.6g}   (ASE - LAMMPS)")
