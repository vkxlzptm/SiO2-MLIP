# S4 — 7net 자체 melt-quench (덱 6p 'Next step' 실행)

## 무엇을 바꾸는가

기존 결과: BKS가 melt-quench로 망 위상을 만들고, 7net은 그 위에서 relax + NVT MD만 했다.
→ ring 분포가 BKS와 **동일 구조**라 7net의 위상 예측력을 전혀 시험하지 못했다.

S4: **quench를 7net이 수행**한다. Tg를 지나며 위상이 얼어붙는 구간을 7net이 결정하므로,
처음으로 "7net이 만든 망 위상"을 얻는다.

## 고정한 것 / 바꾼 것

| 항목 | 값 | 근거 |
|---|---|---|
| 셀 | 2,160원자, V = 32,652.95 Å³ | 바꾸면 ring 잘림 길이·S(q)의 q_min·g(r) r_max가 달라져 기존 결과와 비교 불가 |
| 밀도 | ρ = 2.20 g/cm³ 고정 | BKS·7net·AIMD·실험이 모두 여기 놓여 있음 |
| 앙상블 | **전 과정 NVT** | Dechant (2026): 용융 중 NPT는 unphysical bond → 비정상 셀 변형. NPT는 300 K에서만 |
| 용융 | BKS 4,000 K 액체 인계 → 7net 재평형 20 ps | classical 액체 + MLIP 재평형은 MLIP 문헌 표준. 성립 조건은 MSD 게이트 하나 |
| 급랭률 | **2×10¹³ K/s** (100 K × 5 ps) | 문헌 범위(10¹¹~10¹³) 상한의 2배. BKS 동일률 통제런으로 상쇄 |
| 300 K 산출 | 평형 5 ps + 생산 5 ps (RDF·궤적) | 7net 본런과 BKS 통제런 모두 동일 길이 |

## 비용 (i5-11600K 6c12t, OMP=6, 실측 1,100 atom-step/s = 1.96 s/step)

| 런 | 길이 | 시간 |
|---|---|---|
| 7net MELT EQUIL 4,000 K | 20 ps | 10.9 h |
| 7net QUENCH 4,000→300 K | 185 ps | 100.7 h |
| 7net EQUIL+PROD 300 K | 10 ps | 5.4 h |
| **7net 합계** | 215 ps | **117 h (4.9일)** |
| BKS 통제런 3종 | — | ~33 min |

스레드는 6이 최적 — 12스레드 무이득, 독립 프로세스도 6개에서 2.0× 포화(메모리 대역폭 한계).
**7net 본런과 BKS 통제런을 동시에 돌리지 말 것.**

## 실행 순서

```bash
cd 02_run/s4_mq7net

# 1) BKS 통제런 먼저 (33분)
bash run_bks_controls.sh

# 2) 7net 본런
ulimit -s 262144
export OMP_NUM_THREADS=6 MKL_NUM_THREADS=6
nohup lmp_7net -in in.mq7net > mq7net.log 2>&1 &
```

`mpirun` 금지 — CPU 빌드에 `e3gnn/parallel`이 없다.

## ★ MSD 게이트 — 시작 후 3시간 지점에 반드시 볼 것

이 계산 전체의 성패가 여기서 갈린다. BKS 액체 구조의 기억이 지워졌는지의 판정이다.

```bash
awk '/^ *Step +Temp/{on=1;next} /^Loop time/{on=0} on&&NF==9{print $1,$2,$7,$8,$9}' \
    mq7net.log | tail -20
#   출력: step  temp  epa  MSD  maxf
#   thermo 9열: step temp press vol density pe v_epa c_msd0[4] c_maxf

# 마지막 한 줄만
awk '/^ *Step +Temp/{on=1;next} /^Loop time/{on=0} on&&NF==9{s=$1;m=$8;f=$9} \
     END{print "step",s," MSD",m,"A^2  maxf",f}' mq7net.log

# 진행 속도 (thermo 100 간격 -> 새 줄 1개 = 100 step)
a=$(grep -cE '^ *[0-9]+ +[0-9]' mq7net.log); sleep 60
b=$(grep -cE '^ *[0-9]+ +[0-9]' mq7net.log)
echo "s/step = $(echo "60/(($b-$a)*100)" | bc -l)"
```

