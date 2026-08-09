# S0-2. 설치 계획 — LAMMPS + SevenNet 연동 (rev.2)

> rev.1(ASE 우회)에서 변경. **LAMMPS `pair_style e3gnn` 연동으로 확정.**

## 0. 경로 선택: 왜 ML-IAP가 아니라 TorchScript(e3gnn)인가

| | 경로 1: **e3gnn (TorchScript)** ← 채택 | 경로 2: ML-IAP (`mliap unified`) |
|---|---|---|
| LAMMPS 버전 | `stable_2Aug2023_update3` 고정 | `stable_22Jul2025_update4` |
| 추가 의존성 | libtorch(=pip torch)만 | Kokkos + CUDA + cupy + cython |
| GPU 필수? | **아니오** (소스에서 CUDA 없으면 CPU로 자동 폴백 확인함) | **예** |
| 병렬 MD | `e3gnn/parallel` (다중 GPU, 공식 권장) | 문서상 "충분히 테스트되지 않음" |
| 빌드 난이도 | 중 | 상 |

근거: `sevenn/pair_e3gnn/pair_e3gnn.cpp` 생성자에
`if (torch::cuda::is_available()) device=kCUDA; else device=kCPU;`
→ **GPU가 없어도 같은 빌드가 CPU로 돈다.** 그래서 GPU 유무와 무관하게 경로 1이 안전하다.
공식 문서도 다중 rank 실행은 ML-IAP 대신 e3gnn/parallel을 쓰라고 명시.

**기존 LAMMPS는 건드리지 않는다.** 별도 소스 트리(`lammps_sevenn`)를 새로 빌드한다.
단, 새 빌드에 KSPACE를 넣어서 **BKS도 같은 바이너리로 돌릴 수 있게** 한다
(RDF 3자 비교에서 코드/설정 차이를 변수에서 제거).

---

## 1. GPU / 환경 확인 (원격에서 먼저 실행)

```bash
nvidia-smi
echo "--- nvcc ---"
nvcc --version 2>/dev/null || echo "nvcc 없음"
echo "--- compiler ---"
gcc --version | head -1; cmake --version | head -1; python3 -V
echo "--- mpi ---"
mpicxx --version 2>/dev/null | head -1 || echo "mpicxx 없음"
echo "--- cpu/mem ---"
lscpu | grep -E "^Model name|^CPU\(s\):|^Socket"
free -g | head -2
echo "--- 기존 lammps ---"
which lmp lmp_mpi lmp_serial 2>/dev/null
```

이 출력 붙여넣어 주면 CUDA 휠 버전과 Kokkos 여부를 확정한다.
(gcc는 9 이상, cmake는 3.16 이상 필요. cmake가 낮으면 `pip install cmake`로 해결 가능.)

---

## 2. Python 환경 + sevenn

```bash
conda create -n mlip python=3.11 -y && conda activate mlip
# conda 없으면: python3 -m venv ~/venv-mlip && source ~/venv-mlip/bin/activate
python -m pip install -U pip
```

