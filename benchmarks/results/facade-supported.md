# 후속 인수 검증: 지원 도구에서의 실제 Cott facade

**앞선 R2/R5의 미완료 인수조건을 해소했다.** 동일 CPython 3.14.6, 알고리즘·입력·검사
수준으로 최적화 전후 컴파일러가 각각 정상 emit하고 실제 verify한 facade를 측정했다.
이번에는 compiler·runtime·하네스 코드를 변경하지 않았다. 이전 3.14.4 컴포넌트 수치와
`facade-attempt.json`의 blocked 기록은 그대로 보존하며 이번 결과와 합산하지 않는다.

## 실제 도구 준비

작업 소유 `target/facade-toolchain-followup/`에만 설치했다. 전역 설치, sudo,
사용자 설정 변경, 가짜 버전 wrapper, pin 완화, sandbox 우회는 없다.
`/usr/bin/python3 --version`은 여전히 **3.14.4**다.

| 도구 | 실제 확인 버전 | 출처/설치 |
|---|---|---|
| uv | 0.12.23 | PyPI의 공식 manylinux x86_64 wheel, 게시 SHA-256과 다운로드 일치 확인 후 격리 추출 |
| CPython | 3.14.6, Clang 22.1.3 | uv의 공식 Astral python-build-standalone `20260804`, `--no-bin` 설치 |
| BasedPyright | 1.39.9, based on pyright 1.1.411 | `https://pypi.org/simple`, 작업 전용 venv |
| nodejs-wheel-binaries | 24.19.0 | BasedPyright 의존성, 같은 PyPI/venv |

python.org 인덱스와 3.14.6 source archive, PyPI, npm registry 조회가 모두 HTTP 200이었다.
Python 3.14.6–3.14.8 및 BasedPyright 1.39.9 이상이 실제 배포돼 있었다. metadata 요청당
20초/최대 8MiB, uv 네트워크 read 30초·retry 1, 설치 명령당 180초로 시도를 제한했다.
출처 URL·해시·명령·실제 stdout/stderr는 [toolchain-followup.json](toolchain-followup.json)에 있다.
초기 uv bootstrap helper가 패키지 디렉터리도 executable 후보로 선택한 오류는 파일만
선택하도록 수정하고 같은 해시 검증 wheel을 재사용했다. 바이너리 내용은 바꾸지 않았다.

주요 준비 명령은 아래와 같다. 환경 변수는 **작업 프로세스 안에서만** 설정하고
HOME/cache/Python/bin/tool 디렉터리를 모두 위 격리 디렉터리로 제한했다.
설치된 uv가 없어 PyPI metadata의 정확한 wheel URL과 SHA-256을 사용해 먼저 준비했다.

```sh
# UV = 격리 추출한 실제 uv 실행 파일, ROOT = 작업 소유 절대경로
"$UV" --no-config --no-progress -v python install 3.14.6 --no-bin
"$UV" --no-config python find --managed-python 3.14.6
"$UV" --no-config venv --python "$PY" "$ROOT/venv"
"$UV" --no-config --no-progress pip install --python "$ROOT/venv/bin/python" \
  --index-url https://pypi.org/simple basedpyright==1.39.9
"$PY" --version
"$ROOT/venv/bin/basedpyright" --version
```

실제 설치 환경은 receipt의 `tool_setup.isolated_environment`에 기록돼 있다.
재실행에서는 해당 설정의 `HOME`, `XDG_CACHE_HOME`, `UV_CACHE_DIR`,
`UV_PYTHON_INSTALL_DIR`, `UV_PYTHON_BIN_DIR`, `UV_TOOL_DIR`, `UV_TOOL_BIN_DIR`도
새 작업 디렉터리에 지정한다. 위 명령을 기본 전역 경로로 실행하라는 뜻이 아니다.

## 정상 생성 출력과 검증

- before: 이전 작업에서 **성능 패치 전에 보존한** `target/boundary-baseline/cott`.
  compiler SHA-256은 `3399886dd72649d473315311f9001868357755cc41f36b86d5a7aa6cc5ad6127`.
