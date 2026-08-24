#!/bin/bash
# BKS Tg(rate) 확장 스윕 — 기존 3점(5e12,2e13,5e13)에 5개 냉각률 추가 +
# 매칭률(2e13) 반복 2회(다른 속도시드). profile-only(in.mqbks_fast)라 가볍다.
# 순차 실행 — 6랭크가 이미 코어를 다 쓰므로 여러 개를 동시에 돌려도 무이득
# (지난 스레드/프로세스 벤치마크: 6개에서 이미 대역폭 포화).
set -e
cd "$(dirname "$0")"
mkdir -p profiles logs

exec 9>/tmp/.s4_bks_sweep.lock
flock -n 9 || { echo "이미 실행 중이다. 중복 실행 차단."; exit 1; }

export OMP_NUM_THREADS=1

run() {
  local ns=$1 tag=$2 seed=${3:-90210}
  echo "=== BKS sweep: ${tag}  (ns=${ns}, seed=${seed}, rate=$(python3 -c "print(f'{1e17/${ns}:.2e}')") K/s) ==="
  mpirun -np 6 lmp_7net -in in.mqbks_fast -var ns "${ns}" -var tag "${tag}" -var seed "${seed}" \
      > "logs/mqbks_${tag}.log" 2>&1
  tail -3 "logs/mqbks_${tag}.log"
}

#      ns       tag
run  100000    1e12          # 1.0e12 K/s  (~1.8 h)
run   50000    2e12          # 2.0e12 K/s  (~0.9 h)
run   10000    1e13          # 1.0e13 K/s  (~11 min)
run    1000    1e14          # 1.0e14 K/s  (~2 min)
run     500    2e14          # 2.0e14 K/s  (~1 min)

# 매칭률(2e13) 반복 — 7net과 직접 비교하는 지점의 시드 대 시드 산포
run    5000    2e13_r2   90211
run    5000    2e13_r3   90212

echo "=== SWEEP DONE ==="
ls -la profiles/mqbks_*_profile.dat
