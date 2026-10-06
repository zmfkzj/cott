# 이번 실행 결과 — 정수 ABI dispatch 최적화

> 이 문서는 **이전 CPython 3.14.4 컴포넌트 실험**의 결과와 당시 blocker를 보존한다.
> 후속 작업에서 실제 지원 CPython 3.14.6/BasedPyright 1.39.9를 격리 설치하고
> 정규 emit/verify를 통과한 facade 전후 측정을 완료했다. 현재 인수 상태와 별도의
> 수치는 [facade-supported.md](facade-supported.md)를 참고한다. 아래 수치는 재인증하거나 혼합하지 않았다.

## 범위와 인증 상태

- 시작 HEAD: `921158c838150c880c5b2792b02969d922626602`.
- 실제 실행기: `/usr/bin/python3` → `/usr/bin/python3.14`, CPython **3.14.4**,
  GCC 15.2.0, Linux x86_64. 가짜 pinned wrapper를 성능 측정에 사용하지 않았다.
- Cott Python 지원 pin은 **3.14.6+**이다. 이번 수치는 **compiler-rendered runtime
  컴포넌트**의 native 측정이지 지원 버전에서 인증된 facade의 측정이 아니다.
- `facade-attempt.json`: 깊이 1/3 × 3개 모드에서 정상 `emit` 6회 성공.
  실제 `verify` 6회는 BasedPyright 부재로 exit 4. 인증 우회 없이 facade runtime 행은
  **0개**로 남겼다. type checker를 설치해도 CPython pin 문제를 별도로 해결해야 한다.
- 실제 `generate`/유료 모델 호출은 없다. `gpt 6.1 sol`의 사용 가능한 정확한
  Cott adapter/model ID를 확인하지 못했다. 다른 모델로 대체하지 않았다.
  고정 identity 알고리즘을 비교하는 이 측정에는 생성 자체가 필요하지 않다.

## 선택한 병목과 변경

최적화 전 cProfile의 boundary/128개/깊이1/80회 호출에서
`_cott_validate_abi_value`가 41,120회 호출됐다. `get_origin` 41,120회,
`get_args` 61,600회가 관찰됐다. Annotated I32의 정규화 후 exact `int` leaf까지
매번 여러 generic/protocol 분기를 통과하는 경로가 있었다.

변경은 `src/python_runtime.rs::_cott_validate_abi_value`의 **exact int 성공 분기를
typing introspection 앞에 이동**한 것뿐이다. traversal state, 깊이/순환 검사,
Annotated 범위 검사, 실패 memo, 타입 힌트 cache, nominal 재구성, loader·provenance,
contract observer, off F32 정규화는 변경하지 않았다. 새 cache도 없다.
기존 Python runtime ABI 7의 값 의미나 wire shape를 바꾸지 않는다.

## 본 측정

두 runtime 디렉터리를 같은 최종 `python_boundary.py`로 측정했다.
각 조합은 fresh process 7회, warm 반복 80회, sizes 4/128, depths 1/3,
`boundary`, `test-only`의 일반/테스트 문맥, `off`를 분리한다.
서로 다른 코드의 실제 식별자는 행의 `runtime_identity`와 compiler export metadata에 있다.

| direct-checked 컴포넌트 | 전 warm 중앙값 | 후 warm 중앙값 | 해석 |
|---|---:|---:|---|
| boundary, 4개, 깊이1 | 30.31µs | 25.29µs | 관찰 범위 비중첩 |
| boundary, 128개, 깊이1 | 773.24µs | 612.94µs | 약 20.7% 감소, 범위 비중첩 |
| boundary, 128개, 깊이3 | 783.81µs | 633.69µs | 약 19.2% 감소, 범위 비중첩 |
| test-only 테스트 문맥, 128개, 깊이1 | 570.98µs | 491.43µs | 약 13.9% 감소 |
| test-only 일반 문맥, 128개, 깊이1 | 363.01µs | 364.86µs | 범위 중첩, 개선 주장 없음 |
| off, 128개, 깊이1 | 366.72µs | 363.70µs | 범위 중첩, 개선 주장 없음 |

