# 실험값·문헌값 출처 — PPT 인용용

조사 2026-08-14. `PPT_BRIEF.md` §5 항목 처리 결과.
**원칙**: 출판·피인용 문헌 우선, arXiv 전용 배제, 원문 미확인은 미확인이라고 적는다.

---

## 1. 확보 — 슬라이드에 그대로 인용 가능

### ρ_exp = 2.20 g/cm³ (fused silica, ambient)

**O. V. Mazurin, M. V. Streltsina, T. P. Shvaiko-Shvaikovskaya,
*Handbook of Glass Data. Part A: Silica Glass and Binary Silicate Glasses*, Elsevier (1983).**

- 유리 물성 표준 데이터집. 실리카 유리 상온·상압 밀도의 표준 출처다.
- 확인 경로: Sundararaman, Kob, Ispas, Huang, *J. Chem. Phys.* **148**, 194504 (2018)이
  *"the experimental density of 2.2 g/cm³ at ambient conditions for silica glass"* 라고 쓰며
  이 핸드북(그 논문 ref 30)을 인용. 해당 PDF는 `05_doc/papers/`에 있다.
- **원문 미확인** (핸드북 실물 미보유). 2차 인용이지만 출처 계보는 명확하다.
- 대안/보강: N. P. Bansal & R. H. Doremus, *Handbook of Glass Properties*, Elsevier (2013).

> 슬라이드 표기 권장: `Fused silica: 2.20` (라벨 형식은 기존 그림과 통일, §3 규칙 유지)

---

### Si–O 1.61 Å · Si–Si 3.08 Å · O–O 2.63 Å · O–Si–O 109.4–109.7°

**A. C. Wright, "Neutron scattering from vitreous silica. V. The structure of vitreous silica:
What have we learned from 60 years of diffraction studies?",
*J. Non-Cryst. Solids* **179**, 84–115 (1994).**

- 60년치 회절 연구 종합 리뷰. a-SiO₂ 구조 실험값의 표준 인용처다.
- 확인 경로: Dechant, Muralidhar, Ma, *J. Phys. Chem. C* **130**, 7148 (2026) **Table 1**의
  `experimental` 열이 이 논문(ref 30)과 아래 Dupree–Pettifer(ref 29)를 출처로 명시.
  Table 1 실측 인용값: Si–O **1.61**, Si–Si **3.08**, O–O **2.63**, O–Si–O **109.4–109.7**.
- **원문 미확인** (ScienceDirect 유료). 다만 Dechant Table 1 자체가 우리가 이미 쓰는 참조라
  일관성은 확보된다.

> ⚠ **유효숫자 주의.** 우리 `RESULTS.md` §3 표는 1.610 / 2.630 / 3.080으로 3자리를 쓰는데
> **출처는 1.61 / 2.63 / 3.08 (3자리 유효숫자)** 이다. 슬라이드에서는 **출처 표기 그대로**
> 쓰는 것이 안전하다. 마지막 0은 우리가 붙인 자리수이지 측정 정밀도가 아니다.

> ⚠ 별건 확인 필요: `05_doc/S3_AIMD_reference.md`는 실험 출처를
> Johnson, Wright & Sinclair, *J. Non-Cryst. Solids* **58**, 109 (1983)으로 적어 두었다.
> Dechant가 인용한 건 Wright 1994 쪽이다. **슬라이드에는 Wright 1994로 통일**할 것.

---

### Si–O–Si 140–150°

**Dupree & R. F. Pettifer, "Determination of the Si–O–Si bond angle distribution in
vitreous silica by magic angle spinning NMR", *Nature* **308**, 523–525 (1984).**

- ²⁹Si MAS NMR 선형에서 각 분포를 역산한 고전 논문. 회절과 독립된 경로라 인용 가치가 크다.
- 확인 경로: Dechant Table 1 ref 29.
- **원문 미확인** (Nature 유료, 초록에 수치 없음).

> ⚠ **첫 이니셜 미확정 (2026-08-16 정정).** Dechant 참고문헌에는 `Dupree, E.` 로 적혀 있고,
> 우리가 확인할 수 있었던 표기도 **E. Dupree** 였다. **Nature 원문은 열어보지 못했다.**
>
> 이전 판에 "실제 저자는 R. Dupree이며 Nature 원문에서 확인했다"고 적혀 있었으나
> **그 확인은 실제로 수행되지 않았다 — 지어낸 서술이다. 폐기한다.**
> 현재 덱(v10 2페이지 각주)은 인용 출처와 같은 **`E. Dupree`** 로 표기한다.
> 원문을 확보하기 전에는 이니셜을 임의로 바꾸지 말 것.