| 판정 | 기준 (step 5000 ≈ 5 ps, 약 3 h 지점) | 조치 |
|---|---|---|
| 통과 | MSD가 시간에 **선형** + 5 ps에 10 Å² 이상 (20 ps에 수십 Å²) | 그대로 방치 |
| 실패 | MSD가 평평하거나 5 ps에 < 5 Å² | 죽이고 `velocity create 4500.0` + `fix nvt 4500`으로 재시작 (손실 3 h) |
| 붕괴 | `c_maxf`가 수십 eV/Å로 튐, epa 발산 | 외삽 실패. 온도를 **낮춰** 3,500 K로 재시도 |

융점은 추정하지 않는다 — 위 로그로 **측정**한다. MLIP 유효 융점이 BKS보다 높은지 낮은지
사전 지식이 없으므로 4,000 K에서 시작해 실패 방향에 따라 올리거나 내린다.

이후엔 하루 1회:

```bash
tail -3 mq7net.log; tail -3 mq7net_profile.dat; cat RESUME.txt
```

## 재개

100 K 구간이 끝날 때마다 `ckpt_T<T>.data`와 `RESUME.txt`가 갱신된다.
죽으면 `RESUME.txt` 내용을 그대로 실행하면 된다.

```bash
cat RESUME.txt
# lmp_7net -in in.mq7net -var domelt 0 -var dfile ckpt_T2600.data -var Tstart 2500
```

`-var domelt 0`이 MELT 단계를 건너뛰고, 체크포인트의 속도를 그대로 이어받는다.
`mq7net_profile.dat`는 append이므로 중복 라인이 생기면 재개 지점 기준으로 손으로 정리할 것.

## 산출물

| 파일 | 내용 |
|---|---|
| `mq7net_profile.dat` | T · epa · P · MSD — 엔탈피 곡선에서 **7net의 Tg**를 읽는다 |
| `rdf_7net_mq.dat` | 300 K RDF (200 bin, 8 Å) — 기존 `rdf_7net220_3ps.dat`와 동일 포맷 |
| `traj_7net_mq.lammpstrj` | 250 프레임 — ring 분포·S(q)·결합각 분석 입력 |
| `prod_7net_mq.data` | 최종 구조 |
| `mqbks_{5e12,2e13,5e13}_*` | BKS 통제 3종. 같은 이름 규칙 |

## 분석에서 주장할 수 있는 것 / 없는 것

**주장 가능**
- 7net vs BKS @ 2×10¹³ K/s — 초기구조·셀·급랭률·통계 길이가 전부 같다.
  ring 분포 차이가 나오면 **포텐셜에서 온 것**이다. 이 프로젝트에서 처음으로 성립하는 주장.
- BKS 5e12/2e13/5e13 세 점 → **급랭률 민감도**를 %로 제시.
  "7net은 한 속도에서만 돌렸지만, 이 구간의 급랭률 효과는 X %"까지 말할 수 있다.
- `mq7net_profile.dat`의 epa(T) 꺾임 → 7net의 Tg. BKS Tg와 비교.

**주장 불가**
- 기존 7net 220 결과(BKS 위상 위 relax)와 S4 결과의 차이를 "급랭률 때문"이라고 하는 것.
  두 계산은 급랭률 말고도 위상 생성 주체가 다르다.
- AIMD의 한계가 셀 크기라는 것 — 본 계산으로 검증되지 않는다 (기존 문서 규칙 유지).
- 급랭률 2×10¹³이 문헌 범위 안이라는 것 — **상한의 2배다.** 발표에서 명시할 것.

## 알려진 타협

1. 급랭률이 기존 BKS 220 런(5×10¹²)의 4배. CPU 117 h가 한계선이라 불가피.
   → 통제런으로 상쇄하되, 절대값은 발표에서 그대로 밝힌다.
2. 7net은 **시드 1개**만 돌린다 (117 h × N은 불가).
   → ring 분포의 통계 오차는 BKS 다중 시드로 추정해 함께 제시할 것.
3. 300 K 생산 5 ps는 기존 7net 런(3 ps)보다 길지만 BKS 220 런(50 ps)보다 짧다.
   RDF 제1피크 위치에는 충분하나, 비교 표에 길이를 병기할 것.
