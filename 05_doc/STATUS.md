# STATUS — 인수인계 (갱신 2026-08-13)

## 프로젝트 한 줄

BKS(고전 포텐셜)로 만든 비정질 SiO₂에 범용 MLIP **SevenNet-Nano**를 적용해,
**ρ = 2.20 g/cm³ (실험값)에서 BKS · MLIP · AIMD(PBE) · 실험**을 비교한다.
목적: 취업 포트폴리오/면접 자료 (코닝, ASM, LG디스플레이).

**결과 요약은 `05_doc/RESULTS.md`.** 이 문서는 진행 상태·환경·실행 규칙만 다룬다.

## 진행 상태

| 단계 | 상태 |
|---|---|
| S0 환경 구축 | **완료** — LAMMPS + `pair_style e3gnn` 빌드·검증·배포 |
| S0′ 구조 재생성 | **완료** — 1차 melt-quench 실패 진단 후 ρ=2.20 고정 NVT로 재수행 |
| S1 sanity + 속도 실측 | **완료** — 단일점, ASE 교차검증, 랭크 비교, 속도, cutoff 스윕, 병렬 확장성 |
| S2′ 구조 이완 + E–V | **완료** — 7net ρ₀ 2.2185 / K₀ 43.2, BKS(tail on) 2.3442 / 34.3 |
| S3′ RDF + 결합각 | **완료** — 300 K NVT 5 ps, g(r)·BAD·ring 통계, AIMD digitize 비교 |
| S4 짧은 MD | 생략 (S3′가 대체) |
| S5 정리 | **진행 중** — 그림 5장·RESULTS.md 완료, 남은 항목은 아래 |

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
동기화 GitHub vkxlzptm/SiO2-MLIP — **양쪽 다 `./sync.sh` 한 줄**
생산 모델  7net-nano-4.5 → 01_input/pot/deployed_nano_4.5.pt
      (4.5/5.0/5.5/6.0 모두 배포돼 있음. 5.5 = deployed_serial.pt)
```

## 반드시 지켜야 할 실행 규칙 (전부 "조용히 틀리는" 함정)

1. **`ulimit -s 262144`** — `pair_e3gnn.cpp`가 edge 배열을 스택 VLA로 잡는다.
   `neighbor 2.0` 기준 2160원자 = 296,870 edge × 28 byte = 8.3 MB > 기본 8 MB → **세그폴트**.
   **1b. e3gnn 은 `neighbor 1.0 bin` 을 기본으로.** skin만 줄여도 190,870 edge(5.3 MB)로
   떨어지고 에너지·힘은 소수점 6자리까지 불변(S1 실측).
2. **`pair_style e3gnn` 에 `mpirun -np 2` 이상 금지.** 도메인 분할이 잡히고 `read_data`까지
   간 뒤 **rank1 SIGSEGV로 즉사**. OOM 아님(dmesg 확인), LAMMPS 코어 MPI 정상(같은 바이너리로
   BKS는 2랭크 완주). 운용: **단일 랭크 + OMP 스레드**.
3. **랭크 × 스레드 ≤ 6.** SevenNet = 1랭크×6스레드, BKS = 6랭크×1스레드.
   HT(12스레드)는 이득 0. `.bashrc`의 `OMP_NUM_THREADS`는 1로 두고 명령 앞에서 덮어쓸 것.
4. **`pair_coeff * * <pt> O Si`** — 원소 순서가 LAMMPS type 순서(1=O, 2=Si)와 일치해야 함.
   틀려도 에러 안 남.
5. **BKS는 빌드에 쓴 Intel MPI launcher로** 실행. OpenMPI도 설치돼 있어 섞이면 같은 계산을 N번 반복.
6. **모든 입력에 `velocity all set 0.0 0.0 0.0`** (단일점·최소화용) 또는 명시적 `velocity create`(MD용).
   data 파일이 속도를 들고 다녀서 `press`에 운동에너지 항이 조용히 섞인다. S2-2에서 virial
   검증이 3배 어긋나 보였던 원인.
7. **`box/relax` 에는 `etol = 0.0`.** 셀 자유도 방향으로 엔탈피가 평탄해 `etol=1e-8`이
   힘 수렴 전에 먼저 걸린다(S2-1에서 확인).
8. **`compute rdf ... cutoff 8.0` 을 쓰면 `comm_modify cutoff 9.0` 필수.**
   e3gnn의 ghost 범위는 pair cutoff 기준(4.5+1.0=5.5 Å)이라 그대로면 에러로 죽는다.
   BKS는 buck cutoff 10+skin 2.0=12 Å이라 우연히 문제가 없다.
9. **melt-quench 는 부피고정 NVT 로, NPT 는 300 K 평형에서만.** 그리고 **MSD 로 완전 용융을
   검증할 것.** 1차 실패의 직접 원인 (`02_run/_v1_superseded/README.md`).
10. conda `mlip` 환경을 지우면 `lmp_7net`이 libtorch를 못 찾아 **LAMMPS 재빌드** 필요.
11. **잘린 고전 포텐셜로 EOS를 할 땐 (a) tail 보정을 켜고 (b) virial P(V)를 피팅할 것.**
    BKS의 `−C/r⁶`를 10 Å에서 그냥 자르면 부피가 변할 때 원자쌍이 cutoff를 넘나들며
    E가 계단처럼 튀는데 virial은 그 계단을 못 봐서 **−dE/dV ≠ P_virial** 이 된다
    (실측 오프셋 평균 −2,415 bar). `pair_modify pair <style> tail yes` 로 −226 bar 까지 준다.
    **tail 보정은 힘에 기여하지 않는다**(V만의 함수) — 구조는 그대로고 E·P 장부만 바뀐다.
    LAMMPS가 더하는 값: E에 A/V, virial P에 **2A/V²** (2배인 게 핵심. 그 덕에 두 경로가 맞는다).
    MLIP는 매끄러운 cutoff 함수를 써서 해당 없음 — 7net은 보정 없이도 두 경로가 0.4 % 일치.
    ※ tail on/off로 BKS K₀가 34.3↔38.0 (10 %) 움직인다. 관례를 반드시 명시할 것.

## 비용 모델 (실측 기반, 2160원자)

```
7net-nano :  s/step ∝ r_c³ 이고 edge 수(∝ 밀도)에 비례
             ρ=2.607 : 4.5→2.401 s,  5.0→3.314,  5.5→4.418,  6.0→5.623
             ρ=2.20  : 4.5→1.995 s   (예측 2.026 대비 −1.7 %)