- after: `target/debug/cott`, SHA-256
  `b82413ad8fa03d204f1b9e456ff6e85bdc8f4f86f0d709622c6baad81a4a7b11`.
- 두 바이너리가 각각 새로운 임시 fixture에 emit → 명시적 verify를 실행했다.
  이전 generated 파일/인증/hash를 복사하거나 수동 변경하지 않았다.
- 각 출력의 runtime bytes는 기존 compiler-owned before/after 컴포넌트 출력과 각각
  일치했다. 그 확인은 **동일 코드의 식별**일 뿐 기존 컴포넌트 결과를 인증한 것이 아니다.
- 새 generation record의 `current == last_verified`, 실제 Python/BasedPyright/compiler
  버전·해시를 읽어 기록하고, 원래 인증 로더를 통과한 facade만 시간 측정했다.
- direct-unchecked/direct-checked는 여전히 provenance 보장이 없다. fixture의 실제
  binding 소스·입력 해시는 두 컴파일러에서 같고, 검증 수준별 행을 따로 비교했다.

정규 측정에서는 **emit 16회, real verify 16회 모두 exit 0**이다.
스모크 2개, 본 행렬 12개, 역순 잡음 확인 2개다. 별도 하네스 단위 회귀의 6회 emit은
실행 성공했지만 인증 측정으로 세지 않는다. 따라서 이번 라운드의 실제 compiler 명령은
총 **emit 22회, verify 16회**이며, 단위 회귀의 loader stub은 성능 측정에 사용하지 않았다.
실제 generate/provider 호출은 **0회**다. 고정 fixture에 `gpt 6.1 sol`이나 다른 모델을
호출할 필요가 없으므로 확인되지 않은 모델을 대체 실행하지 않았다.

## 측정 결과

본 행렬은 sizes 4/128 × depths 1/3 × boundary/test-only 일반·테스트 문맥/off ×
3개 경로를 분리했다. 전후 각각 48개 행, 각 7개 새 프로세스 표본/80회 warm 반복이다.
전체 96행의 warm 표본은 672개이며, 그중 **실제 facade는 32행·warm 224개 + 별도 cold 224개**다.
정확성 검사·메모리·profile 실행은 warm 시간 측정 밖에서 수행했다.

| 실제 facade 조건 | 전 warm 중앙값 | 후 warm 중앙값 | 표본 범위 |
|---|---:|---:|---|
| boundary, 4개, 깊이1 | 59.17µs | 49.73µs | 비중첩 |
| boundary, 128개, 깊이1 | **1,549.39µs** | **1,241.31µs** | 비중첩, 약 19.9% 감소 |
| boundary, 128개, 깊이3 | 2,315.37µs | 1,859.11µs | 비중첩, 약 19.7% 감소 |
| test-only 테스트 문맥, 128개, 깊이1 | 1,357.08µs | 1,138.40µs | 비중첩 |
| test-only 일반 문맥, 128개, 깊이1 | 750.92µs | 750.86µs | 중첩, 개선 주장 없음 |
| off, 128개, 깊이1 | 761.20µs | 747.36µs | 중첩, 개선 주장 없음 |

대표 boundary/128개/깊이1의 warm 범위는 **1,544.16–1,560.58µs →
1,236.17–1,274.78µs**다. 같은 조건의 전체 cold 중앙값은 **417.87→419.52ms**,
범위는 **414.80–420.73 → 418.00–420.07ms**로 겹친다. 따라서 **cold 개선은 주장하지
않는다**. 준비 이후 첫 호출 자체는 2.951→2.625ms로 기록됐다.

같은 조건의 Python traced peak는 **24,221→24,221 bytes**, retained는 **1,112→1,112**다.
런타임 소스 패키지는 **110,425→110,684 bytes(+259)**다. tracemalloc은 Python의 별도
1회 peak/retained 측정이며 RSS·native 할당·전체 allocation 횟수를 측정하지 않는다.