**확정: 이 머신은 GPU 없음 (i5-11600K, 6코어/12스레드). CPU 휠을 쓴다.**
```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

> Accelerator(cuEquivariance / FlashTP / OpenEquivariance)는 **전부 CUDA 전용**이다.
> 설치하지 않는다. `patch_lammps`에 `--enable_flash`, `--enable_oeq`도 붙이지 않는다.

**sevenn은 PyPI가 아니라 GitHub main에서 설치해야 한다.**
PyPI 0.13.0에는 `7net-nano-*` 이름 매핑이 없다 (`util.py:pretrained_name_to_path`에 분기 없음).
nano 체크포인트는 GitHub 릴리스 `v0.13.1.cp` 태그에 올라와 있고, main 브랜치 코드만 그 URL을 안다.

```bash
pip install ase
cd ~ && git clone https://github.com/MDIL-SNU/SevenNet.git SevenNet-src
cd SevenNet-src
git log -1 --format="%H %cd %s" | tee $PROJ/00_env/sevenn_commit.txt   # 재현성: 커밋 해시 기록
pip install -e .
```

> `sevenn.__version__`은 `0.13.0`으로 뜬다 (main의 버전 문자열이 아직 안 올라감). 정상이다.
> 판별 기준은 버전이 아니라 `sevenn cp 7net-nano-5.5`가 되는지 여부.

검증:
```bash
python -c "import torch;print('torch',torch.__version__,'cuda',torch.cuda.is_available())"
sevenn cp 7net-nano-5.5
```

> **torch 버전 주의(미검증 휴리스틱):** LAMMPS `stable_2Aug2023_update3`는 2023년 코드라
> 최신 libtorch와 링크 시 ABI/`CMAKE_CXX_STANDARD` 충돌이 보고되는 경우가 있다.
> 3-1의 빌드가 undefined reference로 실패하면 `torch==2.5.1`로 내려서 재시도.
> 이건 확인된 사실이 아니라 대응책이므로, 처음엔 최신으로 시도할 것.

체크포인트 확인:
```bash
sevenn cp 7net-nano-5.5
```
→ Cutoff 5.5 / Channel 32 / Lmax 2 / Interaction layers 3 이 찍히면 정상.

---

### 2-1. 확보한 체크포인트 실측값 (2026-08 확인)

```
checkpoint_7net_nano_5.5.pth   458 KB
Sevennet version      0.12.0.dev0     (학습에 쓴 버전)
Hash                  238dab8affec439d87ed50e672f5c47e   /  When 2025-12-16
Cutoff / Channel / Lmax / Layers    5.5 / 32 / 2 / 3     ← 논문과 일치
Group (parity)        O3                                 ← parity=full, 문서와 일치
Self connection type  linear                             ← 논문 미기재. 7net-0은 nequip
Elements              119
FlashTP used          True                               ← 주의, 아래 참조
```

- **458 KB ÷ 4 byte ≈ 115k** → 논문의 "105k 파라미터"와 정합. 독립 검증됨.
- `self_connection_type = linear`는 논문에 없는 정보. self-connection을 full tensor product 대신
  linear로 바꾼 것도 경량화 기여분 중 하나로 보인다. (발표에 쓸 만한 디테일)

### 2-2. ⚠ FlashTP 플래그 문제 (검증 필요)

체크포인트 config에 `use_flash_tp: True`가 박혀 있다. CPU에서는 flash 없이 빌드해야 하는데,
`SevenNetCheckpoint.build_model()`은 이 불일치를 감지하면 "Converting model backend..." 경로로 빠져
**`load_state_dict(..., strict=False)`** 로 로드한다 → **키가 누락돼도 에러가 안 난다.**

FlashTP는 보통 파라미터 레이아웃을 바꾸지 않으므로 무해할 가능성이 높지만, 확인하고 넘어갈 것:

```bash
python - <<'PY'
from sevenn.util import load_checkpoint
cp = load_checkpoint('7net-nano-5.5')
m  = cp.build_model(enable_flash=False)
a, b = set(m.state_dict()), set(cp.model_state_dict)
print('model에만 있는 키(로드 안 된 파라미터):', sorted(a - b))
print('checkpoint에만 있는 키(버려진 값)   :', sorted(b - a))
PY
```
→ **양쪽 모두 빈 리스트여야 정상.** 뭔가 나오면 조용히 틀린 포텐셜이 되므로 즉시 중단.

### 2-3. 빌드 도구 (cmake 버전이 미묘함)

실측: 시스템 gcc **9**, 시스템 cmake **3.16.3** (Ubuntu 20.04 기본값).

- cmake 3.16은 libtorch 2.x의 `TorchConfig.cmake`(≥3.18 요구)에 못 미친다 → 올려야 함
- 그런데 **cmake 4.x는 반대로 위험하다.** 4.0부터 `cmake_minimum_required(VERSION < 3.5)`
  호환성이 제거되어, 2023년 LAMMPS 트리에서 "Compatibility with CMake < 3.5 has been removed"로
  죽는 경우가 있다.
- → **3.18 ≤ cmake < 4.0 구간으로 고정한다.**

```bash
pip install "cmake<4"          # 3.31.x 계열이 설치됨
hash -r
which cmake && cmake --version # ~/anaconda3/envs/mlip/bin/cmake, 3.31.x 확인
```

> 이미 4.x를 깔았다면 위 명령이 다운그레이드해준다.
> 굳이 4.x를 유지해야 한다면 cmake 인자에 `-D CMAKE_POLICY_VERSION_MINIMUM=3.5`를 추가할 것.

gcc 9는 일단 그대로 시도한다. libtorch 헤더에서 C++17 관련 에러가 나면 (sudo 없이):
```bash
conda install -c conda-forge gxx_linux-64=11 -y
export CXX=$CONDA_PREFIX/bin/x86_64-conda-linux-gnu-g++
```

## 3. LAMMPS 빌드

### 3-1. 소스 받기 + 패치

```bash
cd ~
git clone https://github.com/lammps/lammps.git lammps_sevenn \
    --branch stable_2Aug2023_update3 --depth=1

