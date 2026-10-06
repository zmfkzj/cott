# Python 경계 성능 측정

`python_boundary.py`는 기존 historical `contract-value-results.json` / AI 생성 결과와
별개의 측정 프로토콜이다. 성능 점수는 인증 증거가 아니며, 실패한 verify 뒤 facade를
실행하거나 기록을 고쳐 성공시키지 않는다. 기본 실행에는 모델 호출이 없다.

## 정상 emit / verify / facade 측정

실제 CPython `>=3.14.6,<3.15`로 스크립트를 실행하고 실제 BasedPyright `>=1.39.9`를
지정한다. 가짜 버전 응답 wrapper를 사용하지 않는다. 임시 프로젝트의 `.tools`는 이
실제 executable에 연결할 뿐이며, compiler의 기존 검사·sandbox를 그대로 거친다.

후속 인수 검증에서 전역 환경을 바꾸지 않고 실제 **CPython 3.14.6 / BasedPyright 1.39.9**를
작업 소유 `target/facade-toolchain-followup/`에 준비해 before/after 정상 facade 측정을 완료했다.
설치 출처·격리 환경·명령과 실제 수치는 [지원 도구의 facade 결과](results/facade-supported.md),
원시 실행 영수증은 [toolchain-followup.json](results/toolchain-followup.json)에 있다.
이후 같은 하네스로 재실행할 때도 지원 interpreter로 스크립트를 직접 실행하고,
`--type-checker`에 해당 격리 환경의 실제 실행 파일을 지정한다. 기존 CPython 3.14.4의
컴포넌트 수치와 실패 기록은 별개 이력이며 인증된 결과로 재표기하지 않는다.

```sh
cargo build
/path/to/python3.14 benchmarks/python_boundary.py \
  --cott "$PWD/target/debug/cott" --type-checker /path/to/basedpyright \
  --output /tmp/boundary-current.json
```

- 입력은 고유한 I32 원소를 가진 `List[...]`이며, 기본 크기 4/128, 깊이 1/3이다.
  깊이가 늘어도 원소 수를 지수적으로 늘리지 않는다.
- 새 **authored manifest binding**을 가진 합성 측정 fixture만 만든다. 기존 agent 구현을
  binding으로 대체하지 않고, 예제나 accepted agent bytes를 수정하지 않는다.
- 세 경로 모두 같은 interpreter, 값 표현, 입력과 동일한 identity 알고리즘을 사용한다.
  두 직접 호출 경로는 프로젝트의 **동일한 binding 소스 파일**을 평가용으로 읽는다.
  이는 일반 Cott 소비자에게 private import를 허용한다는 뜻이 아니다.
- `direct-unchecked`: 알고리즘만 실행. 음성 입력 거부를 보장하지 않는다.
- `direct-checked`: Cott와 같은 ABI validator/normalizer 및 두 계약 조건을 실행한다.
  구현 로딩 인증·provenance·observer 증거는 없다. 독립 구현한 validator의 성능 비교도 아니다.
- `facade`: 실제 emit, 명시적 verify 성공, 현재 인증 상태 확인 후 public facade를 호출한다.
  인증 로더를 대체하거나 private callable로 바꿔 측정하지 않는다.

```sh
/path/to/python3.14 benchmarks/python_boundary.py \
  --cott "$PWD/target/debug/cott" --type-checker /path/to/basedpyright \
  --modes boundary test-only off --sizes 4 128 4096 --depths 1 3 \
  --repeat 7 --loops 80 --profile --output /tmp/boundary-expanded.json
```

`test-only`는 일반 문맥/테스트 문맥을 별도 행으로 측정한다. 현행 wrapper는 입력에는
F32 정규화를 적용하고, 테스트 문맥에서는 계약 조건과 반환값 validation을 켠다.
측정용 context toggle은 실제 contract runner의 관찰 증거를 만들지 않는다.
`off`도 F32 정규화와 정상 facade 로딩 비용을 유지한다.

### 기록과 해석

- cold: 매번 **별도 새 프로세스**에서 import/입력 생성/첫 호출만 실행한 전체 시간.
  준비 시간과 첫 호출 시간도 기록한다. 다른 warm 프로세스의 루프·profile·메모리 측정을
  cold에 섞지 않는다. cold는 filesystem/OS page cache를 비운 결과가 아니다.
- warm: 별도 프로세스에서 3회 준비 호출 후 반복 호출. 정확성 확인, cProfile,
  tracemalloc은 시간 측정 밖에서 수행한다. raw sample, 중앙값, min/max, 표준편차를 남긴다.
- 메모리: 별도 1회 호출의 `tracemalloc` peak/retained bytes. Python이 추적하는 할당만
  포함하며 RSS, native 할당, 총 할당 횟수/누적 churn은 **측정하지 않는다**.
- `tool_costs`: fixture마다 emit/verify의 실제 argv, 종료 코드, walltime을 따로 기록한다.
  runtime 반복 수와 달리 각 도구 단계는 fixture당 한 번이다. 실패 시간은 성공 시간으로
  평균내지 않는다. generate는 `not-run`, model은 null이며 개발자 생산성을 추정하지 않는다.
- interpreter 실제 버전/바이너리 해시, host, 스크립트·입력·fixture 소스 해시,
  compiler/target tools, 실행 설정, runtime 소스 크기를 남긴다. 환경 변수나 인증정보는
  결과에 덤프하지 않는다. 출력은 exclusive create로 과거 결과를 덮어쓰지 않는다.
