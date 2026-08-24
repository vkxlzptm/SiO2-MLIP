# 새 채팅 시작 프롬프트 — S4 (7net 자체 melt-quench)

> **2026-08-24 (2차 갱신).** S4 본런 완료. Tg 그림(`fig_tg_s4.png`) + **ring 해석 완료
> (`fig_rings_s4.png`)** + **P300 부호 반전 검증 완료(추가 계산 없이 로그로 결론)**.
> 남은 것은 전부 **dhl-desktop 에서 사용자가 직접 돌려야 하는 계산**이다.
> 해석 근거는 전부 `NOTE.md` 의 "S4 분석 1/2" 절에 있다.

---

## 새 세션에 붙여넣을 프롬프트

SiO2-MLIP 프로젝트, S4 단계(7net 자체 melt-quench)를 이어간다. 폴더는 이미 연결돼 있다.

**먼저 이 순서로 읽어라.**

1. `02_run/s4_mq7net/NEXT_SESSION_PROMPT.md` — 이 문서. S4 진행 상황·수치·미결 항목
2. `02_run/s4_mq7net/NOTE.md` — S4 설계 근거(냉각률 선택, MSD gate, resume 절차)
3. `05_doc/RESULTS.md` — S4 이전(BKS 위상 상속 기준) 수치의 유일한 출처
4. `04_analysis/src/fig_tg_s4.py`, `fig_rings_s4.py` — 두 핵심 그림 스크립트.
   docstring에 방법론·비교 설계·오차 처리 근거가 다 들어 있다

**바로 이어서 할 일** (아래 "남은 작업" 순서대로):
1. dhl-desktop 에서 `run_bks_sweep.sh` 실행 → 끝나면 `fig_tg_s4.py` **와**
   `ring_stats.py`(새로 생기는 `prod_bks_*.data` 에) 재실행 → `fig_rings_s4.py` 재실행
2. dhl-desktop 에서 `run_ev_s4.sh` 실행 (0 K E-V 스캔, ~45분) → 자체 형성 망의 ρ₀·K₀
3. `traj_analyze.py` / `sq_direct.py` 를 S4 궤적에 실행

---

## 배경 — 왜 S4를 하고 있는가

기존 파이프라인은 항상 BKS로 melt-quench하고 7net은 그 구조를 relax/MD만 했다. 즉
**7net이 그동안 한 번도 자기 힘으로 비정질 망을 만들어본 적이 없다.** PPT p.6 "Next step"의
질문 — "7net 스스로도 현실적인 SiO2 망 위상을 만들 수 있는가?" — 에 답하려면 7net 자체
melt-quench가 필요했다.

**셀은 기존과 동일하게 2160원자(Si 720/O 1440), ρ=2.20 g/cm³ 고정 NVT**를 썼다 — 셀 크기를
바꾸면 ring statistics·S(q)·밀도가 다 사이즈에 민감해져 기존 결과와 비교가 안 된다는 이유로
사용자가 명시적으로 요구했다.

**냉각률은 BKS의 4000K 액체를 출발점으로 재평형(MSD gate) 후 2×10¹³ K/s**(100K/5ps)로
300K까지 낮췄다. 이 속도와 **정확히 같은 속도의 BKS 통제런**을 짝지어 돌렸고, 추가로
5×10¹²·5×10¹³ K/s BKS 런도 돌렸다 — "포텐셜 차이"와 "냉각률 차이"를 분리해서 보기 위해서다.
(이 설계에 도달하기까지 냉각률 후보를 여러 번 재협상했다. 다시 논쟁하지 말 것 — 결론은
`NOTE.md`에 근거와 함께 있다.)

### 비교 프레임워크 (중요 — 새 개념이니 명확히 인지할 것)

- **기존 `fig_density.py` 결과** = 같은 BKS 망 위상 위에서 각 포텐셜이 0K 정적 이완만 한 것
  → **순수 "포텐셜/이완 효과"**
- **이번 S4 결과** = 각 포텐셜이 **자기 힘으로 형성한** 위상, 냉각률까지 맞춤
  → **"포텐셜 효과 + 위상 형성 효과"의 합**
- 두 결과의 차이가 **"위상 형성 효과"** — 지금까지 한 번도 측정한 적 없는 양이다.

---

## 완료된 계산

