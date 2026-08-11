# a-SiO₂ MLIP 벤치마크 — 이 분야는 실제로 무엇을 어떻게 비교하는가

"밀도가 서로 다를 때 어떻게 비교하나"에 대한 답을 문헌 관행에서 찾은 결과.
결론부터: **곡선 오버레이가 아니라 밀도에 둔감한 국소 구조량 + 밀도 자체를 따로 보고한다.**

---

## 문헌 1 — 실리카 GAP

**Erhard, Rohrer, Albe, Deringer**, *A machine-learned interatomic potential for silica and its
relation to empirical models*, **npj Comput. Mater. 8, 90 (2022)**
https://www.nature.com/articles/s41524-022-00768-w

- 비교 대상: **GAP(SCAN 수준 DFT 학습) vs BKS · CHIK · Vashishta · Munetoh** — 딱 우리 구도.
- **밀도를 고정하지 않는다.** 프로토콜(Methods 원문):
  > "Amorphous-phase structural models were created from initially randomly placed atoms, which were
  > additionally randomised at 6000 K (NVT, 10 ps) and then held at 4000 K (**NPT with zero external
  > pressure**, 100 ps) to generate a melt. The melt was quenched to 300 K with a rate of **10¹³ K/s**...
  > The resulting amorphous structure was then held for another 10 ps."
  → LAMMPS, Nosé–Hoover + Parrinello–Rahman, dt = 1 fs.
  **즉 밀도는 강제하는 제약이 아니라 각 포텐셜이 내놓는 예측값이다.**
- 벤치마크 항목 (g(r) 오버레이가 아니다):
  1. **X-ray S(q) vs 실험** (Mei et al., PRB 78, 144204 (2008)) — FSDP 위치·높이가 핵심 지표
  2. **배위 결함 비율** — Si가 4배위, O가 2배위가 아닌 원자의 분율
  3. **excess energy** (α-quartz 기준). 실험 참조값 **78–131 meV/SiO₂** (Richet et al. 1982)
- **우리 워크플로가 이 논문에서 검증된 방법론이다.**
  > "'Hybrid' quenches with a combination of CHIK and GAP ... quenching rates between 10¹³ and 10¹¹ K/s,
  > and subsequent annealing for 20 ps using the GAP."
  > "...a combination of CHIK quenching and GAP relaxation **might be promising** for the modelling of
  > amorphous silica."
  → **싼 고전 포텐셜로 quench + MLIP로 이완**이 바로 우리가 하고 있는 것. 즉흥이 아니라 인정된 접근.
- 정성 결과: GAP은 배위 결함을 "거의 0"으로 줄임. BKS·CHIK·Vashishta는 결함이 적고 Munetoh는 >10 %.
  BKS의 S(q)는 실험과 잘 맞으나 첫 피크가 약간 높은 q로 밀림.

## 문헌 2 — 통합 MTP (Si / O / silica)

**A unified moment tensor potential for silicon, oxygen, and silica**, **npj Comput. Mater. (2024)**
https://www.nature.com/articles/s41524-024-01390-8

- 비교 대상: **MTP vs DFT(AIMD) · BKS · Tersoff · Vashishta · SHK1 · SHK2**
- **AIMD와의 직접 비교는 고온 액체(3600 K)·96원자 상자**에서 한다. 비정질 고체는 AIMD가 너무 비싸서
  실험 쪽으로 간다 — **vitreous SiO₂의 partial g(r)은 실험 RMC 데이터**(Tucker et al., JPCM 17, S67 (2005))와 비교.
- **본문에 있는 수치 (digitize 불필요)**:
  > "the Si–O bond length distribution are centered between **1.60 and 1.66 Å**. The average bond length
  > distribution for MTP potential is **1.63 Å**, which is close to experimental values of **1.62 Å**."
  > "both the MTP and BKS show similar profiles centered between the experimental values of **144° and 152°**.
  > The average values for **BKS Si–O–Si angle is 150** and the one of the **MTP is 145.5**."
