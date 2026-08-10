# STATUS — S0 완료 시점 인수인계 (2026-08-10)

## 프로젝트 한 줄

BKS(고전 포텐셜)로 만든 비정질 SiO2 구조에 범용 MLIP **SevenNet-Nano**를 적용해,
**RDF(Si–O / O–O / Si–Si)를 BKS vs SevenNet-Nano vs AIMD(문헌 digitize) 3자 비교**한다.
목적: 취업 포트폴리오/면접 자료 (코닝, ASM, LG디스플레이). 목표 기간 3일.

## 진행 상태

| 단계 | 상태 |
|---|---|
| S0 환경 구축 | **완료** — LAMMPS + `pair_style e3gnn` 빌드·검증·배포까지 |
| S1 sanity + 속도 실측 | **진행 중** — single point 통과, 속도 측정 남음 |
| S2 구조 이완 | 미착수 |
| S3 RDF 3자 비교 | 미착수 |
| S4 짧은 MD (여유 시) | 미착수 |
| S5 정리 | 미착수 |

## 확정된 환경

```
원격  Ubuntu 20.04 / i5-11600K (6c12t) / RAM 15GB / GPU 없음
      gcc 9.4.0, cmake (pip) 3.31.x, python 3.11, torch 2.13.0+cpu
      sevenn = GitHub main (-e 설치, ~/SevenNet-src)   ※ PyPI엔 7net-nano 없음
      LAMMPS stable_2Aug2023_update3 + sevenn patch_lammps, C++17
      MPI = Intel oneAPI 2021.5 (PATH 우선)
      lmp_7net → ~/lammps_sevenn/build/lmp  (~/bin 심볼릭 링크)
경로  원격 $PROJ=/home/dhl/projects/lammps_tutorial/SiO2-MLIP
      로컬 /Users/DHDLee/projects/SiO2-MLIP
동기화 GitHub vkxlzptm/SiO2-MLIP (SSH)
모델  7net-nano-5.5 → 01_input/pot/deployed_serial.pt (471 KB)
```

## S0에서 확인된 사실 (근거 있음)

- **7net-Nano = 7net-Omni(26M)를 105k로 knowledge distillation.** lmax 2 / 3층 / 채널 32 /
  self-connection **linear**(논문 미기재, 체크포인트 메타에서 확인). 체크포인트 458 KB ÷ 4 byte ≈ 105k로 정합.
- **학습 functional = PBE(+U), D3 없음.** 단 DFT 직접이 아니라 **teacher(7net-Omni)의 `mpa` 채널 추론값**으로
  증류 → 정확도 상한이 이중 근사. 실험값 해석에 반드시 반영할 것.
- **논문은 SiO2 밀도를 예측한 적이 없다.** 비정질 SiO2를 NVT로 2.34 g/cm³에 고정해서 만들었고,
  그 2.34는 인용문헌상 **박막/세라믹** 값이지 벌크 fused silica(2.20)가 아니다.
  → 우리 S2는 논문 재현이 아니라 새 측정.

## S1 첫 결과 (single point, `02_run/s1_sanity/in.sp_nano`)

BKS 구조(2160원자, 28.73×28.83×33.27 Å, ρ=2.607 g/cm³)에 7net-nano-5.5 적용:

```
PotEng   -16715.923 eV      v_epa  -7.7389 eV/atom     ← 정상 규모
Press    +93,941 bar ≈ 9.4 GPa                          ← 핵심
c_maxf   5.574 eV/Å (최대 원자력)                        ← 정상 범위
FullNghs 296,870  (137.4 /atom)
원소매핑  O→type1, Si→type2 확인
```

**해석**: 운동에너지 기여(nk_BT ≈ 3,250 bar, 3.5%)를 빼도 virial 압력이 **+9 GPa**.
SevenNet-Nano는 BKS의 2.607 g/cm³ 구조를 강하게 압축된 상태로 본다 → 0 bar 이완 시 팽창, 밀도 하락 예상.
**단 크기는 추정하지 말 것** — 실리카는 압력-부피 응답이 anomalous(3 GPa 부근 K 감소)라 선형 외삽 무효.

