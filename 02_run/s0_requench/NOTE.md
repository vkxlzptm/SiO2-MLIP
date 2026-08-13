
---

## S0-b · 300 K NPT 재실행 (tail 보정 on) — 2026-08-13

`in.npt_tail` — `sio2_bks220.data`(300 K NVT 산물)에서 NPT 단계만 다시.
20 ps 재평형 + 100 ps 생산, 3분 53초 (6랭크).

| | tail OFF (원 런) | **tail ON (현행)** |
|---|---|---|
| 300 K NPT ρ | 2.3119 | **2.3401** (100 ps 평균) |
| 0 K virial ρ₀ | 2.3151 | **2.3442** |
| 둘의 차이 | 0.14 % | 0.17 % |

**왜 다시 돌렸나.** EOS 보고 관례를 tail OFF → ON 으로 바꿨는데(경위는
`../s2_relax/NOTE.md` 와 `05_doc/RESULTS.md` §2), **NPT 는 압력으로 barostat 을
구동하므로 tail 유무에 실제로 반응한다.** E–V 스캔과 달리 결과가 바뀐다.
(반대로 E–V 최소화는 tail 이 힘에 기여하지 않아 구조가 비트 단위로 동일했다.)

**판정.** 두 관례 모두 0 K virial 과 0.15 % 수준으로 맞는다 → 관례가 바뀌어도
내부 정합은 유지된다. 열팽창은 여전히 무시할 수준.

**산물.** `sio2_bks_npt300_tail.data`, `npt_tail_avg.dat`, `npt_tail.log`.
구 `sio2_bks_npt300.data`(tail off)는 비교용으로 남겨둠.