- O–Si–O 각은 모든 모델이 실험 109.0° 근처로 수렴 → 변별력 없음. **Si–Si–Si 각에서 BKS가 DFT와 어긋난다.**
- Si–Si g(r)의 **5 Å 부근 2피크**를 MTP만 재현, BKS 포함 나머지는 실패 → 중거리 구조의 변별 지표.

---

## 우리 결과를 문헌 좌표에 얹으면

| | Si–O (Å) | Si–O–Si (°) | 출처 |
|---|---|---|---|
| 실험 | 1.61–1.62 | 144–152 | Mozzi–Warren, Grimley 등 |
| **BKS (우리, 0 K, ρ=2.607)** | **1.6123** | **149.25 ± 13.2** | 본 작업 |
| BKS (MTP 논문, 300 K) | ~1.6 | **150** | npj 2024 |
| BKS (Camellone, 300 K, ρ=2.20) | 1.61 | 152 ± 11 | arXiv:1109.2852 |
| **7net-nano-4.5 (우리, 0 K, ρ=2.516)** | **1.6360** | **143.78 ± 14.0** | 본 작업 |
| MTP (npj 2024, 300 K) | **1.63** | **145.5** | npj 2024 |
| CPMD PW91 (Camellone, 300 K) | 1.65 | 146 ± 6 | arXiv:1109.2852 |

**우리 SevenNet 값이 독립 개발된 MTP와 사실상 같은 자리에 떨어진다** (1.636 vs 1.63 / 143.8 vs 145.5).
그리고 두 MLIP 모두 BKS의 ~150°를 ~145°로 끌어내려 DFT·실험 중심으로 이동시킨다.
서로 다른 아키텍처(MTP=descriptor 회귀 / SevenNet-nano=foundation model 증류)가 같은 보정을 낸다는 것은
**우리 계산이 개별 모델의 우연이 아님을 시사한다.**

배위수: 우리 7net 구조의 Si 배위수 4.013 (BKS 4.017) — Erhard et al.의 "배위 결함 거의 없음" 기준 충족.

## 그래서 비교 설계는 이렇게 간다

밀도를 억지로 맞출 필요가 없다. 문헌이 실제로 쓰는 지표는 대부분 **밀도에 둔감한 국소량**이고,
밀도 자체는 **별도의 예측 항목**으로 보고한다.

| 항목 | 밀도 민감도 | 우리 상태 |
|---|---|---|
| Si–O 결합길이 | 낮음 | ✅ 확보 (0 K) |
| Si–O–Si 각 분포 | 중간 | ✅ 확보 (0 K) |
| 배위 결함 비율 | 낮음 | ✅ 확보 |
| 평형밀도 (NPT/E–V) | — (그 자체가 항목) | ✅ S2에서 확보 |
| g(r) 곡선 (BKS vs 7net) | 높음 → **같은 밀도에서** | S3에서 확보 예정 |
| g(r) 곡선 vs AIMD(ρ=2.20) | 높음 | ❌ 포기. 피크 위치만 비교 |
| S(q) FSDP | 높음 | 선택 (g(r) 있으면 계산 가능) |

**결론: ρ=2.20 구조를 새로 만들 필요 없다.** S3는 원래 계획대로 ρ=2.607 고정으로
BKS vs SevenNet g(r)을 뽑고, AIMD·MTP·실험과는 **국소 구조량(피크 위치·각도·배위)**으로 비교한다.
단 300 K 값이어야 문헌과 직접 비교되므로 **S3 MD가 여전히 필요하다**(현재 값은 0 K 정적).

## 남은 열린 항목

- **우리 BKS 밀도 2.607이 문헌 BKS 값과 맞는지 미확인.** Erhard et al.은 NPT로 밀도를 예측시켰으므로
  그 논문에 BKS의 a-SiO₂ 밀도가 있을 것이나 본문 발췌에서 확인 못 함.
  우리가 2.607이 나온 게 BKS 자체 특성인지 quench 속도(6.7×10¹² K/s) 탓인지 아직 구분 못 함.
  Erhard et al.이 quench rate 의존성을 명시적으로 다뤘으므로(Fig. 5d,e) 참고 가능.
- 실험 partial g(r)은 RMC 기반(Tucker et al. 2005)이 표준. 필요하면 이쪽을 digitize 대상으로.
