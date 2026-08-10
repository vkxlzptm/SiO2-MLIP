# SevenNet + LAMMPS 처음부터 세팅하기 (검증된 절차)

2026-08-10, Ubuntu 20.04 / i5-11600K (6c12t) / RAM 15 GB / **GPU 없음** 환경에서 실제로 성공한 순서.
위에서 아래로 그대로 실행하면 된다. 각 단계 끝에 **[확인]** 이 있으면 통과 후 다음으로 갈 것.

> GPU가 있는 머신이면 §9의 차이점만 반영하면 된다.

---

## 0. 사전 조건 확인

```bash
python3 -V                    # >= 3.10
gcc --version | head -1       # >= 9.4  (PyTorch 권장 하한)
cmake --version | head -1     # 아래 §3에서 재조정함
mpirun --version | head -1    # MPI 종류 기록 (빌드/실행 launcher 일치용)
nvidia-smi                    # 없으면 CPU 경로
free -g | head -2             # make -j 값 결정용
```

**[기록]** MPI가 여러 개 설치된 머신이면 어느 것이 PATH 우선인지 반드시 적어둘 것.
빌드에 쓴 MPI와 다른 `mpirun`으로 실행하면 **에러 없이** 같은 계산을 N번 반복하는 버그가 난다.

---

## 1. Python 환경

```bash
conda create -n mlip python=3.11 -y
conda activate mlip
python -m pip install -U pip
```

## 2. PyTorch — CPU 휠 명시

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install ase
python -c "import torch;print(torch.__version__, torch.cuda.is_available())"
```

**[확인]** `2.x.x+cpu False`

> 그냥 `pip install torch` 하면 기본값이 CUDA 빌드라 2 GB 넘는 NVIDIA 라이브러리가 딸려온다.
> 또한 여기서 고른 torch가 그대로 **LAMMPS가 링크할 libtorch**가 된다. 나중에 torch를 바꾸면
> LAMMPS도 재빌드해야 한다.

## 3. 빌드 도구 — cmake는 `3.18 ≤ v < 4.0`

```bash
pip install "cmake<4"
hash -r
which cmake && cmake --version
```

**[확인]** conda 환경 경로의 cmake, 버전 3.31.x 계열

- 3.18 미만: libtorch의 `TorchConfig.cmake`가 요구하는 하한에 못 미침
- 4.0 이상: `cmake_minimum_required(VERSION < 3.5)` 호환성이 제거되어 2023년 LAMMPS 트리에서
  "Compatibility with CMake < 3.5 has been removed"로 죽을 수 있음
- 굳이 4.x를 쓰려면 cmake 인자에 `-D CMAKE_POLICY_VERSION_MINIMUM=3.5`

## 4. SevenNet — **PyPI 말고 GitHub main**

```bash
cd ~
git clone https://github.com/MDIL-SNU/SevenNet.git SevenNet-src
cd SevenNet-src
git log -1 --format="%H %cd %s"     # 커밋 해시 기록 (재현성)
pip install -e .
```

> PyPI `sevenn==0.13.0`에는 `7net-nano-*` 이름 매핑이 없다 (`util.py:pretrained_name_to_path`에
> 분기 자체가 없음). nano 체크포인트는 GitHub 릴리스 `v0.13.1.cp` 태그에 있고, main 브랜치
> 코드만 그 URL을 안다. `sevenn.__version__`이 `0.13.0`으로 뜨는 건 정상 — 판별 기준은 §5.

## 5. 체크포인트 확보 + 무결성 확인

```bash
sevenn cp 7net-nano-5.5
```

**[확인]** Cutoff 5.5 / Channel 32 / Lmax 2 / Interaction layers 3 / O3 / Elements 119
체크포인트 파일은 약 458 KB (÷4 byte ≈ 논문의 105k 파라미터와 정합).

체크포인트 config에 `use_flash_tp: True`가 박혀 있는데 CPU에서는 flash 없이 빌드해야 한다.
이 경우 `build_model()`이 "Converting model backend..." 경로로 빠지며 **`load_state_dict(strict=False)`**
를 쓰므로, 키 누락이 있어도 에러가 안 난다. 반드시 직접 검사할 것:

```bash
python - <<'PY'
from sevenn.util import load_checkpoint
cp = load_checkpoint('7net-nano-5.5')
m  = cp.build_model(enable_flash=False)
a, b = set(m.state_dict()), set(cp.model_state_dict)
print('model에만:', sorted(a - b))
print('cp에만  :', sorted(b - a))
PY
```

**[확인]** `cp에만` 이 **빈 리스트**여야 한다 (체크포인트 값이 하나도 안 버려졌다는 뜻).
`model에만` 쪽에는 아래 세 종류만 나와야 하며, 전부 학습 파라미터가 아닌 **상수 버퍼**다:

| 키 | 정체 |
|---|---|
| `*_w3j_*` | Wigner 3j 계수 (수학 상수) |
| `*.output_mask` | 0이 아닌 irrep 성분 마스크 |
| `*.convolution.weight` | NequIP형 conv는 가중치를 radial MLP에서 외부 주입 → 빈 텐서 |

이 셋은 `sevenn/checkpoint.py`의 `e3nn_only_conv_followers`에 "무시해도 되는 키"로 명시돼 있다.
다른 키가 나오면 **중단**.

---

## 6. LAMMPS 소스 + 패치

```bash
cd ~
git clone https://github.com/lammps/lammps.git lammps_sevenn \
    --branch stable_2Aug2023_update3 --depth=1