| 런 | 조건 | 상태 |
|---|---|---|
| 7net 본런 | BKS 4000K 액체 재평형 → 2×10¹³ K/s 급랭, ρ=2.20 NVT | ✅ 완료 (wall time 122:33:32) |
| BKS 2×10¹³ K/s | 7net과 동일 속도 통제런 | ✅ 완료 |
| BKS 5×10¹² K/s | 통제런 | ✅ 완료 |
| BKS 5×10¹³ K/s | 통제런 | ✅ 완료 |
| BKS 확장 스윕 (1e12/2e12/1e13/1e14/2e14 + 2e13 반복 2개) | `run_bks_sweep.sh` | ❌ **미실행** — 다음 섹션 참조 |

## 핵심 결과 1 — Tg (`fig_tg_s4.png`, `tg_s4_summary.dat`)

```
run         rate(K/s)   Tg_arrest(K)  Tg_caloric(K)  P300(GPa)
7net        2.0e+13     2000          2431           0.80
BKS 2e13    2.0e+13     2800          2962          -3.07
BKS 5e12    5.0e+12     2700          2908          -2.79
BKS 5e13    5.0e+13     3000          2468          -3.19
```

- **kinetic-arrest Tg**: ΔMSD/100K 구간이 잡음 수준(0.10 Å², 5구간 연속) 아래로 떨어지는 온도.
  1차 지표로 채택 — 확산 정지라는 물리를 직접 본다. 임계값(0.10)과 연속조건(K=5)은
  T≤1000K 구간 ΔMSD의 p95를 4개 런에서 다 구해 가장 시끄러운 곡선의 3배로 잡은 것이고,
  임계값×K 격자를 스캔해 안정적인 조합인지 확인했다 — **재도출하지 말 것**, `fig_tg_s4.py`
  docstring과 이 세션 로그에 근거가 다 있다.
- **같은 냉각률(2×10¹³)에서 7net Tg(2000K)가 BKS(2800K)보다 800K 낮다.** 매칭된 속도이므로
  이 차이는 냉각률 아티팩트가 아니라 **포텐셜(→위상 형성 경로) 차이**로 봐야 한다.
- **P300 부호가 갈린다**: 7net은 +0.80 GPa(팽창하려는 경향), BKS 세 런은 전부 −2.8~−3.2 GPa.
  ✅ **검증 완료 (2026-08-24)**: 300K 10ps 전 구간에서 압력 드리프트 < 0.02 GPa,
  MSD 는 소수 3자리까지 고정. **미평형 아티팩트가 아니다** — "핵심 결과 3" 참조.
- caloric Tg(E(T) 이중직선 교점)는 참고용 2차 지표. arrest 기준 ±400K로 창을 재배치해서
  피팅했다 (고정창을 쓰면 냉각률별 실제 전이온도가 다른 채로 섞여 비단조 결과가 났었다).

## 핵심 결과 2 — Ring statistics (**해석 완료**)

그림 `04_analysis/fig/fig_rings_s4.png` · 스크립트 `04_analysis/src/fig_rings_s4.py`
수치 `dat/S4_rings_summary.dat` · 강건성 `dat/S4_rings_robust.dat` (`src/ring_robust_s4.py`)
**해석 전문과 근거는 `NOTE.md` "S4 분석 1" 절에 있다. 여기는 결론만.**

| n | 7net | BKS 평균 | BKS 최소~최대 | 차이(%p) | σ |
|---|---|---|---|---|---|
| 3 | **7.17** | 2.81 | 1.80 ~ 3.43 | **+4.35** | **3.0** |
| 4 | 15.58 | 14.92 | 14.24 ~ 15.54 | +0.66 | 0.3 |
| 5 | **24.82** | 30.79 | 29.97 ~ 31.61 | **−5.97** | **2.2** |
| 6 | 31.65 | 30.97 | 27.45 ~ 35.69 | +0.68 | 0.2 |
| 7 | 15.67 | 16.45 | 14.83 ~ 18.26 | −0.78 | 0.4 |
| 8 | 4.73 | 3.81 | 3.34 ~ 4.17 | +0.93 | 0.8 |
| 9 | 0.38 | 0.25 | 0.13 ~ 0.33 | +0.13 | 0.4 |

★ **BKS 표본을 4개로 늘렸다.** S4 BKS 3종은 같은 시드·같은 액체에서 갈라진 것이라
서로 독립이 아니다(그 폭은 냉각률 효과지 통계 산포가 아니다). 그래서 s0_requench 의
BKS 220 런(seed 77213, 200 ps 용융, 5e12 K/s)을 넣었다 — 같은 냉각률·다른 실현이고,
**기존 실험에서 7net 이 물려받았던 바로 그 망**이다.