BKS       :  1.35 Matom-step/s @ρ=2.20 (6랭크)  → 배수 1,244×
병렬      :  스레드 1→12 = 1.83× (4에서 포화), 프로세스 1→6 = 1.98×
             → **메모리 바운드. 이 머신 천장 ≈ 1,000 atom-step/s**
```

작업 계획 시: **force eval 1회 = 2.0초** (7net-nano-4.5 @ρ=2.20, OMP=6).

## 디렉토리

```
01_input/          BKS quench 산물(1차, 폐기), 포텐셜 .pt, vt_profile.dat
02_run/
  s0_requench/     ★ 현행 구조 생성 (ρ=2.20 NVT) + BKS RDF·궤적
  s1_sanity/       속도·virial·cutoff 스윕 (구조 무관, 유효)
  s2_relax/        ★ 7net 정적 이완 + E–V (in.relax220, in.ev220)
  s3_md/           ★ 7net NVT MD 5 ps → RDF·BAD
  _v1_superseded/  ρ=2.607 기반 폐기물 (README.md 에 경위)
04_analysis/
  src/             분석·작도 스크립트 (경로는 __file__ 기준, 어디서든 실행 가능)
  dat/             digitize 결과, ring 통계
  fig/             fig_pdf / fig_bad / fig_density / fig_speed / fig_rings (PNG 300dpi)
  src/old_delete/  폐기 스크립트 — `./cleanup.sh --yes` 로 정리 (샌드박스는 삭제 권한 없음)
05_doc/            README.md(색인) / RESULTS.md(결과) / STATUS.md(이 문서) + 문헌·그림

sync.sh            git 동기화 (양쪽 다 이거 한 줄)
cleanup.sh         폐기 파일 정리 (드라이런 기본, --yes 로 실삭제)
```

## 남은 일

1. **`./cleanup.sh` 실행** — 폐기 파일 정리 (드라이런이 기본, 실삭제는 `--yes`).
   대상: `init_struct/`(01_input 과 비트 동일), `04_analysis/*/old_delete/`, `03_result/`,
   1차 BKS 스캔 잔재, `.DS_Store`. 약 1.3 MB.
   **남기는 것과 이유**도 스크립트 하단에 적어뒀다 (`_v1_superseded/`, tail 대조군 로그 등).
2. ~~그림 라벨 통일~~ **완료** — 논문 표기 `7net-Nano-4.5` 로 5장 전부 재생성.
   ※ `00_env/*`, `ase_crosscheck.py`, 위 '확정된 환경'의 소문자 `7net-nano-*` 는
     **checkpoint 리터럴**이라 그대로 둔다. 바꾸면 `sevenn cp` 명령이 깨진다.
3. **§3(b) 밀도-결합길이 논증 재검토** — ρ ∝ d⁻³ 휴리스틱이 입력(평균 vs 피크 Si–O)에
   따라 −4.0 ~ −5.4 % 를 오간다. 이전 판의 "0.03 %p 일치" 는 재현 불가라 삭제했다.
   제대로 하려면 각 부피에서의 결합길이·각도 변화를 직접 재야 한다 (E–V 스캔 구조에서
   추출 가능, 추가 MD 불필요). 안 할 거면 지금의 정성 서술로 두면 된다.
4. (선택) **S(q) 계산** — g(r) 푸리에 변환으로 FSDP를 실험 1.52 Å⁻¹ 과 비교. 추가 계산 불필요
5. (선택) **excess energy** — Erhard et al.의 주요 지표(실험 78–131 meV/SiO₂).
   α-quartz 단일점 하나만 추가하면 됨 (7net 으로 1분)
6. (선택) **7net 어닐링** — 중거리 구조를 마저 고치려면 필요. 20 ps에 11시간

## 참고 문서

**`05_doc/README.md` 가 색인이다** — 어느 문서가 현행이고 어느 게 기록인지 거기 정리돼 있다.
(파일명의 S0/S0c/S3 번호는 착수 당시 계획 기준이라 실제 진행과 어긋난다. 순서를 믿지 말 것.)

- `05_doc/RESULTS.md` — **결과 요약 (여기부터 읽을 것)**
- `00_env/SETUP_FROM_SCRATCH.md` — 새 머신 재현 절차
- `02_run/*/NOTE.md` — 각 단계의 조건·이유·결과 한 줄 기록
