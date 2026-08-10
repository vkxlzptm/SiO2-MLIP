# 02_run/s1_sanity — NOTE

계: BKS melt-quench 산물 `01_input/sio2_quenched.data`
2160 atoms (720 Si / 1440 O), 28.7283 × 28.8287 × 33.2702 Å, V = 27,554.3 Å³, ρ = 2.6071 g/cm³
포텐셜: 7net-nano-5.5 → `01_input/pot/deployed_serial.pt`
하드웨어: i5-11600K 6c12t, GPU 없음, RAM 15 GB

형식: `날짜 | 실행 | 조건 | 이유 | 결과`

---

## S1-0 단일점 (기존)

- 2026-08-10 | `in.sp_nano` | run 0, `neighbor 2.0` 추정, data 파일 속도 포함 | 배포 포텐셜이 물리적으로 말이 되는지 첫 확인 | PotEng −16715.923 eV (−7.7388532 eV/atom), Press +93,941.1 bar, maxF 5.5737669 eV/Å, FullNghs 296,870 (137.4/atom)

## S1-3 랭크 비교 (→ 규칙 2 확정)

- 2026-08-10 | `in.sp_check` `mpirun -np 1` (OMP=6) | run 0 | 1랭크 기준값 | PotEng −16715.923 / Press 93,941.059 / Pxx 95,965.0 Pyy 95,886.1 Pzz 89,972.0 / c_maxf 5.5737669 → **`in.sp_nano` 완전 재현**
- 2026-08-10 | `in.sp_check` `mpirun -np 2` (OMP=3) | 동일 | e3gnn이 도메인 분할에서 조용히 틀리는지 확인 | **크래시.** `1 by 1 by 2 MPI processor grid` 잡히고 `read_data` 통과 후 rank1 SIGSEGV, rank0 SIGKILL(런처 정리로 추정). 에너지 출력 도달 못 함
- 2026-08-10 | `dmesg -T \| grep -i oom` | — | SIGKILL이 OOM인지 판별 | **OOM 기록 없음** → 메모리 아님
- 2026-08-10 | `in.timing_bks` `mpirun -np 2` | 동일 계, 동일 바이너리 `lmp_7net` | LAMMPS 코어 MPI 자체가 멀쩡한지 분리 | **정상 완주**, 0.479 Matom-step/s. → MPI 코어 정상, KSPACE 패키지 포함 확인
  - **결론: 크래시 원인은 `pair_style e3gnn`에 국한.** STATUS 규칙 2를 강화 — 이 빌드·이 계에서는 "조용히 틀리는" 게 아니라 **즉시 죽는다**. 단 확인된 건 2160원자/2랭크 1건뿐이므로 "항상 죽는다"로 일반화 금지. 운용 규칙은 그대로: **e3gnn은 1랭크 + OMP만**

## S1-2 ASE 교차검증 (→ 배포 경로 통과)

- 2026-08-10 | `in.sp_check` + `velocity all set 0 0 0`, `mpirun -np 1` | data 파일 속도를 죽여 Press를 순수 virial로 | ASE stress와 사과 대 사과 비교하려고 | Temp 0, PotEng −16715.923, FullNghs 190,870 (88.4/atom, `neighbor 1.0`)
- 2026-08-10 | `ase_crosscheck.py` | `SevenNetCalculator('7net-nano-5.5')`, 동일 구조 | deploy 과정에서 조용히 틀어졌는지 검증 | E_total **−16715.922993 eV** / E/atom −7.738853 / \|F\|max **5.5738 eV/Å** / \|F\|mean 1.7325 / sum(F) 1.4e−05 / P_virial **90,669.6 bar** → LAMMPS와 소수점 6자리 일치. **배포 경로 검증 통과**

### 여기서 확정된 것 2가지

1. **압력은 +9.07 GPa (순수 virial)**, 9.4 GPa 아님.
   93,941.1 − 90,669.6 = **3,271.5 bar** 가 운동에너지 항.
   N k_BT/V 로 역산하면 T = 302.3 K → data 파일이 300 K quench 종료 상태라는 것과 정합.
   결론(BKS 구조를 강하게 압축된 상태로 본다)은 불변.
2. **FullNghs 차이는 skin 때문이며 결과에 무해.**
   수밀도 0.078391 /Å³, 모델 cutoff 5.5 Å 기준
   `neighbor 2.0` → r=7.5 Å → ⁴⁄₃πr³·ρ = 138.5/atom (실측 137.4)
   `neighbor 1.0` → r=6.5 Å → 90.2/atom (실측 88.4)
   에너지·힘이 6자리까지 동일하므로 skin은 결과 무영향.
   **다만 규칙 1(스택)에 직결**: skin 1.0이면 190,870 edge × 28 B = 5.3 MB (기본 8 MB 안), skin 2.0이면 8.3 MB (초과 → 세그폴트).
   → **e3gnn 실행은 `neighbor 1.0 bin` 을 기본으로 한다.**

## S1-1 속도 실측 (→ 발표 자료 핵심 숫자)

측정 조건: 동일 계·동일 구조, NVE, `velocity create 300 K`, Neighbor list builds = 0 (순수 force eval)

| | SevenNet-Nano | BKS + pppm |
|---|---|---|
| 병렬 | 1 rank × 6 OMP | 6 rank × 1 OMP |
| 입력 | `in.timing_nano` (`neighbor 1.0`) | `in.timing_bks` (`neighbor 2.0`) |
| 측정 구간 | run 20 → Loop 88.3816 s | run 200 → Loop 0.358769 s |
| s/step | **4.419** | **1.794e−3** |
| atom-step/s | **488.8** | **1,204,000** |
| ns/day | 0.020 | 48.165 |

