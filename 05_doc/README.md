# 05_doc — 문서 색인

> **처음 보는 사람은 `RESULTS.md` 부터.** 이어서 볼 게 있으면 `STATUS.md`.
> 나머지는 **결론이 아니라 그때의 판단 기록**이다. 인용하기 전에 아래 상태를 확인할 것.

## 현행 — 이게 결론이다

| 파일 | 내용 |
|---|---|
| **`RESULTS.md`** | **결과 요약.** 밀도·탄성률, 구조(g(r)·결합각·ring), 속도, 검증표, 실패에서 배운 것 |
| **`STATUS.md`** | 인수인계. 환경, **실행 규칙 11개**(전부 "조용히 틀리는" 함정), 비용 모델, 남은 일 |
| **`PPT_BRIEF.md`** | **PPT 제작 인수인계 — 현재 유일한 남은 과제.** 코닝 송부 맥락, 슬라이드 구성, 표기 규칙, 반드시 피할 함정 6개, 출처 조사 목록 |

## 참고 — 여전히 유효

| 파일 | 내용 |
|---|---|
| `S3_MLIP_benchmark_practice.md` | **이 분야가 실제로 뭘 어떻게 비교하는가.** 밀도가 다른 계를 어떻게 비교하는지에 대한 문헌 관행. 비교 설계의 근거 |
| `S0_sevennet_nano_overview.md` | SevenNet-Nano 논문 정리. 모델 계보(7net-Omni `mpa` 채널, PBE(+U), D3 없음)와 논문의 a-SiO₂ 취급 |

## 기록 — ⚠ 결론으로 인용하지 말 것

| 파일 | 상태 |
|---|---|
| `S3_AIMD_reference.md` | **폐기된 후보 검토.** Camellone(arXiv, PW91)을 1순위로 보던 시점의 문서. **최종 AIMD 참조는 Dechant JPCC 2026(PBE)로 교체**됐고, 이 문서가 "가치 낮다"고 판단한 그림 digitize도 결국 수행했다. 후보 탈락 사유(범함수 불일치) 정리로만 유효 |
| `S0c_RDF_comparison_plan.md` | **착수 전 계획서(08-09).** "밀도는 결과가 아니라 경계조건"이라는 당시 프레이밍인데, 실제로는 밀도·K₀를 정면으로 다뤘다(`RESULTS.md` §2). 계획이 어떻게 바뀌었는지의 기록 |

## 원자료

| | |
|---|---|
| `Dechant 등 - 2026 - Origin of Structural Variations...pdf` | **AIMD 참조 원문** (J. Phys. Chem. C **130**, 7148) |
| `jp6c00944_si_001.pdf` | 위 논문의 **Supporting Information**. ring 통계(Fig. S4a)가 여기 있다 |
| `dechant_figs/` | 위 PDF에서 추출한 그림. `04_analysis/src/digitize_dechant_*.py` 의 입력 |

---

## 파일명이 왜 이 모양인가

`S0`/`S0c`/`S3` 접두사는 **착수 당시의 단계 번호**다. 이후 melt-quench 실패로 계획이
한 번 갈아엎어져 실제 진행(S0′, S2′, S3′)과 어긋난다. 파일명을 고치면 문서·NOTE·커밋의
상호참조가 전부 깨지므로 **그대로 두고 이 색인으로 해결**한다. 번호 순서를 신뢰하지 말 것.

## 다른 곳의 기록

- `02_run/*/NOTE.md` — 각 실행의 조건·이유·결과. **실패 이력이 여기 있다**
  (특히 `s2_relax/NOTE.md` 상단에 v1/현행 구분 배너)
- `02_run/_v1_superseded/README.md` — ρ=2.607 계산을 왜 버렸는지
- `00_env/SETUP_FROM_SCRATCH.md` — 새 머신 재현 절차