sevenn patch_lammps --help          # 옵션 확인 (cxx_standard 지정 방법 등)
sevenn patch_lammps ./lammps_sevenn # --d3 / --enable_flash / --enable_oeq 붙이지 말 것
```

`patch_lammps`가 하는 일:
- `pair_e3gnn.{cpp,h}` (직렬), `pair_e3gnn_parallel.{cpp,h}` (다중 GPU),
  `comm_brick.{cpp,h}` (parallel용 통신 패치), `pair_e3gnn_oeq_autograd.cpp` 를 `src/`에 복사
- 원본 `comm_brick.*`, `cmake/CMakeLists.txt`를 `_backups/`에 백업
- `CMakeLists.txt`에 libtorch 링크 추가 + C++ 표준 상향

### 3-1b. **[CPU 전용 필수] parallel 파일 제거**

`pair_e3gnn_parallel.cpp`는 `#include <cuda_runtime.h>` 하고 `cudaMalloc/cudaFree/cudaMemGetInfo`를
**조건 없이** 호출한다. LAMMPS cmake는 `src/*.cpp`를 전부 glob하므로,
**CUDA 툴킷이 없는 이 머신에서는 빌드가 `fatal error: cuda_runtime.h: No such file or directory`로 죽는다.**

패치 직후 아래를 실행할 것:

```bash
cd ~/lammps_sevenn
rm -f src/pair_e3gnn_parallel.cpp src/pair_e3gnn_parallel.h
cp _backups/comm_brick.cpp _backups/comm_brick.h src/     # 원본으로 복원
grep -rl cuda_runtime src/ || echo "OK: CUDA 의존 파일 없음"
```

- `comm_brick`의 SevenNet 패치는 **오직 `e3gnn/parallel` 전용**이다. 직렬 `pair_e3gnn.cpp`는
  `comm_brick`을 전혀 쓰지 않으므로 원본 복원해도 안전하다. (복원 안 하면 `PairE3GNNParallel`
  심볼이 없어 링크 에러가 난다.)
- `pair_e3gnn_oeq_autograd.cpp`는 **지우면 안 된다.** `pair_e3gnn.cpp`가 extern으로 참조한다.
  내용은 순수 libtorch라 CUDA 없이 컴파일된다.

### 3-2. cmake 설정

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

- `PKG_KSPACE`: BKS의 `buck/coul/long` + `pppm/ewald`에 필수. **이걸 빼면 기존 BKS 입력이 안 돈다.**

에러별 대응 (나오면 인자 추가 후 재실행):

| 에러 메시지 | 추가할 인자 |
|---|---|
| `MKL_INCLUDE_DIR NOT-FOUND` | `-D MKL_INCLUDE_DIR=/tmp` |
| C++ 표준 관련 / libtorch 헤더 에러 | `-D CMAKE_CXX_STANDARD=17 -D CMAKE_CXX_STANDARD_REQUIRED=ON` |
| `Compatibility with CMake < 3.5 has been removed` | `-D CMAKE_POLICY_VERSION_MINIMUM=3.5` (또는 cmake<4로 다운그레이드) |
| `Could not find Torch` | `CMAKE_PREFIX_PATH` 경로 확인 — conda 환경이 activate 됐는지부터 볼 것 |

cmake 재실행 시에는 캐시가 남아 혼란스러우므로 `rm -rf build/*` 후 다시 하는 편이 안전하다.

### 3-3. 빌드

```bash
make -j6 2>&1 | tee $PROJ/00_env/lammps_build.log
ls -lh lmp
mkdir -p ~/.local/bin && ln -sf ~/lammps_sevenn/build/lmp ~/.local/bin/lmp_7net
```

빌드 검증:
```bash
lmp_7net -h | grep -iE "e3gnn|buck/coul/long|pppm"
```
→ `e3gnn`, `buck/coul/long`, `pppm`이 보이면 성공.
 (`e3gnn/parallel`은 3-1b에서 제거했으므로 **안 보이는 게 정상**이다.)

### 3-4. 바이너리 정리 — 어느 실행파일을 쓰나

| 바이너리 | 용도 |
|---|---|
| 기존 `lmp_serial`, `lmp_mpi` | **더 이상 쓰지 않는다.** `pair_style e3gnn`이 없다. 단, 새 빌드의 BKS 결과가 기존 결과와 일치하는지 확인하는 **교차검증용**으로만 한 번 사용 |
| 신규 `lmp_7net` (= `lammps_sevenn/build/lmp`) | **BKS도 SevenNet도 전부 이걸로 돌린다.** 같은 바이너리를 써야 비교가 공정 |

새 바이너리는 `BUILD_MPI=yes`로 빌드하므로 mpirun 유무 둘 다 가능하다:
- BKS: `mpirun -np 6 lmp_7net -in in.sio2` (MPI 병렬 OK)
- SevenNet: `lmp_7net -in in.nano` (단일 랭크, OMP 스레드로 병렬)

**예상 소요: 순조로우면 30~60분(컴파일 포함). 링크 에러 발생 시 반나절 각오.**
막히면 즉시 알려줄 것 — 30분 이상 같은 에러면 torch 버전 다운그레이드로 전환한다.

---

## 4. 포텐셜 배포 (deploy)

