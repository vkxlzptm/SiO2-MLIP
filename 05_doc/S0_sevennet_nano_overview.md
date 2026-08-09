# S0-1. SevenNet-Nano 논문 정리 (근거 기반)

> rev.2 메모: 연구 질문이 **밀도 → RDF 3자 비교**로 재정의됨. 아래 4절(논문의 비정질 SiO2 취급)은
> 여전히 유효하며 특히 "논문은 NVT로 밀도를 고정했다"는 점이 새 계획에서 더 중요해졌다.
> 비교 설계는 `S0c_RDF_comparison_plan.md` 참조.

출처
- Oh, You, Kim, Lee, An, Han, Kang, *A Lightweight Universal Machine-Learning Interatomic Potential
  via Knowledge Distillation for Scalable Atomistic Simulations*, arXiv:2604.10887v1 (2026-04-13).
  출판본 DOI: 10.1021/acs.jcim.6c01103 (SevenNet 공식 문서에 링크됨)
- Supporting Information (첨부)
- SevenNet 공식 문서 v0.13.0: https://sevennet.readthedocs.io/en/latest/
- 체크포인트 Zenodo: https://doi.org/10.5281/zenodo.19491140

---

## 1. 모델 개요

| 항목 | 7net-Nano | 7net-Omni (teacher) |
|---|---|---|
| 파라미터 수 | **105 k** | 26 M (약 250배) |
| l_max | 2 | 3 |
| convolution layer | 3 | 5 |
| node feature dim | 32 (모든 l) | 128 / 64 / 32 (l=0 / 1 / >1) |
| parity | full | full |
| cutoff r_c | **4.5 / 5.0 / 5.5 / 6.0 Å (4종 체크포인트)** | — |
| task | single-task | multi-task (13 task) |

- 아키텍처는 SevenNet(= NequIP 계열 E(3)-equivariant GNN). 새 아키텍처가 아니라 **크기를 줄인 것**.
- 학습: AdamW, **2 epoch만** 학습. weight는 random init (단, energy scale/shift는 Omni의 mpa
  채널에서 가져옴; shift는 trainable, scale은 고정).
- Loss = λE·E + λF·F + λS·stress + λ_AE·**atomic energy**
  (λE=1.0, λF=1.0, λS=2e-4, λ_AE=0.5). atomic energy를 supervision으로 쓰는 것이 distillation의 핵심
  — DFT로는 얻을 수 없고 teacher 모델에서만 나오는 신호.

## 2. 학습 데이터 — **여기가 우리 프로젝트의 해석 포인트**

**중요: 7net-Nano는 DFT 데이터로 직접 학습하지 않았다.**
teacher(7net-Omni)의 **inference 결과**로 학습했다 (knowledge distillation).

- config 소스: MPtrj, MatPES, Alex, OMat24 (무기결정) / OMol25, SPICE, QCML (분자) /
  OC20, OC22 (표면) / ODAC23 (MOF) / MAD (multi-domain)
- 이 config들의 E/F/S를 **7net-Omni의 `mpa` 채널로 재계산**하여 라벨 생성
- `mpa` 채널 = **PBE(+U)** 수준 (MPtrj + sAlex 데이터셋 설정). VASP PAW, ENCUT 520 eV,
  MPtrj와 동일한 POTCAR 버전.
- **D3 분산보정 없음** (mpa는 PBE(+U) 단독. ODAC23 task만 PBE-D3인데 Nano는 mpa만 증류받음)

### → 정확도 상한에 대한 결론
1. 7net-Nano의 상한은 **DFT-PBE가 아니라 "7net-Omni의 mpa 채널"** 이다. 이중 근사.
2. functional은 **PBE(+U), 분산보정 없음**.
3. PBE는 실리카(α-quartz 등)의 부피를 과대평가하는 것이 알려져 있으며(주로 분산력 누락),
   그렇다면 **밀도를 과소평가**하는 방향이 예상된다. → 즉 BKS(2.607, 과대)와 **반대 방향**으로
   틀릴 가능성이 있다. *단 이 방향성은 문헌 일반론이며, 우리 비정질 구조에서 실제로 어떻게
   나오는지는 S2에서 측정할 것. 미리 결론짓지 않는다.*
4. 실험값과 어긋나도 그것 자체가 유효한 결과 — "MLIP는 cutoff 트레이드오프에서는 자유롭지만
   학습 functional에 종속된다"는 서사의 데이터가 된다.

## 3. 보고된 성능

### 정확도
- Li-ion 고체전해질 확산: pretrained MLIP의 force-softening 문제를 완화하며 합리적 예측.
- 액체 전해질 밀도: teacher와 일치. 7net-Omni는 실험 밀도 경향과 일치(MPE 9.2% 언급된 계열 있음).
- **sub-Å 단거리 반발**을 잘 기술 → 플라즈마 식각 같은 극한 조건에서 안정.
- 벤치마크 상세 MAE는 SI Figure S1~S3.

