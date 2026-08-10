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

## 미측정 / 열린 항목

- 순수 LJ(쿨롱·kspace 없음) 속도는 **측정하지 않았음**. BKS의 kspace 비중(19.3 %)으로 볼 때 LJ가 더 빠를 것은 분명하나 배수는 추정하지 않는다. 필요하면 별도 5초 벤치로 실측할 것.
- 스레드 스케일링(OMP 1/2/4/6) 미측정. e3gnn이 6스레드에서 실제로 스케일하는지는 확인 안 됨 — 발표 자료에 "6코어 활용" 이라고 쓰려면 재야 함.
- 2랭크 크래시의 정확한 지점(백트레이스) 미확보. 운용상 불필요하므로 추적 안 함.