## 반드시 지켜야 할 실행 규칙 (전부 "조용히 틀리는" 함정)

1. **`ulimit -s 262144`** — `pair_e3gnn.cpp`가 edge 배열을 스택 VLA로 잡음.
   2160원자 = 296,870 edge × 28 byte = 8.3 MB > 기본 8 MB → **세그폴트**. 실측으로 확인됨.
   hard limit이 262144(=root 없이 최대)라 상한은 약 900만 edge ≈ 6만 원자.
2. **`pair_style e3gnn`에 `mpirun` 쓰지 말 것.** 로컬 tag map에 없는 이웃을 버리므로 도메인 분할 시
   edge가 누락되고 **에러 없이 힘이 틀린다.** 단일 랭크 + OMP 스레드로 병렬.
   (`e3gnn/parallel`은 GPU 전용이라 이 빌드에 없음 — CUDA 무가드 의존 때문에 빌드 시 제거함)
3. **랭크 × 스레드 ≤ 6.** SevenNet = 1랭크×6스레드, BKS = 6랭크×1스레드.
   `.bashrc`의 `OMP_NUM_THREADS`는 **1**로 두고 명령 앞에서 덮어쓸 것.
4. **`pair_coeff * * <pt> O Si`** — 원소 순서가 LAMMPS type 순서(1=O, 2=Si)와 일치해야 함. 틀려도 에러 안 남.
5. **BKS는 빌드에 쓴 Intel MPI launcher로** 실행. OpenMPI도 설치돼 있어 섞이면 같은 계산을 N번 반복함.
6. conda `mlip` 환경을 지우면 `lmp_7net`이 libtorch를 못 찾아 **LAMMPS 재빌드** 필요.

## 바로 다음 할 일

1. **속도 실측** — `02_run/s1_sanity/in.timing_nano` (run 20, NVE, `neighbor 1.0 bin`).
   `Loop time` → 원자-스텝/초. 같은 계를 BKS로도 돌려 배수 산출. **이 자체가 발표 자료.**
2. **ASE 교차검증** — `SevenNetCalculator('7net-nano-5.5')`로 같은 구조 single point.
   LAMMPS 값(-16715.923 eV)과 일치하는지 → 배포 경로 검증.
3. **1랭크 vs 2랭크 에너지 비교** — 위 규칙 2를 데이터로 확정.
4. `02_run/s1_sanity/NOTE.md` 작성 (조건·이유·결과 한 줄씩).

## 미해결 / 결정 필요

- **AIMD 참고문헌 확정.** 1순위 후보: Farnesi Camellone et al., **arXiv:1109.2852** (GGA,
  *BKS 구조를 DFT로 이완* — 우리 워크플로와 동일). digitize 전에 functional이 PBE인지 PW91인지,
  셀 크기·밀도·g(r) 축 범위 확인 필요. 차선: Benoit et al. EPJB 13, 631 (2000) [BLYP],
  Sarnthein et al. PRL 74, 4682 (1995) [LDA] — functional 불일치가 변수로 추가됨.
- **런 A/B 설계**: 밀도가 RDF의 경계조건이므로 (A) NVT @ ρ=2.607 고정으로 포텐셜만 비교 [1순위],
  (B) NPT @ 0 bar로 각자 평형밀도. 상세는 `05_doc/S0c_RDF_comparison_plan.md`.
- **기존 분석 코드 재활용 가능 여부** 미확인 (RDF/배위수, POSCAR↔LAMMPS 변환). 새로 짜지 말 것.
- D3는 쓰지 않음 (mpa 채널이 D3 없는 PBE).

## 참고 문서

- `00_env/SETUP_FROM_SCRATCH.md` — 새 머신 재현 절차 (검증 게이트 포함)
- `00_env/INSTALL.md` — 경로 선택 근거, 에러 대응표
- `05_doc/S0_sevennet_nano_overview.md` — 논문 정리
- `05_doc/S0c_RDF_comparison_plan.md` — 비교 설계, AIMD 후보