**살아남은 결론**
- **3-ring: 7net 7.17 % vs BKS 상한 3.43 % (2.1배), 3.0σ.** 냉각률 10배 변화로도
  BKS 는 2.95~3.43 % 안에서만 움직인다 → 냉각률 아티팩트가 아니다.
- **5-ring 은 반대로 −5.97 %p (2.2σ).** 평균 고리 크기 7net 5.488 vs BKS 5.533~5.580.
- 물려받았을 때 1.80 % → 스스로 만들었을 때 7.17 %, **4배**. 이게 위상 형성 효과다.

**폐기된 예비 관찰** (첫 판에서 썼다가 독립 실현을 넣고 사라진 것)
- ~~"6-ring 이 7net 에서 가장 높다"~~ → BKS 실현간 폭이 27.45~35.69 %(8 %p)로 가장 넓고
  7net 은 그 한가운데(0.2σ). **"7net 망이 더 결정질에 가깝다" 류 서술 금지.**
- ~~"BKS 세 런이 좁게 모여 있으니 통계적으로 안정"~~ → 세 런은 독립 표본이 아니다.

**검증 통과** (자세한 표는 NOTE.md)
- RCUT 1.85~2.15 Å 스윕에서 3-ring 순위가 한 번도 안 뒤집힌다 → 결합 cutoff 아티팩트 아님
- 다섯 구조 모두 다리 O ≥ 99.58 %, Si 배위≠4 가 0~5개 → 7net 망도 BKS 만큼 깨끗함.
  결함 신호 아님 (7net 은 Si 배위≠4 가 **0개**로 오히려 가장 좋다)
- 300 K 미평형도 아님 (아래 핵심 결과 3)

**⚠ 반드시 병기할 한계**: 7net 은 시드 1개다. 3.0σ 의 실현간 오차 성분은 전부 BKS 에서
추정한 것이다. 발표 문장은 "유의하다"가 아니라 **"BKS 의 실현간 산포를 기준으로 재면
3σ 수준이고, 7net 자체 반복이 없어 그 이상은 말할 수 없다"** 로 쓴다.
그리고 ring 분포에는 **실험 계열이 없다** — "실물 유리와 다르다"의 근거로 쓸 수 없다.

⚠ **기존 `fig_rings.png`(06_ppt 덱 3페이지)와 헷갈리지 말 것**: 그건 "7net 이 BKS 가 만든
위상을 그대로 물려받는다"는 **다른 실험**이다. 같은 그림에 섞지 말고, 대비시키려면
나란히 놓아라 (fig_rings_s4.png 패널 (c) 가 s0 점에 화살표로 그 대비를 표시해 둔다).

## 핵심 결과 3 — P300 부호 반전은 **미평형이 아니다** (추가 계산 없이 결론)

기존 `logs/*.log` 의 300 K 10 ps(평형 5 + 생산 5)를 전·후반으로 갈라 압력 평균:

| 런 | 평형 전반 | 평형 후반 | 생산 전반 | 생산 후반 | 요동 sd |
|---|---|---|---|---|---|
| **7net** | **+0.781** | **+0.774** | **+0.797** | **+0.795** | 0.117 |
| BKS 2e13 | −3.118 | −3.054 | −3.025 | −3.041 | 0.121~0.206 |
| BKS 5e12 | −2.797 | −2.745 | −2.755 | −2.844 | 0.079~0.123 |
| BKS 5e13 | −3.245 | −3.154 | −3.262 | −3.261 | 0.067~0.133 |

드리프트가 요동 sd 의 1/5 미만, 단조 추세 없음. 같은 구간 MSD 는 소수 3자리까지 고정
(300 K 확산 0). → **+0.80 GPa 는 얼어붙은 망 위상 자체의 성질이다.**
300 K NVT 를 더 끌어봐야 움직일 자유도가 없다.

**그래서 NPT tail 검증은 폐기하고 0 K E-V 스캔으로 대체했다.**
7net 300 K NPT 100 ps = 54 시간(불가). E-V 9점 = 45분이고, **RESULTS 2절의
ρ₀ = 2.2185 / K₀ = 43.2 가 정확히 그 방법으로 나온 값**이라 같은 자로 뺄셈이 된다.
→ `in.ev_s4`, `run_ev_s4.sh` (작성 완료, 미실행). 근거는 NOTE.md "S4 분석 2".

