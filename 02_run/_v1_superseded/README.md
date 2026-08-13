# _v1_superseded — 폐기된 1차 시도 (ρ = 2.607 g/cm³ 구조 기반)

## 왜 폐기했나

첫 BKS melt-quench(`01_input/sio2_quenched.data`, `01_input/melt_quench_log.lammps`)가
**녹지 않은 상태로 진행**됐다. 승온 100 ps + 4500 K 25 ps 동안 MSD < 1.6 Å²였고,
step ~130,000에서 비로소 확산이 시작되면서 부피가 2.26 → 2.62로 붕괴했다.
결과 밀도 2.607은 α-quartz(2.648) 수준인데, 비정질이 결정만큼 조밀할 수는 없다.

원인은 **용융 중 NPT 사용**이다 — Dechant, Muralidhar, Ma, *J. Phys. Chem. C* **130**,
7148 (2026) 이 명시적으로 경고한다:

> "the presence of unphysical bonds may lead to unphysical cell shape and volume
> variations if the NPT ensemble is used. ... the NVT ensemble was used for melting
> simulations, while the NPT ensemble was employed for equilibration runs at 300 K."

부피고정 NVT로 다시 만든 것이 `02_run/s0_requench/` 이고, BKS 밀도 오차가
+18.5 % → +5.1 %로 줄었다. 상세는 `05_doc/RESULTS.md` §7.

## 여기 있는 것

| 경로 | 내용 |
|---|---|
| `s2_relax/` | ρ=2.607 구조의 정적 이완(`in.relax`)과 E–V 스캔(`in.ev`, `ev_scan.txt`) |
| `s3_md/` | ρ=2.607 용 MD 입력. **실행하지 않음** |
| `s0_check/` | NPT 부피 평형 진단 입력. 재quench로 방향이 정해져 **실행하지 않음** |

## 그래도 유효한 것

- **`02_run/s1_sanity/`는 폐기 아님.** 속도·virial 검증·cutoff 스윕은 포텐셜 성능에
  대한 결과라 구조와 무관하다.
- 여기 `ev_scan.txt`의 E–V 방법론과 BM3 피팅 절차는 그대로 `s2_relax/in.ev220`에 재사용됐다.
- 이 구조에서 얻은 "밀도 하락이 결합길이 신장으로 100 % 설명된다"는 관계식은
  새 구조에서도 성립한다.

지우지 않고 남긴 이유: **왜 다시 했는지가 이 프로젝트의 핵심 서사**이기 때문이다.