도구 시간은 runtime과 별도다. 본 행렬 6개 fixture당 한 번씩 기록한 범위는
emit **0.232–0.260s → 0.237–0.262s**, verify **8.179–8.538s → 8.138–8.208s**다.
모드/깊이가 다른 소수 관찰이므로 빌드·검증 성능 개선을 주장하지 않는다.

### 잡음과 한계

본 행렬 test-only 일반 문맥/4개/깊이1에서 **51.42→32.27µs**와 큰 cold 차이가 보였다.
이 분기는 이번 최적화 대상이 아니며 before 표본도 33.21–72.83µs로 넓었다. 그 행을
삭제하거나 최적화 효과라고 발표하지 않고 **after 먼저, before 나중**으로 9회/200회
반복했다. 결과는 **32.059→32.069µs**, 범위 **31.591–32.929 → 31.555–32.475µs**로
같은 수준이었다. 같은 재측정의 테스트 문맥은 **53.409→46.015µs**, 범위 비중첩이다.
`facade-control-*.json`에 원시 결과를 별도로 보존했다.

이것은 작은 identity 알고리즘과 동일 값 표현을 사용하는 순차 비대응 실험이다.
CPU 부하/열 상태를 통제하지 않았고, cold도 OS page cache를 비운 결과가 아니다.
범위 비중첩은 통계적 유의성 검정이 아니다. 실제 verify 성공은 기록된 유한 검사와
provenance의 증거이며 모든 자연어 요구 충족이나 앱 전체 성능·안전성을 증명하지 않는다.

## 재실행 및 검증

```sh
PY="$PWD/target/facade-toolchain-followup/python/cpython-3.14.6-linux-x86_64-gnu/bin/python3.14"
CHECKER="$PWD/target/facade-toolchain-followup/venv/bin/basedpyright"
# 실제 실행은 receipt의 격리 HOME/cache/PATH 환경을 사용했다.
"$PY" benchmarks/python_boundary.py --cott "$PWD/target/boundary-baseline/cott" \
  --type-checker "$CHECKER" --modes boundary test-only off --sizes 4 128 --depths 1 3 \
  --repeat 7 --loops 80 --profile --output /tmp/new-supported-before.json
"$PY" benchmarks/python_boundary.py --cott "$PWD/target/debug/cott" \
  --type-checker "$CHECKER" --modes boundary test-only off --sizes 4 128 --depths 1 3 \
  --repeat 7 --loops 80 --profile --output /tmp/new-supported-after.json
"$PY" benchmarks/compare_python_boundary.py /tmp/new-supported-before.json \
  /tmp/new-supported-after.json --output /tmp/new-supported-comparison.json
```

before 바이너리는 이번 작업 환경의 보존물이다. 없다면 최적화 전 source를 별도 소유
빌드 디렉터리에서 정규 빌드해야 하며, after의 generated 파일을 수정해 before를
만들어서는 안 된다. 실행 스크립트의 exclusive-create 때문에 출력 경로도 새로 정한다.

- 실제 CPython 3.14.6에서 기존 하네스 **9개 회귀 통과**, skip 0.
- 같은 interpreter에서 ABI 정상/거부·오류 phase/clause 등 **61개 관찰 전후 bytes 동일**.
- 결과 감사: 동일 interpreter/하네스/알고리즘/입력, 16개 real verify 성공과 도구 해시,
  current/last_verified 일치, 원본/최적화 runtime bytes, 기존 결과·compiler 코드 보존 확인.
- compiler/harness는 이번에 수정하지 않아 전체 cargo test를 다시 실행하지 않았다.
  직전 **998 통과/0 실패/103 ignored** 증거는 원래 `checks.json`에 그대로 남아 있다.
  이번 좁은 검사·지원 도구 명령은 `toolchain-followup.json`의 `checks`/`audit`를 참고한다.

관련 결과: `facade-supported-{before,after,comparison}.json`,
`facade-control-{before,after,comparison}.json`, `abi-supported-{before,after}.json`.
