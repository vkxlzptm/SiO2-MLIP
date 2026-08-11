#!/usr/bin/env bash
# 양방향 동기화. 노트북·원격 어디서든 그냥 ./sync.sh
#
#   ./sync.sh              → .commit_msg 내용을 커밋 메시지로 사용
#   ./sync.sh "메시지"      → 인자를 커밋 메시지로 사용
#
# 하는 일: 잔여 lock 제거 → add -A → commit(변경 있을 때만) → pull(merge) → push
set -u
cd "$(dirname "$0")" || exit 1

rm -f .git/HEAD.lock .git/index.lock .git/refs/heads/*.lock 2>/dev/null

MSG="${1:-}"
if [ -z "$MSG" ]; then
  if [ -s .commit_msg ]; then
    MSG=$(cat .commit_msg)
  else
    MSG="sync from $(hostname -s) $(date +%F_%H%M)"
  fi
fi

git add -A
if git diff --cached --quiet; then
  echo "[sync] 커밋할 변경 없음"
else
  git commit -m "$MSG" || exit 1
  echo "[sync] 커밋: ${MSG%%$'\n'*}"
fi

git config pull.rebase false
if ! git pull --no-rebase --no-edit; then
  echo ""
  echo "!! 충돌 발생. 아래로 상태 확인 후 수동 해결:"
  echo "   git status --short"
  echo "   git checkout --ours <파일>   # 또는 --theirs"
  echo "   git add <파일> && git commit --no-edit && git push"
  exit 1
fi

git push || exit 1
echo ""
git log --oneline -3