sevenn patch_lammps ~/lammps_sevenn
```

**버전 고정 필수.** `pair_style e3gnn` (TorchScript 경로)은 `stable_2Aug2023_update3`에만 검증돼 있다.
`--d3` / `--flashTP` / `--oeq`는 붙이지 않는다 (전부 CUDA 필요).

**[확인]** 출력에 아래가 있어야 한다.
- `Patched CMakeLists.txt: include LibTorch, CXX_STANDARD 17`
- `[FlashTP] Skipped: not provided`, `[OEQ] Skipped: not provided`
- LAMMPS 버전 불일치 경고가 **없을 것**

패치가 하는 일: `pair_e3gnn.{cpp,h}`, `pair_e3gnn_parallel.{cpp,h}`, `comm_brick.{cpp,h}`,
`pair_e3gnn_oeq_autograd.cpp`를 `src/`에 복사 + 원본을 `_backups/`에 백업 + CMakeLists에 libtorch 링크.

## 7. **[CPU 전용 필수]** CUDA 의존 파일 제거

```bash
cd ~/lammps_sevenn
rm -f src/pair_e3gnn_parallel.cpp src/pair_e3gnn_parallel.h
cp _backups/comm_brick.cpp _backups/comm_brick.h src/
grep -rl cuda_runtime src/ || echo "OK: CUDA 의존 파일 없음"
```

**[확인]** `OK: CUDA 의존 파일 없음`

이유: `pair_e3gnn_parallel.cpp`가 `#include <cuda_runtime.h>` 하고 `cudaMalloc/cudaFree`를
**`#ifdef` 가드 없이** 호출한다. LAMMPS cmake는 `src/*.cpp`를 전부 glob하므로, 쓰지 않을 파일
하나 때문에 CUDA 툴킷 없는 머신에서 빌드 전체가 죽는다.

`comm_brick`을 원본으로 되돌리는 이유: 패치본은 `PairE3GNNParallel` 통신 훅을 갖고 있어
짝이 없으면 링크 에러가 난다. 직렬 `pair_e3gnn.cpp`는 `comm_brick`을 쓰지 않으므로 안전.
`pair_e3gnn_oeq_autograd.cpp`는 **지우면 안 된다** (`pair_e3gnn.cpp`가 extern 참조, 내용은 순수 libtorch).

> 지운 파일 원본은 `~/SevenNet-src/sevenn/pair_e3gnn/`에 그대로 있다. GPU 머신에서 되살리려면
> `pair_e3gnn_parallel.{cpp,h}`와 `comm_brick.{cpp,h}`를 다시 복사하면 된다.

## 8. cmake 설정 + 빌드

```bash
cd ~/lammps_sevenn && mkdir -p build && cd build

cmake ../cmake \
  -D CMAKE_BUILD_TYPE=Release \
  -D CMAKE_PREFIX_PATH=$(python -c 'import torch;print(torch.utils.cmake_prefix_path)') \
  -D PKG_KSPACE=ON \
  -D PKG_MANYBODY=ON \
  -D PKG_EXTRA-PAIR=ON \
  -D PKG_MOLECULE=ON \
  -D BUILD_MPI=yes
```

- `PKG_KSPACE`는 **비교군 BKS**(`buck/coul/long` + `pppm`)에 필수. 같은 바이너리로 두 포텐셜을
  다 돌려야 비교가 공정해진다.

무해한 경고 두 개:
- `library kineto not found` — PyTorch 프로파일러. 추론에 안 씀
- `libgomp.so.1 ... may be hidden by files in torch/lib` — 실제로는 torch 번들 것 하나로 해결됨.
  런타임에 `OMP: Error #15`가 뜨면 이게 원인

```bash
time make -j8 2>&1 | tee build.log        # RAM 15GB 기준 -j8. 32GB+면 -j12
```

소요: 6c12t에서 **약 1분 10초** (CPU time 8분 40초).

