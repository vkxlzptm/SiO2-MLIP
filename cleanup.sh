#!/bin/bash
# 폐기 파일 정리 — 기본은 **드라이런**(목록만 출력). 실제 삭제는 --yes 를 붙인다.
#
#   ./cleanup.sh          # 뭐가 지워질지 보기만
#   ./cleanup.sh --yes    # 실제 삭제
#
# 샌드박스(Claude)는 파일을 못 지우므로 이 스크립트는 **사용자가 직접 실행**한다.
# 삭제 후 ./sync.sh 로 커밋하면 된다.

cd "$(dirname "$0")"
DRY=1; [ "$1" = "--yes" ] && DRY=0
if [ $DRY -eq 1 ]; then echo "※ 드라이런입니다. 실제로 지우려면  ./cleanup.sh --yes"; fi
echo

TOTAL=0
kill_it() {   # kill_it <경로> <이유>
  local p="$1" why="$2"
  [ -e "$p" ] || return 0
  local sz; sz=$(du -sk "$p" 2>/dev/null | cut -f1); TOTAL=$((TOTAL+sz))
  printf "  %6s KB  %-52s %s\n" "$sz" "$p" "$why"
  [ $DRY -eq 0 ] && rm -rf "$p"
}

echo "── A. 완전 중복 / 재생성 가능 ────────────────────────────────"
kill_it init_struct                       "01_input 과 비트 동일(md5 일치), 이미 gitignore"
kill_it 04_analysis/src/old_delete        "구세대 작도 스크립트"
kill_it 04_analysis/fig/old_delete        "구 그림 + PDF (PNG 만 쓰기로 함)"
kill_it 03_result                         "한 번도 안 쓴 빈 placeholder (결과는 05_doc)"

echo
echo "── B. 폐기된 실행의 잔재 ─────────────────────────────────────"
# 1차 BKS E-V 스캔은 창을 잘못 잡아 폐기. f=1.04/1.06 은 현 스캔 목록(0.90~1.02) 밖이라
# 남아 있으면 "왜 이것만 있지?" 하고 헷갈린다. 정의는 같지만 쓸 데가 없다.
kill_it 02_run/s2_relax/ev_bks_f1.04.log  "1차 BKS 스캔 잔재 (현 목록 밖)"
kill_it 02_run/s2_relax/ev_bks_f1.06.log  "1차 BKS 스캔 잔재 (현 목록 밖)"

echo
echo "── C. OS 쓰레기 ──────────────────────────────────────────────"
find . -name ".DS_Store" -not -path "./.git/*" 2>/dev/null | while read -r f; do
  printf "  %6s KB  %s\n" "$(du -sk "$f" | cut -f1)" "$f"
  [ $DRY -eq 0 ] && rm -f "$f"
done

echo
echo "────────────────────────────────────────────────────────────────"
printf "A+B 합계 약 %d KB\n" "$TOTAL"
[ $DRY -eq 1 ] && echo "(드라이런 — 아무것도 안 지웠습니다)"

cat <<'EOF'

── 지우지 않은 것들과 그 이유 ──────────────────────────────────

02_run/_v1_superseded/  (976 KB)
    ρ=2.607 폐기 계산. **남겨둔다.** README.md 에 실패 경위가 있고,
    "MSD 검증 없이 melt-quench 를 믿지 말 것" 이 이 프로젝트의 핵심 교훈이다.
    면접에서 실패 사례를 물으면 근거로 보여줄 자료다.

02_run/s0_requench/sio2_bks_npt300.data  (tail off)
    현행은 _tail 쪽이지만, tail 관례가 밀도를 1.3 % 움직인다는 대조 증거다.

02_run/s2_relax/ev_bks_f*_tail.log  (7개)
    tail 보정 진단의 대조군 원자료. 결론(원인 확정)의 유일한 직접 증거다.

04_analysis/fig/quench_VT.png,  quench220_fit.png
    RESULTS.md 가 참조하지 않지만 melt-quench 진단 그림이다.
    quench_VT.png 는 v1 실패(4500 K 에서 밀도 붕괴)를 보여주는 그림일 가능성이 높다.
    → 확인 후 _v1_superseded/ 로 옮기든지 RESULTS 에 인용하든지 결정할 것.

04_analysis/src/ev_fit.py,  ev220_fit.py,  quench220_fit.py
    문서 참조 0~1. ev_fit.py 는 v1 전용, ev220_fit.py 는 fig_density.py 가 흡수했다.
    지워도 되지만 **간이 CLI 피팅 도구**로는 여전히 쓸모가 있어 판단은 남긴다.

05_doc/jp6c00944_si_001.pdf  (0.6 MB), dechant_figs/  (0.6 MB)
    AIMD 참조 문헌 원본. digitize 재현에 필요하다.
EOF