```bash
mkdir -p $PROJ/01_input/pot && cd $PROJ/01_input/pot
sevenn get_model 7net-nano-5.5
ls -lh deployed_serial.pt
```

- 출력: `deployed_serial.pt` (TorchScript). `pair_style e3gnn`이 이걸 읽는다.
- `--enable_flash` / `--enable_oeq`는 GPU 가속용 — **처음엔 붙이지 말 것**(의존성 추가 = 리스크).
  S1에서 속도가 병목이면 그때 도입.
- 병렬(다중 GPU)은 `--get_parallel`. GPU 1장이면 불필요.

---

## 5. LAMMPS 입력 (핵심 문법)

```lammps
units           metal
atom_style      charge          # 기존 sio2_quenched.data 가 charge 스타일
boundary        p p p
atom_modify     map yes
newton          on

read_data       ../01_input/sio2_quenched.data

pair_style      e3gnn
pair_coeff      * * ./pot/deployed_serial.pt O Si
```

**주의 3가지**

1. `pair_coeff * *` 뒤의 원소 나열 순서는 **LAMMPS type 순서**다.
   우리 데이터는 **type1=O, type2=Si** 이므로 반드시 `O Si` (거꾸로 쓰면 조용히 틀린다).
2. `atom_style charge`로 읽어도 e3gnn은 q를 무시한다. BKS와 동일 데이터 파일을 그대로 쓸 수 있어 편하다.
3. e3gnn은 `units metal`(eV, Å, ps) 전용. BKS 입력도 metal이므로 일치.

로그에서 확인할 것:
```
PairE3GNN using device : CPU
Chemical specie 'O' is assigned to type 1
Chemical specie 'Si' is assigned to type 2
```

### 5-1. CPU 실행 규칙 (중요)

```bash
export OMP_NUM_THREADS=6        # 물리코어 6개. 12(HT)은 보통 더 느림 — S1에서 실측 비교
export MKL_NUM_THREADS=6
lmp_7net -in in.nano_nvt        # mpirun 없이 단일 랭크
```

**`mpirun -np N lmp_7net` 로 `pair_style e3gnn`을 돌리지 말 것.**
근거: `pair_e3gnn.cpp`는 로컬 원자의 tag만 `tag_map`에 넣고, 그 map에 없는 이웃은
`continue`로 버린다. MPI 도메인 분할을 하면 다른 랭크 소유의 ghost 원자가 map에 없어
**edge가 조용히 누락되고 힘이 틀린다.** (다중 랭크용으로 `e3gnn/parallel`이 따로 있는 이유.)
→ 병렬은 MPI가 아니라 **torch의 OMP 스레드**로 받는다.
→ **S1에서 1랭크 vs 2랭크 total energy를 비교해 이 판단을 반드시 검증할 것.** 값이 다르면 확정.

반면 **BKS 런은 MPI 병렬 정상 사용 가능** (`mpirun -np 6 lmp_7net -in in.sio2`).
속도 비교표를 만들 때 이 비대칭을 각주로 밝힐 것.

---

## 6. 버전 기록 (필수)

```bash
cd $PROJ/00_env
pip freeze > pip_freeze_$(date +%Y%m%d).txt
{
  echo "date: $(date -Iseconds)"
  echo "lammps: stable_2Aug2023_update3 + sevenn patch_lammps"
  echo "lammps build: $(cd ~/lammps_sevenn && git rev-parse --short HEAD)"
  python -c "import torch,sevenn,ase;print('torch',torch.__version__,'| sevenn',sevenn.__version__,'| ase',ase.__version__)"
  python -c "import torch;print('cuda',torch.version.cuda,torch.cuda.is_available())"
  nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader 2>/dev/null
  echo "cmake flags: PKG_KSPACE MANYBODY EXTRA-PAIR MOLECULE, BUILD_MPI=yes"
} | tee versions.txt
```

---

## 7. 리스크 & 중단 기준

| 리스크 | 신호 | 대응 |
|---|---|---|
| libtorch 링크 실패 | undefined reference | torch 2.5.1로 다운그레이드 → 그래도 실패 시 보고 |
| KSPACE 누락 | BKS 입력에서 `Unknown pair style buck/coul/long` | cmake 재설정 후 재빌드 |
| type 매핑 오류 | Si-O 첫 피크가 1.6 Å이 아님 | `pair_coeff` 원소 순서 확인 |
| CPU only라 너무 느림 | S1 실측에서 목표 스텝수 불가 | 원자수 축소(2160→~650) 또는 MD 길이 축소. **RDF는 짧아도 수렴함** |

**중단 기준: 빌드에 누적 4시간 이상 → 즉시 보고하고 ASE 폴백 논의.**
(ASE로도 RDF 비교는 가능하다. 다만 이번엔 LAMMPS를 1순위로 간다.)