## 남은 작업 (우선순위 순)

**분석 쪽은 추가 계산 없이 할 수 있는 것을 다 했다. 남은 건 전부 dhl-desktop 실행이다.**

1. **[계산, dhl-desktop] BKS 확장 스윕** — `run_bks_sweep.sh`, 여전히 **미실행**.
   ```
   cd ~/projects/lammps_tutorial/SiO2-MLIP/02_run/s4_mq7net
   setsid nohup bash run_bks_sweep.sh > sweep_chain.log 2>&1 < /dev/null &
   ```
   ★ **2026-08-24: `in.mqbks_fast` 에 300 K 평형 5 ps + `write_data prod_bks_${tag}.data`
   를 추가했다** (런당 +9초). 원래는 profile 만 뽑아서 스윕 결과로 ring 분석이 불가능했다.
   이제 **2e13_r2 / 2e13_r3 반복이 매칭 냉각률에서 BKS 실현 3개**를 만들어 주고,
   그러면 ring 비교의 '실현간 산포'가 추정치가 아니라 **실측치**가 된다 —
   현재 3.0σ 주장의 가장 약한 고리를 메우는 가장 싼 방법이다.
   끝나면: `python3 04_analysis/src/fig_tg_s4.py` (glob 자동인식) **그리고**
   새 `prod_bks_*.data` 에 `ring_stats.py` 를 돌린 뒤 `fig_rings_s4.py` 재실행.

2. **[계산, dhl-desktop] 0 K E-V 스캔** — `run_ev_s4.sh` (신규, ~45분).
   자체 형성 망의 ρ₀·K₀ → **밀도에서의 위상 형성 효과**.
   ```
   setsid nohup bash run_ev_s4.sh > ev_s4_chain.log 2>&1 < /dev/null &
   ```
   BKS 짝(`in.ev_bks` 를 `prod_bks_2e13.data` 로)도 같이 돌려야 비교가 성립한다.

3. **[분석, dhl-desktop 실행] `traj_analyze.py`** (결합각·배위수·세밀 g(r)) —
   `traj_7net_mq.lammpstrj` vs `traj_bks_2e13.lammpstrj`. 궤적이 커서 원격 실행 후
   `*_stats.dat`, `*_angles.dat`, `*_gr.dat` 만 sync.
   ★ 3-ring 초과의 **직접 상관 증거**가 여기서 나온다: 3원환은 Si–O–Si 를 좁히므로
   7net 의 Si–O–Si 분포에 저각(~130° 이하) 어깨가 있어야 한다. 있으면 ring 결론이
   독립 경로에서 확인되고, 없으면 다시 봐야 한다.