- 입력/모드/타깃이 다른 결과를 합쳐 일반적인 성능 배율로 제시하지 않는다.
  현재 하네스의 타깃은 Python뿐이다.

## 인증과 분리된 컴포넌트 실험

지원 도구가 없는 환경에서도 **renderer가 만든 ABI checker만** 검사할 수 있다.
이것은 정상 facade 측정의 자동 fallback이 아니며 명시적인 별도 실행이다.

성능 패치 **전**에 baseline runtime을 compiler-linked fixture exporter로 보존하고,
패치 뒤 다른 새 디렉터리에 다시 export한다. 기존 runtime을 수동 수정하지 않는다.

```sh
cargo run --example benchmark-runtime -- /tmp/runtime-before
# compiler/runtime 성능 변경 및 회귀 검증 후:
cargo run --example benchmark-runtime -- /tmp/runtime-after
python3 benchmarks/python_boundary.py --component-runtime /tmp/runtime-before \
  --modes boundary test-only off --repeat 7 --loops 80 --profile \
  --output /tmp/before.json
python3 benchmarks/python_boundary.py --component-runtime /tmp/runtime-after \
  --modes boundary test-only off --repeat 7 --loops 80 --profile \
  --output /tmp/after.json
python3 benchmarks/compare_python_boundary.py /tmp/before.json /tmp/after.json \
  --output /tmp/comparison.json
```

두 측정에는 **같은 최종 하네스**를 사용한다. 각 행의 runtime bytes 및
`compiler_export.runtime_source_sha256`가 실제 측정 코드를 식별한다. 결과 생성 당시의
`workspace_sources_at_measurement`와 오래된 compiled baseline은 다를 수 있다.
export metadata는 재현 식별 정보일 뿐 Cott generation provenance가 아니다.
비교기는 interpreter/host, 하네스, 입력·검사 수준·scope 불일치를 거부한다.
범위 중첩은 그대로 표시하고 비중첩도 통계적 유의성 검정으로 부르지 않는다.

## 생성 측정은 명시적 모델 선택으로만

기존 `ai_generation.py`의 구 모델 기본값을 제거했다. provider/model ID와 thinking을
필수 입력으로 받고, Cott generate와 직접 OMP 호출 모두 `--model`을 전달한다.
별도 복제한 상태의 `retry.modelFallback=false`를 유지하고, direct usage의 실제 모델이
요청 ID와 다르면 실패로 남긴다. AgentRun/provenance를 재작성하지 않는다.

```sh
# 먼저 설치된 provider/CLI에서 사용자 지정 모델의 정확한 ID/접근 가능성을 확인한다.
# 확인하지 못했다면 이 명령을 실행하지 않는다. 환경 변수는 확인된 ID만 넣는다.
python3 benchmarks/ai_generation.py --cott "$PWD/target/debug/cott" \
  --model "$CONFIRMED_PROVIDER_MODEL_ID" --thinking high \
  --repeat 1 --jobs 1 --output /tmp/generation-explicit-model.json
```

이번 작업에서는 사용자가 지정한 `gpt 6.1 sol`의 확인 가능한 ID/접근 가능한 Cott
adapter를 찾지 못했다. `codex`, `claude`, `omp`가 PATH에 없었고, 설치된 Pi의 offline
모델 목록도 비어 있었다. 모델명을 추측하거나 다른 모델을 호출하지 않았으며,
고정 알고리즘 성능 실험에는 유료 생성이 필요하지 않아 **실제 generate는 미실행**이다.
테스트 안의 mock provider 실행은 이와 별개의 프로토콜 회귀이며 모델 사용 실적이 아니다.

## 회귀 검사

```sh
cargo fmt --check
cargo test
cargo test --test python_emit --test python_runtime --test python_benchmark
cargo test --test lsp_protocol
python3 -m unittest discover -s benchmarks -p 'test_*.py' -v
# Rust python_benchmark 테스트가 runtime과 compiler를 공급해 통합 항목도 실행한다.
# 직접 unittest 실행 시 COTT_BENCH_RUNTIME/COTT_BENCH_COTT가 없으면 해당 항목을 skip한다.
python3 tests/support/python_abi_cases.py /tmp/runtime-before > /tmp/abi-before.json
python3 tests/support/python_abi_cases.py /tmp/runtime-after > /tmp/abi-after.json
cmp /tmp/abi-before.json /tmp/abi-after.json
```

`test_emitted_predicates_match_direct_checker_without_claiming_provenance`는 정상 emit한
wrapper의 **값/계약 의미만** 비교하는 단위 회귀다. 이 테스트에서만 in-memory loader를
stub으로 교체하며, 측정 함수 호출·인증 성공 기록은 하지 않는다. 실제 측정 하네스는
그 경로를 사용하지 않고 반드시 원래 loader와 real verify를 거친다.


이전 컴포넌트 측정·한계는 [results/README.md](results/README.md),
완료된 지원 도구의 인증 facade 측정은 [results/facade-supported.md](results/facade-supported.md)를 참고한다.

Rust 컬렉션 후속 측정은 별도 [RUST_COLLECTIONS.md](RUST_COLLECTIONS.md)와
`results/rust-collections-*.json`에 있다. Python 결과와 타깃/워크로드를 섞지 않는다.
