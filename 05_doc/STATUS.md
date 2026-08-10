# STATUS — S0 완료 시점 인수인계 (2026-08-10)

## 프로젝트 한 줄

BKS(고전 포텐셜)로 만든 비정질 SiO2 구조에 범용 MLIP **SevenNet-Nano**를 적용해,
**RDF(Si–O / O–O / Si–Si)를 BKS vs SevenNet-Nano vs AIMD(문헌 digitize) 3자 비교**한다.
목적: 취업 포트폴리오/면접 자료 (코닝, ASM, LG디스플레이). 목표 기간 3일.

## 진행 상태

| 단계 | 상태 |
|---|---|
| S0 환경 구축 | **완료** — LAMMPS + `pair_style e3gnn` 빌드·검증·배포까지 |
| S1 sanity + 속도 실측 | **완료** — 단일점·ASE 교차검증·랭크 비교·속도 실측 전부 끝 |
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

## S1 결과 (상세는 `02_run/s1_sanity/NOTE.md`)

BKS 구조(2160원자, 28.7283×28.8287×33.2702 Å, V=27,554.3 Å³, ρ=2.6071 g/cm³)에 7net-nano-5.5 적용:

```
PotEng    -16715.923 eV      v_epa  -7.7388532 eV/atom
Press     +90,669.6 bar = +9.07 GPa   ← 순수 virial (속도 죽인 값). 핵심
c_maxf    5.5737669 eV/Å    |F|mean 1.7325 eV/Å    sum(F) 1.4e-05
원소매핑   O→type1, Si→type2 확인
```

**검증 통과 3건**
- **ASE 교차검증**: `SevenNetCalculator('7net-nano-5.5')` = −16715.922993 eV, |F|max 5.5738.
  LAMMPS 배포본과 소수점 6자리 일치 → **deploy 경로 무결.**
- **압력 정정**: 기존 기록 93,941.1 bar에는 운동에너지 항 3,271.5 bar가 섞여 있었다
  (data 파일에 속도 섹션이 있어 `read_data`가 같이 읽음). 역산 T = 302.3 K로 300 K quench와 정합.
  **참값은 +9.07 GPa.**
- **랭크 비교**: 2랭크는 크래시(아래 규칙 2).

**속도 실측** (동일 계, NVE, neighbor 재빌드 0)

| | SevenNet-Nano (1랭크×6스레드) | BKS+pppm (6랭크×1스레드) |
|---|---|---|
| s/step | **4.419** | 1.794e−3 |
| atom-step/s | **488.8** | **1,204,000** |
| 10 ps MD | **12.3 시간** | 18 초 |

**BKS가 2,463배 빠르다.** → S4 MD는 하룻밤 ≈ 10 ps가 현실적 상한.

**해석**: SevenNet-Nano는 BKS의 2.607 g/cm³ 구조를 강하게 압축된 상태로 본다
→ 0 bar 이완 시 팽창, 밀도 하락 예상.
**단 크기는 추정하지 말 것** — 실리카는 압력-부피 응답이 anomalous(3 GPa 부근 K 감소)라 선형 외삽 무효.

## 반드시 지켜야 할 실행 규칙 (전부 "조용히 틀리는" 함정)

1. **`ulimit -s 262144`** — `pair_e3gnn.cpp`가 edge 배열을 스택 VLA로 잡음.
   `neighbor 2.0` 기준 2160원자 = 296,870 edge × 28 byte = 8.3 MB > 기본 8 MB → **세그폴트**. 실측 확인.
   hard limit이 262144(=root 없이 최대)라 상한은 약 900만 edge.
   **1b. e3gnn은 `neighbor 1.0 bin`을 기본으로 쓸 것.** skin만 줄여도 190,870 edge(5.3 MB)로 떨어지고
   에너지·힘은 소수점 6자리까지 불변(S1 실측). 스택 여유가 3배 늘어난다.
