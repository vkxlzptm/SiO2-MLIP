#!/usr/bin/env bash
# Part 2 덱 마감 파이프라인 — build 이후의 반복 작업을 한 번에.
#
#   1) clean.py      : 삭제된 슬라이드가 남긴 미디어·notesSlide 정리
#                      (안 하면 validate 가 "Unreferenced file" 로 CRITICAL 을 낸다)
#   2) 총 장수 수정  : 마스터의 "/ 7" 이 **하드코딩**이라 자동 갱신되지 않는다
#   3) ko_pptx apply : 한글 줄바꿈 속성(eaLnBrk 등) + 자동축소 해제
#   4) validate      : --original 로 v10 을 기준선 삼아 템플릿 자체 오류를 뺀다
#   5) 렌더          : PDF → JPG (시각 QA용)
#
# 사용: bash finish_part2.sh [총_슬라이드_수]
set -e
cd "$(dirname "$0")"
SK=/sessions/sweet-amazing-tesla/mnt/.claude/skills
DECK=SiO2_MLIP_SevenNet_pilot_part2_v1.pptx
BASE=SiO2_MLIP_SevenNet_pilot_v10.pptx
N=${1:-10}
W=/tmp/pptwork

rm -rf $W/unp && mkdir -p $W/unp && cd $W/unp
python3 -c "import zipfile,sys;zipfile.ZipFile(sys.argv[1]).extractall('.')" "$OLDPWD/$DECK"
python3 $SK/pptx/scripts/clean.py . >/dev/null 2>&1 || true

python3 - "$N" << 'PY'
import sys
p = "ppt/slideMasters/slideMaster1.xml"
t = open(p, encoding="utf8").read()
import re
t2 = re.sub(r"<a:t>/ \d+</a:t>", f"<a:t>/ {sys.argv[1]}</a:t>", t)
open(p, "w", encoding="utf8").write(t2)
print(f"  총 장수 -> {sys.argv[1]}")
PY

rm -f $W/out.pptx && zip -Xrq $W/out.pptx .
cd "$OLDPWD"
cp $W/out.pptx "$DECK"

python3 $SK/korean-ppt-standards/scripts/ko_pptx.py apply "$DECK"
echo "---- validate ----"
python3 $SK/pptx/scripts/office/validate.py "$DECK" --original "$BASE" 2>&1 | tail -4

rm -f $W/*.pdf
python3 $SK/pptx/scripts/office/soffice.py --headless --convert-to pdf --outdir $W "$DECK" >/dev/null 2>&1
cd $W && rm -f v-*.jpg && pdftoppm -jpeg -r 100 "${DECK%.pptx}.pdf" v
cp v-*.jpg /sessions/sweet-amazing-tesla/mnt/outputs/pptqa/ 2>/dev/null || true
echo "렌더 완료: /sessions/sweet-amazing-tesla/mnt/outputs/pptqa/v-*.jpg"