4. **[분석] S(q) 비교** (`sq_direct.py`) — S4 궤적에 미실행.
   RESULTS 4절이 남긴 질문("7net 자체 melt-quench 로 위상을 다시 만들면 FSDP 가
   움직이는가")에 직접 답하는 계산이다. **우선순위를 올릴 만하다.**

5. `_to_delete/s4_chain.log` — 빈 파일, device_bash 가 못 지우니 사용자가 직접 삭제.
6. `./sync.sh` — 이 세션 산출물(ring 그림·스크립트 2개, `in.ev_s4`/`run_ev_s4.sh`,
   `in.mqbks_fast` 수정, NOTE.md 2개 절)을 양쪽에 반영하려면 양쪽에서 한 번씩 실행.

## 확정된 판단 — 되돌리지 말 것 (재논쟁 금지)

- **셀 2160원자·ρ=2.20 NVT 고정**은 기존 결과와의 비교 가능성 때문. 바꾸지 말 것.
- **매칭 냉각률 비교가 필수**다. 다른 속도끼리 Tg를 비교하면 포텐셜 효과와 냉각률 효과가
  섞인다 — 그래서 BKS 2e13 통제런을 따로 돌렸다.
- **kinetic-arrest 임계값 0.10 Å²/100K, K=5 연속**은 T≤1000K ΔMSD p95의 3배 + 임계값×K
  격자 스캔으로 검증된 값이다. "왜 하필 그 위치냐"는 이미 데이터로 답했다 — 다시 묻지 말고
  `fig_tg_s4.py` docstring과 `tg_s4_summary.dat` 생성 이력 참고.
- **"all remaining points below threshold" 방식은 폐기됐다** — 후반부 노이즈 스파이크 하나에
  전체 판정이 흔들리는 문제가 있어 "K개 연속 구간" 방식으로 교체했다.
- **BKS epa와 7net epa는 절대값 비교 불가**(에너지 기준점이 다름 — BKS는 pairwise+Coulomb
  ledger, 7net은 DFT 기준). 그림은 항상 `E(T)−E(300K)`로 그린다. Tg 자체 값에는 영향 없음.
- **7net의 P300 양수(+0.80 GPa, 팽창 경향)는 미평형이 아니다** — 300K 10ps 정상상태로
  확인됐다(핵심 결과 3). 다만 "그래서 이 망이 원하는 밀도가 얼마냐"는 **아직 미측정**이다
  (0K E-V 스캔 대기). ρ₀ 값을 말하기 전까지는 압력 부호까지만 주장할 것.
- **300K NPT tail 런은 하지 않는다.** 7net 100ps NPT = 54시간이고, 애초에 답이 필요한
  자유도는 부피인데 그건 0K E-V 스캔이 45분에 **같은 자로**(RESULTS 2절과 동일 방법)
  답한다. 이 판단을 되돌리려면 NPT가 E-V로 안 되는 무엇을 주는지부터 말할 것.

---

## 아키텍처 — 두 머신 구조 (다시 헷갈리지 말 것)

- **Mac 샌드박스**(`device_bash`가 닿는 곳): `SiO2-MLIP` git 폴더가 마운트돼 있음.
  파일 읽기/쓰기·정리·git 조작은 여기서 가능. **LAMMPS/conda/mpirun 자체는 없다.**
- **dhl-desktop**: 실제 계산이 도는 곳. `mlip` conda 환경, `lmp_7net` 바이너리.
  사용자가 본인 SSH 터미널로 직접 접속해서 실행해야 한다 (device_bash로 대신 실행 불가).
- 둘 사이는 `sync.sh`(git add -A → commit → pull --no-rebase → push)로 연결. 스크립트를
  만들면 Mac에 써두고 → 사용자가 양쪽에서 sync → dhl-desktop에서 사용자가 직접 실행하는
  흐름을 따른다.
- `device_bash`는 삭제를 못 한다 — 지울 파일은 `_to_delete/`로 옮기고 사용자에게 알린다.

---

## 파일 위치 맵

```
02_run/s4_mq7net/
  in.mq7net              7net 본런 스크립트 (완료)
  in.mqbks                BKS 통제런 스크립트 (3종 완료)
  in.mqbks_fast            확장 스윕용 프로파일-only 버전 (RDF/dump 없음)
  run_bks_controls.sh      완료된 3종 통제런 러너
  run_bks_sweep.sh         미실행 — flock 락 걸림, 8개 추가 rate/반복
  in.ev_s4, run_ev_s4.sh   미실행 — 자체 형성 망 0K E-V 스캔 (NPT tail 검증 대체)
  RESUME.txt                (이제 참고용, 본런은 끝났음)
  NOTE.md                    설계 근거 전체
  ckpt/, logs/, profiles/    체크포인트 · 로그 · Tg용 프로파일(T,epa,P,MSD)
  prod_7net_mq.data, prod_bks_{2e13,5e12,5e13}.data   ring stats 입력이 된 최종 구조
  traj_7net_mq.lammpstrj, traj_bks_2e13.lammpstrj      아직 미분석 궤적 (traj_analyze 대상)
  rdf_*.dat                  LAMMPS 자체 RDF (거친 bin, 0.04Å)

04_analysis/
  src/fig_tg_s4.py           Tg 3-panel 비교 그림 (핵심 스크립트)
  src/ring_stats.py          ring statistics 계산 (이번에 재사용)
  src/traj_analyze.py        결합각·배위수·세밀 g(r) — 미실행
  src/sq_direct.py, sq_analyze.py   S(q) — 미실행
  fig/fig_tg_s4.png           Tg 비교 그림
  dat/tg_s4_summary.dat       Tg 수치 요약
  dat/S4_{7net,BKS_2e13,BKS_5e12,BKS_5e13}_rings.dat   ring stats 원시 출력
  src/fig_rings_s4.py         S4 ring 3-panel 비교 그림
  src/ring_robust_s4.py       RCUT 민감도·결함 검증
  fig/fig_rings_s4.png        S4 ring 비교 그림
  dat/S4_rings_summary.dat    7net-BKS 차이·오차·σ
  dat/S4_rings_robust.dat     RCUT 스윕 원시 출력
```