### 속도 (본문 Figure 11, NVIDIA RTX PRO 6000 80GB, 비정질 SiO2, NVT 300 K, 1 fs)
| 시스템 크기 | 7net-Omni | 7net-0 | MACE-mp-0-small | **7net-Nano-6.0** |
|---|---|---|---|---|
| 70 atoms | 3.695 ns/day | 6.356 | 4.703 | **9.895** |
| 15,120 atoms | 0.093 (이후 OOM) | 0.525 | — | — |
| 70,000 atoms | OOM | 0.104 | 0.166 | **0.170** |

- Omni 대비 speedup: 1,000 atoms 미만에서는 **~2.68배** (r_c 무관),
  10,000 atoms 초과에서 r_c=6.0/5.5/5.0/4.5에 대해 **9.5 / 11.8 / 15.2 / 20.45배**.
- 70,000 atoms 기준 r_c 5.5·5.0·4.5는 6.0 대비 각각 1.26·1.66·2.43배 빠름.
- 9 nm² 식각 모델에서 7net-Nano-5.5 = **26.8 steps/s** (RTX PRO 6000) vs
  descriptor 기반 SIMPLE-NN 86.8 steps/s (CPU 24코어 × 2노드).

> **우리 계에 대한 함의**: 2160 atoms는 위 표의 70~15,120 사이. 논문에 해당 점의 수치가
> 없으므로 추정하지 않는다. **S1에서 직접 측정**한다 (그 측정 자체가 발표 자료).
> 단, "1000 atoms 미만에서 Omni 대비 2.68배"라는 건 **작은 계에서는 Nano의 이점이 작다**는
> 뜻 — 우리 계는 이점이 중간 정도일 것으로 보인다.

### 권장 체크포인트
논문 결론: **`7net-nano-5.5`가 벤치마크 전반에서 가장 안정적 → 기본 선택.**
더 빠른 계산이 필요하면 4.5 (필요시 fine-tuning).
→ **우리는 `7net-nano-5.5`를 main으로 쓰고, 여유가 되면 4.5/6.0을 cutoff 민감도 비교로 추가.**
(BKS의 cutoff 트레이드오프가 주제이므로, MLIP의 r_c 민감도가 약하다는 걸 보이면 서사가 강해진다.
논문 본문도 "Nano의 정확도는 r_c 의존성이 약하다"고 명시 — 이건 우리가 재현·검증할 수 있는 주장.)

## 4. 논문의 비정질 SiO2 취급 — **중요**

논문에서 비정질 SiO2를 만든 방식:
- cubic cell에 원자를 랜덤 배치 → pre-melting 5000 K 2 ps → melting 4000 K 20 ps →
  quench 4000→300 K, **−100 K/ps** → anneal 500 K 15 ps. 전부 **NVT**.
- **밀도를 2.34 g/cm³로 고정**해서 만들었다 (ref 57, 58 인용).

이 2.34는 인용문헌을 보면 **유리 기판 위 SiO2 박막**(Šimurka et al., Chem. Papers 2018)과
**fused silica 세라믹**(Dehghani & Soleimani) 값이다. 즉 벌크 fused silica의 표준값
**2.20 g/cm³가 아니다.**

### → 두 가지 결론
1. **논문은 SiO2 밀도를 예측한 적이 없다.** NVT로 고정해서 넣었다.
   → 우리의 S2(0 bar 이완으로 밀도가 어디로 가는지)는 **논문 재현이 아니라 새 측정**이다.
   포트폴리오 관점에서 오히려 좋다.
2. 3자 비교의 "실험값"은 **2.20 g/cm³ (벌크 fused silica)** 를 기준으로 하되,
   논문이 쓴 2.34(박막/세라믹)도 병기해서 "실험값도 시료 형태에 따라 범위가 있다"는 점을 밝힌다.

## 5. 배포 상태 (2026-08 확인)

- **7net-Nano는 공식 `sevenn` 패키지(v0.13.0)에 정식 포함됨.** Zenodo 수동 다운로드 불필요.
  모델 키워드: `7net-nano-4.5`, `7net-nano-5.0`, `7net-nano-5.5`, `7net-nano-6.0`
  ```python
  from sevenn.calculator import SevenNetCalculator
  calc = SevenNetCalculator('7net-nano-5.5')
  ```
  → **S0 최대 리스크였던 "체크포인트 구하기"는 해소.** 남은 리스크는 LAMMPS 연동뿐.
- Zenodo(10.5281/zenodo.19491140)에는 checkpoints.tar(5.2 MB), module.tar(fine-tuning용 수정
  SevenNet), example.tar, dft.tar. **fine-tuning을 할 게 아니면 받을 필요 없다.**

## 6. 면접에서 쓸 한 줄 요약

> 7net-Nano는 26M 파라미터 foundation model(7net-Omni)을 105k 파라미터로 knowledge
> distillation한 경량 universal MLIP다. 핵심은 teacher의 atomic energy까지 supervision으로
> 쓴 것이고, 대가는 정확도 상한이 DFT가 아니라 teacher의 PBE 채널에 묶인다는 점이다.