```bash
grep -inE "error" build.log | head        # error.h / error.cpp 파일명만 나와야 함
ln -sf ~/lammps_sevenn/build/lmp ~/bin/lmp_7net    # ~/bin 이 PATH에 있는 경우
hash -r
```

### [확인] 빌드 검증 3종

```bash
lmp_7net -h 2>&1 | grep -oiE "\be3gnn(/parallel)?\b|buck/coul/long|\bpppm\b" | sort -u
ldd ~/lammps_sevenn/build/lmp | grep -iE "torch|gomp|not found"
```

- 1행: `buck/coul/long`, `e3gnn`, `pppm` 세 개. **`e3gnn/parallel`은 없어야 정상** (§7에서 제거)
- 2행: `libtorch.so`, `libtorch_cpu.so`, `libc10.so`가 경로와 함께 나오고 `not found` 없음
- `libgomp`가 **한 곳에서만** 잡히는지 확인

> ⚠ `lmp`는 conda 환경 안의 `libtorch.so`를 절대경로로 물고 있다.
> **`mlip` 환경을 지우거나 재생성하면 LAMMPS를 다시 빌드해야 한다.**

## 9. 포텐셜 배포

```bash
mkdir -p $PROJ/01_input/pot && cd $PROJ/01_input/pot
sevenn get_model 7net-nano-5.5
ls -lh deployed_serial.pt      # 약 471 KB
```

`No tensor product accelerator is enabled` 경고는 CPU에서 정상 (느릴 뿐).
`Converting model backend...`도 정상 (§5의 flash→e3nn 변환).

LAMMPS 입력에서:

```lammps
units       metal
atom_style  charge          # 데이터 파일이 charge 스타일인 경우. e3gnn은 q를 무시함
pair_style  e3gnn
pair_coeff  * * ./pot/deployed_serial.pt O Si
```

**`pair_coeff` 뒤 원소 순서 = LAMMPS type 순서다.** type1=O, type2=Si이면 반드시 `O Si`.
거꾸로 써도 에러가 안 나고 결과만 틀린다. 로그에서 확인:
```
Chemical specie 'O' is assigned to type 1
Chemical specie 'Si' is assigned to type 2
```

## 10. 실행 규칙 (CPU)

```bash
export OMP_NUM_THREADS=6      # 물리코어 수. HT(12)는 추론에서 이득이 없거나 손해일 수 있음
lmp_7net -in in.xxx           # mpirun 없이 단일 랭크
```

**`mpirun -np N`으로 `pair_style e3gnn`을 돌리지 말 것.**
`pair_e3gnn.cpp`는 로컬 원자 tag만 map에 넣고 없는 이웃은 버리므로, 도메인 분할을 하면
다른 랭크 소유 ghost 원자의 edge가 **조용히 누락되고 힘이 틀린다.**
(다중 랭크용 `e3gnn/parallel`은 GPU 전용이라 이 빌드엔 없다.)

BKS 같은 고전 포텐셜 런은 MPI 병렬 정상 사용 가능. 단 **빌드에 쓴 MPI의 launcher**를 쓸 것.

---

## 11. GPU 머신에서 달라지는 점

| 단계 | 변경 |
|---|---|
| §2 | `pip install torch --index-url .../whl/cu124` (CUDA 버전에 맞춰) |
| §7 | **생략.** `pair_e3gnn_parallel`과 패치된 `comm_brick`을 그대로 둔다 |
| §8 | 동일. `e3gnn/parallel`도 빌드됨 |
| §9 | 가속기 사용 시 `sevenn get_model 7net-nano-5.5 --enable_flash` (flashTP 선설치 필요) |
| §10 | 다중 GPU면 `pair_style e3gnn/parallel` + `mpirun -np <GPU수>`, GPU 1장이면 그대로 직렬 |

가속기(cuEquivariance / FlashTP / OpenEquivariance)는 equivariant tensor product를 융합 CUDA
커널로 대체하는 물건이라 **전부 GPU 전용**이다. CPU에는 대응물이 없다.

---

## 12. 이 환경의 실측 기록

```
OS          Ubuntu 20.04
CPU         Intel i5-11600K (6c/12t),  RAM 15 GB,  GPU 없음
gcc         9.4.0
cmake       (pip) 3.31.x
python      3.11
torch       2.13.0+cpu
sevenn      GitHub main  (__version__ 0.13.0으로 표시)
MPI         Intel oneAPI MPI 2021.5   ← OpenMPI도 설치돼 있으나 PATH 우선순위는 Intel
LAMMPS      stable_2Aug2023_update3 + sevenn patch_lammps, C++17
빌드 시간   make -j8 → real 1m10s / user 8m39s
lmp 크기    12 MB (libtorch는 동적 링크)
체크포인트  checkpoint_7net_nano_5.5.pth 458 KB / deployed_serial.pt 471 KB
```