- **BKS가 SevenNet-Nano보다 2,463배 빠르다** (4.4191 / 1.7938e−3).
- warm-up `run 3` (488.557 atom-step/s) 과 본 측정 `run 20` (488.789) 이 사실상 동일 → 모델 로드/JIT 워밍업이 Loop time을 오염시키지 않음. 깨끗한 측정.
- BKS 랭크 스케일링: 2랭크 0.479 → 6랭크 1.204 Matom-step/s = 2.51배 (3배 랭크 대비 효율 84%). pppm 통신이 제한 요인 — 정상 패턴.
- BKS 6랭크 breakdown(2랭크 로그 기준): Pair 79.5 %, Kspace 19.3 %, Comm 0.9 %.

### MD 예산 (1 fs timestep 기준, 위 실측 그대로 환산)

| | SevenNet-Nano | BKS |
|---|---|---|
| 1 ps | 1.23 시간 | 1.8 초 |
| 10 ps | **12.3 시간** | 18 초 |
| 20 ps | 24.6 시간 | 36 초 |

→ S4(짧은 MD)는 **하룻밤 = 약 10 ps** 가 현실적 상한. S2/S3 설계에 반영할 것.

## S1-5 OMP 스레드 스케일링 (2026-08-10)

`in.timing_probe` (= `in.timing_nano`의 run 20 → run 3), mpirun 없이 직접 실행, 두 번째 `run 3` 기준.
i5-11600K = 물리 6코어 / 12논리스레드.

| OMP | Loop (3 step) | s/step | atom-step/s | CPU use | speedup |
|---|---|---|---|---|---|
| 1 | 24.3006 | 8.100 | 266.7 | **60.0 %** | 1.00 |
| 4 | 13.5215 | 4.507 | 479.2 | 291.9 % | 1.797 |
| 6 | 13.2641 | 4.421 | 488.5 | 441.0 % | 1.832 |
| 12 | 13.2502 | 4.417 | 489.1 | 447.6 % | 1.834 |

**결론 3가지**

1. **하이퍼스레딩(12)은 이득 없음.** 6 대비 0.1 % (노이즈 수준). STATUS 규칙 3(랭크×스레드 ≤ 6) 유지.
2. **스레드 병렬화 자체가 거의 안 먹는다.** 1→6이 **1.83배뿐**이고 4에서 이미 포화(4→6 = +1.9 %).
   CPU 441 %를 쓰면서 wall은 1.83배 → CPU-초당 유효 일은 41 %. 나머지는 OpenMP 배리어 스핀으로 추정.
   원인 추정: 7net-nano는 채널 32 / 3층으로 텐서가 작아 스레드 분할 이득 < 동기화 오버헤드.
   (논문이 GPU 벤치만 제시한 것과 정합. 단 이건 우리 추론이지 논문이 말한 바 아님.)
3. **OMP=1의 CPU 60 %는 설명 안 됨.** 단일 스레드인데 40 %가 idle.
   메모리 지연 바운드일 가능성이 높지만 확인 안 함. 운용 결론에는 영향 없어 추적 중단.

**파생 결론 — 리플리카 병렬이 스레드보다 3.3배 효율적**

스레드가 안 먹으므로, 독립 궤적을 **여러 개 동시에** 돌리는 게 총 샘플링 처리량에서 유리:

- OMP=6 단일 실행: 488.5 atom-step/s
- OMP=1 × 6개 동시 실행: 266.7 × 6 = **1,600 atom-step/s (3.28배)**

RDF는 앙상블 평균이므로 "10 ps 궤적 1개" 대신 "5 ps 궤적 6개"가 같은 벽시계 시간에 더 많은 통계를 준다.
**단 미검증 리스크 2가지**: (a) 6프로세스 × libtorch의 RAM 총량(15 GB 한계), (b) 실제 동시 실행 시
메모리 대역폭 경합으로 개당 속도가 떨어질 수 있음. 착수 전 2~3개로 실측할 것.
S2(단일 궤적 이완)에는 도움 안 되고 S3(RDF 샘플링)·A/B 런 설계에서만 유효.

## 미측정 / 열린 항목

- 순수 LJ(쿨롱·kspace 없음) 속도는 **측정하지 않았음**. BKS의 kspace 비중(19.3 %)으로 볼 때 LJ가 더 빠를 것은 분명하나 배수는 추정하지 않는다. 필요하면 별도 5초 벤치로 실측할 것.
- 2랭크 크래시의 정확한 지점(백트레이스) 미확보. 운용상 불필요하므로 추적 안 함.
- **cutoff 변종 미측정.** `7net-nano-4.5 / 5.0 / 5.5 / 6.0` 존재 확인(`sevenn/util.py` L292–299).
  로컬에는 5.5만 번들, 나머지는 첫 호출 시 자동 다운로드됨(4.5 다운로드 성공 확인, 458 KB).
  논문 권고: "accuracy exhibits **weak dependence on r_c**", 5.5가 robust default, 효율이 필요하면 4.5.
  **단 논문의 속도 이득은 우리에게 그대로 오지 않는다** — 논문은 cutoff 간 비용 차이를
  "primarily from **neighbor list construction** ... increasingly impacts performance as system size grows"
  로 귀속시켰는데, 논문 벤치는 GPU·최대 7만 원자이고 우리는 CPU·2160원자에 `Neighbor list builds = 0`이다.
  우리 쪽 이득은 edge 수 감소(r³: 5.5→4.5 = 0.55배)에서만 나오므로 1.8배보다 작을 것. **배수는 실측 전 추정 금지.**
- 리플리카 동시 실행의 RAM·대역폭 한계 미측정 (위 S1-5 파생 결론 참조).