2. **`pair_style e3gnn`에 `mpirun -np 2` 이상 쓰지 말 것.** S1 실측: 도메인 분할이 잡히고
   `read_data`까지 간 뒤 **rank1 SIGSEGV로 즉사**(rank0 SIGKILL은 런처 정리). OOM 아님(dmesg 확인),
   LAMMPS 코어 MPI 정상(같은 바이너리로 BKS는 2랭크 완주). **원인은 e3gnn에 국한.**
   → 이 빌드에서는 "조용히 틀린 힘"이 아니라 크래시로 드러난다. 다만 확인된 건 2160원자/2랭크 1건이므로
   다른 조건에서 조용히 틀릴 가능성은 배제 못 함. 운용 규칙은 동일: **단일 랭크 + OMP 스레드.**
   (`e3gnn/parallel`은 GPU 전용이라 이 빌드에 없음 — CUDA 무가드 의존 때문에 빌드 시 제거함)
3. **랭크 × 스레드 ≤ 6.** SevenNet = 1랭크×6스레드, BKS = 6랭크×1스레드.
   `.bashrc`의 `OMP_NUM_THREADS`는 **1**로 두고 명령 앞에서 덮어쓸 것.
4. **`pair_coeff * * <pt> O Si`** — 원소 순서가 LAMMPS type 순서(1=O, 2=Si)와 일치해야 함. 틀려도 에러 안 남.
5. **BKS는 빌드에 쓴 Intel MPI launcher로** 실행. OpenMPI도 설치돼 있어 섞이면 같은 계산을 N번 반복함.
6. conda `mlip` 환경을 지우면 `lmp_7net`이 libtorch를 못 찾아 **LAMMPS 재빌드** 필요.

## 바로 다음 할 일 (S2 구조 이완)

**전제: force eval 1회 = 4.42 s.** 모든 설계는 "force eval 몇 회인가"로 비용을 환산할 것.

1. **S2 설계 결정 먼저** — `fix box/relax` + `minimize` (정적 이완, 수백 회 eval = 30분~1시간)로 갈지,
   NPT MD(수천 회 eval = 하룻밤)로 갈지. 착수 전 확인받을 것.
2. **S3 RDF 샘플링 예산** — 10 ps = 12.3 시간. 2160원자면 통계는 충분하나 평형화 구간을 빼야 함.
3. **cutoff 변종 실측** — `7net-nano-4.5/5.0/6.0` 배포 후 같은 구조 단일점 + 타이밍.
   압력 +9.07 GPa가 cutoff에 robust한지 확인 = 공짜 검증. CPU에서 남은 거의 유일한 속도 레버.
4. 미측정: 순수 LJ 속도. BKS의 kspace 비중 19.3 %만 근거 — 배수는 추정하지 말고 필요하면 실측.

### S1-5에서 추가된 성능 사실 (중요)

**스레드 병렬화는 이미 천장이다.** OMP 1→6이 겨우 **1.83배**, 4에서 포화, **12(HT)는 이득 0**.
CPU 441 %를 쓰면서 wall은 1.83배 → CPU-초당 유효 일 41 %. 모델이 작아(채널 32/3층)
텐서 분할 이득이 동기화 오버헤드에 먹히는 것으로 추정.
→ **코어를 더 붙여도 답이 없다. 속도 레버는 cutoff 축소와 리플리카 병렬뿐.**

**리플리카 병렬 = 1.12배뿐** (S1-7 실측. 3.3배 예측은 반증됨)
프로세스 6개 동시 실행 시 개당 3.03배 감속 → 총 1,007 atom-step/s vs OMP=6 단일 899.5.
RAM은 프로세스당 2.1 GB로 6개가 하드 상한(여유 2 GB).
→ **S2·S3 전부 OMP=6 단일 실행.** 리플리카는 복잡도 값어치 없음.

**관통하는 설명: 이 워크로드는 메모리 바운드다.**
OMP=1의 CPU 60 %, 스레드 1.83배 포화, 프로세스 3.03배 감속 — 셋 다 같은 원인.
채널 32/3층이라 산술 강도가 낮아 대역폭 벽에 부딪힘.
**이 머신 천장 ≈ 1,000 atom-step/s. 병렬화로는 못 넘는다.**

**생산 모델 = `7net-nano-4.5`** (`01_input/pot/deployed_nano_4.5.pt`), 2.401 s/eval @ OMP=6.
근거: 압력 산포 ±3.2 %로 물리 결론 불변, 5.5 대비 1.84배 빠름, 논문도 효율 필요 시 4.5 권고.

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