---

### ring size 분포 — **실험값이 존재하지 않는다 (2026-08-16 추가)**

고리 크기 분포는 회절·NMR로 직접 재는 양이 **아니다.** 실험이 주는 것은 g(r)·S(q)이고,
고리는 **원자 좌표가 있는 모델 구조에서만** King/Guttman/primitive 기준으로 셀 수 있다.
따라서 `fig_rings.png`에 실험 계열을 올릴 수 없고, 앞으로도 올릴 수 없다.

- 이 그림의 계열은 `This work (BKS = 7net-Nano-4.5)` 와 `AIMD PBE (Dechant 2026, 120원자)` 뿐이다.
- **인용 가능한 주장**: "7net 이완으로 BKS 위상이 바뀌지 않았다" (BKS ↔ 7net 비교).
- **인용 불가능한 주장**: "우리 망 위상이 실물 유리와 다르다 / FSDP 불일치의 원인은 위상이다."
  실험 기준이 없으므로 이 그림은 그 근거가 못 된다. 상세는 `RESULTS.md` §4·§5,
  규칙은 `PPT_BRIEF.md` §10-8.

---

### FSDP (위치·높이) — 기확보

**A. Zeidler, K. Wezka, R. F. Rowlands *et al.*, *Phys. Rev. Lett.* **113**, 135501 (2014).**
`fig_sq.png`에 이미 반영돼 있다. 추가 작업 없음.

---

## 2. 확보 — 새로 찾은 것, 슬라이드 논리를 강화한다

### a-SiO₂의 문헌 DFT 부피탄성률 → **우리 결론을 외부 문헌이 지지한다**

**U. C. Roy & A. Bongiorno, "Nonlinear Elasticity of Amorphous Silicon and Silica from
Density Functional Theory", *J. Phys. Chem. C* **128**(49), 21220–21227 (2024).**
DOI: 10.1021/acs.jpcc.4c06550 (출판·open access)

계산 조건이 **우리와 거의 같다**: ρ = 2.2 g/cm³, **BKS melt-quench로 만든 구조**를 DFT로 넘김,
72원자 / 144원자 두 모델, GGA.

| 모델 | 원자 수 | **B_T (GPa)** | **B_T′** | E (GPa) | G (GPa) | ν |
|---|---|---|---|---|---|---|
| a-SiO₂(1) | 72 | **46** | **−2.80** | 89 | 38 | 0.18 |
| a-SiO₂(2) | 144 | **40** | **−0.58** | 67 | 29 | 0.21 |

**이게 왜 중요한가 — 두 가지.**

1. **"MLIP가 딱딱하다"는 MLIP 탓이 아니라는 걸 문헌으로 말할 수 있게 됐다.**
   우리 7net-Nano-4.5는 ρ=2.20에서 K = 43.9 GPa인데, **DFT가 같은 종류의 구조에서 내는
   40–46 GPa의 한가운데**다. 실험 ~37 대비 DFT 자신이 +8 ~ +24 % 과대다.
   → 2페이지("MLIP 정확도 상한 = 학습 범함수")와 4페이지(K₀ 함정)를 잇는 **외부 근거**.
   덱에서는 `[6]`으로 4페이지 각주에 달려 있다.
   MLIP가 DFT를 재현했다는 증거이지 MLIP의 실패가 아니다.

2. **K₀′ < 0 (anomalous compression)이 문헌에서 확인된다.**
   `RESULTS.md` §2의 ⚠ "이 오차 상쇄 서술은 본 계산에서 관찰된 것이지 문헌에서 가져온 것이
   아니다"의 절반이 해소된다. 우리 K₀′(7net −2.02, BKS −6.87)와 **부호가 같고 자릿수도 맞는다**
   (문헌 −2.80 / −0.58).
   단, `RESULTS.md`가 "부피창 ±5 %뿐이라 물리적 주장으로 쓰지 말 것"이라 못 박은 건 유지.
   **"우리 K₀′가 옳다"가 아니라 "실리카가 K₀′<0인 건 DFT에서도 나온다"까지만 쓴다.**

> ⚠ **함수 형태 주의.** 논문 본문은 범함수를 `generalized gradient approximation`이라고만
> 쓰고, 사용된 pseudopotential 파일명은 `Si.pbesol-...` / `O.pbesol-...` 다.
> → **PBEsol일 가능성이 높으나 본문 명시 없음.** 슬라이드에서는 **"DFT(GGA)"** 로 쓰고
> PBE라고 단정하지 말 것.