128개/깊이1/boundary의 warm 범위는 **764.97–784.56µs → 608.25–667.78µs**.
같은 행에서 fresh-process 전체 시간은 **112.47 → 114.38ms**로 범위가 겹친다.
따라서 **cold startup 개선은 주장하지 않는다**. 새 프로세스의 첫 호출 자체는
880.38 → 710.59µs였으며, raw cold 세부 관찰도 결과에 보존돼 있다.
여기서 cold는 OS/page cache를 비웠다는 뜻이 아니다.

같은 boundary 행의 traced peak는 **22,937 → 22,937 bytes**다.
런타임 Python 소스 패키지는 **110,425 → 110,684 bytes(+259)**이며, 새 상태/cache
할당은 없다. tracemalloc은 Python 추적 할당의 1회 peak/retained만 관찰하고
RSS·native 할당·전체 allocation churn은 측정하지 않는다.

### 잡음을 숨기지 않은 후속 측정

본 측정의 `test-only` 테스트 문맥/4개/깊이3은 34.73 → 44.83µs로 나빠졌지만
관찰 범위가 겹쳤고 cold도 함께 증가했다. 이를 지우거나 개선으로 해석하지 않았다.
동일 workload를 **after 먼저, before 나중** 순서로 fresh process 15회/300회 warm
반복하여 다시 측정한 결과는 **34.00 → 30.61µs**, 범위 **33.17–34.90 →
30.17–31.54µs**였다. 일반 문맥은 24.07 → 24.08µs로 동일 수준이다.
`noise-followup-*.json`에 두 실행과 비교를 별도로 보존했다.

모든 값은 작은 합성 workload의 순차 비대응 실행이다. host 부하/열 상태가 통제되지
않았으며 범위 비중첩도 통계적 유의성 검정은 아니다. 앱 전체, 지원 pin의 interpreter,
인증된 facade, 다른 언어 타깃, 개발자 생산성으로 확대 해석하면 안 된다.

## 의미 보존

`tests/support/python_abi_cases.py`를 전후 runtime에서 실제 CPython으로 실행했다.
61개 관찰의 JSON bytes가 `cmp`로 완전히 같았다. 정상/거부 값, error message,
phase/clause/symbol/expected/actual, integer bounds/exactness, nested/generic/nominal,
변조 객체 재검사, union 실패, Unicode surrogate, cycle/depth, off F32가 포함된다.
기존 Python emit/runtime 테스트와 새 fast-path traversal 회귀도 함께 실행한다.
`abi-before.json`, `abi-after.json`은 이 실험의 결과이지 verify 인증 증거가 아니다.

## 재실행한 명령

```sh
CARGO_PROFILE_DEV_DEBUG=0 CARGO_INCREMENTAL=0 cargo run -j 2 \
  --example benchmark-runtime -- /tmp/cott-boundary-original-native
# 위 export는 runtime 변경 전에 실행. 변경 뒤 별도 디렉터리에 export:
CARGO_PROFILE_DEV_DEBUG=0 CARGO_INCREMENTAL=0 cargo run -j 2 \
  --example benchmark-runtime -- /tmp/cott-boundary-candidate-native
python3 benchmarks/python_boundary.py --component-runtime /tmp/cott-boundary-original-native \
  --output benchmarks/results/boundary-before.json --label original-integer-dispatch \
  --profile --modes boundary test-only off --repeat 7 --loops 80
python3 benchmarks/python_boundary.py --component-runtime /tmp/cott-boundary-candidate-native \
  --output benchmarks/results/boundary-after.json --label early-exact-int-dispatch \
  --profile --modes boundary test-only off --repeat 7 --loops 80
python3 benchmarks/compare_python_boundary.py benchmarks/results/boundary-before.json \
  benchmarks/results/boundary-after.json --output benchmarks/results/boundary-comparison.json
python3 tests/support/python_abi_cases.py /tmp/cott-boundary-original-native > /tmp/abi-before.json
python3 tests/support/python_abi_cases.py /tmp/cott-boundary-candidate-native > /tmp/abi-after.json
cmp /tmp/abi-before.json /tmp/abi-after.json
```

이미 있는 결과를 덮어쓰지 않으므로 재실행은 새로운 output path를 사용한다.
과거 저장소의 `contract-value-results.json` / `ai-generation-results.json`은 수정하지 않았고
이번 전후 비교의 기준선으로 사용하지 않았다.