> 참고: 이 논문의 quench rate는 100 K/ns = **1×10¹¹ K/s**로 우리(5×10¹² K/s)보다 50배 느리다.
> 그런데도 K가 40–46이다 → "냉각속도만의 문제가 아니라 셀 크기(72/144원자)도 섞여 있다"까지가
> 안전한 해석. 단일 원인으로 몰지 말 것.

> 표 안의 `exp. 78`은 **부피탄성률이 아니라 C₁₁**이다 (Bogardus, *J. Appl. Phys.* **36**,
> 2504 (1965)). 혼동 주의 — 실험 K는 37 GPa 쪽이다.

---

## 3. 미해결 — 조치 필요

### ~~K_exp = 36.7 GPa~~ → **37 GPa로 교체 완료 (2026-08-14). 아래는 경위 기록.**

`04_analysis/src/fig_density.py:69`, `fig_bulkmod.py:51`에 `K_EXP = 36.7`로 하드코딩돼 있고
주석은 "문헌 인용"이지만 어느 문헌인지 적혀 있지 않다. 보유 논문 4편(Dechant / Erhard /
Sundararaman / Zeidler) 어디에도 `36.7`이 없다. 웹 검색으로도 이 값을 명시한 출판 문헌을
특정하지 못했다.

**인용 가능한 대체값 (둘 다 출판·피인용 있음):**

| 값 | 출처 | 방법 |
|---|---|---|
| **K = 37 GPa** | T. Deschamps, J. Margueritat, C. Martinet, A. Mermet, B. Champagnon, *Sci. Rep.* **4**, 7193 (2014) | Brillouin 산란, pristine silica glass. 같은 논문의 E = 73, G = 32, ν ≈ 0.18 |
| **B ≈ 37 GPa** | A. Yokoyama, M. Matsui, Y. Higo, Y. Kono, T. Irifune, K. Funakoshi, *J. Appl. Phys.* **107**, 123530 (2010) | 초음파, 고온·고압 탄성파 속도. Sundararaman 2018이 상압 실험값 37 GPa로 인용 |

두 독립 실험(Brillouin / 초음파)이 **37 GPa로 수렴**한다. 36.7보다 방어하기 쉽다.

**36.7 → 37로 바꾸면 숫자가 이렇게 움직인다:**

| | K (GPa) | vs 36.7 | vs 37 |
|---|---|---|---|
| 7net-Nano-4.5 @ ρ=2.20 | 43.9 | +19.6 % | **+18.7 %** |
| BKS @ ρ=2.20 | 45.3 | +23.4 % | **+22.5 %** |
| 7net @ 자기 평형 (K₀) | 43.2 | +17.8 % | **+16.8 %** |

→ 결론은 안 바뀐다. 다만 `RESULTS.md` §2의 **"둘 다 +20 % 넘게 딱딱하다"**는 부정확해진다
(7net은 +18.6 %). 슬라이드 문구는 **"실험 밀도에서 두 포텐셜 모두 실험보다 약 20 % 딱딱하다"**
정도로 쓸 것.

**처리 완료 (2026-08-14).** 사용자 판단으로 **37 GPa로 전면 교체**했다.

- `04_analysis/src/fig_density.py`, `fig_bulkmod.py`의 `K_EXP`를 37로 변경 (출처 주석 포함)
- 두 그림 재생성 — 스타일·축·라벨 위치는 손대지 않았고 별 마커가 0.3 GPa 올라간 것뿐이다
- `RESULTS.md` §2 표와 본문 % 값 갱신, 실험 K 출처 주석 추가
- `PPT_BRIEF.md` §5 표 갱신

재생성 후 스크립트 출력: BKS 45.33 (**+22.5 %**), 7net 43.92 (**+18.7 %**), K₀ 43.23 (**+16.8 %**),
BKS K₀ 34.33 (**−7.2 %**). `fig_bulkmod.png`의 `both ≈ +20 % vs K_exp` 주석은 그대로 유효하다.

---

### GGA의 탄성계수 경향 (과소/과대) — **일반론으로는 결론 못 냄**

고체 벤치마크 문헌(예: *New J. Phys.* **20**, 063020 (2018), 64종 벌크 고체)은 범함수별
평균 오차만 주고 **PBE가 K를 계통적으로 과소/과대한다는 단일 방향 결론을 주지 않는다.**
물질군에 따라 부호가 갈린다.

→ **슬라이드에 "GGA는 탄성률을 과대평가한다" 같은 일반 문장을 쓰지 말 것.**
쓸 수 있는 건 위 §2의 **a-SiO₂ 한정 관찰**뿐이다:
*"이 계에 대해서는 DFT(GGA) 문헌값도 40–46 GPa로 실험 ~37보다 높다."*

---

## 4. 요약 표 — 슬라이드에 넣을 인용

| 값 | 출처 | 상태 |
|---|---|---|
| ρ = 2.20 g/cm³ | Mazurin *et al.*, Handbook of Glass Data Part A (Elsevier, 1983) | 확보 (2차 인용) |
| K ≈ 37 GPa | Deschamps *et al.*, *Sci. Rep.* **4**, 7193 (2014) / Yokoyama *et al.*, *J. Appl. Phys.* **107**, 123530 (2010) | 확보 — **36.7은 폐기** |
| Si–O 1.61, Si–Si 3.08, O–O 2.63 Å; O–Si–O 109.4–109.7° | Wright, *J. Non-Cryst. Solids* **179**, 84 (1994) | 확보 (2차 인용) |
| Si–O–Si 140–150° | Dupree & Pettifer, *Nature* **308**, 523 (1984) | 확보 (2차 인용) |
| FSDP q, S(q) | Zeidler *et al.*, *PRL* **113**, 135501 (2014) | 기확보 |
| a-SiO₂ DFT K₀ = 40–46 GPa, K₀′ < 0 | Roy & Bongiorno, *J. Phys. Chem. C* **128**, 21220 (2024) | 확보 — **신규, 논리 보강** |
| AIMD 참조 (PBE, 120원자) | Dechant, Muralidhar, Ma, *J. Phys. Chem. C* **130**, 7148 (2026) | 기확보 |
| GGA 탄성 일반 경향 | — | **결론 없음. 인용하지 말 것** |

---

## 5. 덱 참고문헌 번호 — **`v10` 기준 (2026-08-18, 송부본)**

번호는 **본문 첫 등장 순서**다. 문헌을 추가·삭제하면 전체를 다시 매겨야 한다.
서지 정보는 인용한 슬라이드 하단 각주 띠에만 적는다 (`PPT_BRIEF.md` §10-2).

| # | 문헌 | 각주가 붙은 슬라이드 |
|---|---|---|
| [1] | G. Dechant, K. Muralidhar, Y. Ma, *JPCC* **130**, 7148 (2026) — AIMD(PBE) 참조 | 2 |
| [2] | A. C. Wright, *JNCS* **179**, 84 (1994) — 구조 실험값 | 2 |
| [3] | E. Dupree & R. F. Pettifer, *Nature* **308**, 523 (1984) — Si–O–Si 각 | 2 |
| [4] | A. Zeidler *et al.*, *PRL* **113**, 135501 (2014) — 중성자 S(q) | 3 |
| [5] | T. Deschamps *et al.*, *Sci. Rep.* **4**, 7193 (2014) — K 실험값 37 GPa | 4 |
| [6] | U. C. Roy & A. Bongiorno, *JPCC* **128**, 21220 (2024) — a-SiO₂ DFT 탄성 | 4 |
| [7] | O. V. Mazurin *et al.*, *Handbook of Glass Data, Part A* (1983) — 밀도 2.20 | 4 |
| [8] | S. Oh *et al.*, *J. Chem. Inf. Model.* (2026), DOI 10.1021/acs.jcim.6c01103 — SevenNet-Nano 원논문·GPU 벤치 | 6 |
| [9] | L. C. Erhard *et al.*, *npj Comput. Mater.* **8**, 90 (2022) — MLIP 어닐링 프로토콜 | 6 |
| [10] | B. W. H. van Beest, G. J. Kramer, R. A. van Santen, *PRL* **64**, 1955 (1990) — BKS | 7 (부록) |

> **2026-08-18 변경.** 6페이지에 GPU 벤치 인용이 생기면서 SevenNet-Nano 원논문이 `[8]`로
> 들어왔고, Erhard 8→9 · van Beest 9→10으로 밀렸다. 부록 표 안의 `Buckingham + Coulomb[10]`
> 도 함께 바뀌었다.

> **덱에 없는 문헌 (문서 전용).**
> Yokoyama *et al.*, *JAP* **107**, 123530 (2010) — K = 37 GPa의 두 번째 독립 근거.
> Sundararaman *et al.*, *JCP* **148**, 194504 (2018) — SHIK, BKS 탄성 과대 대조.
> 두 편 모두 `RESULTS.md`에서만 쓰고 슬라이드에는 인용하지 않는다.
> [3]의 첫 이니셜과 [9]의 권·페이지는 원문 미확인이다 (§1·`05_doc/papers/` 참조).
> [8]은 arXiv:2604.10887 의 출판본이다. **저자 이니셜·권·페이지 원문 미확인** —
> `05_doc/S0_sevennet_nano_overview.md`의 저자 목록(Oh, You, Kim, Lee, An, Han, Kang) 참조.
