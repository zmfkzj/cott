# `ready_ordered_by`의 authored 계약/회귀 fixture

실제 출발 요구는 `examples/complex/artifact-pipeline/src/curriculum/artifact_pipeline.cott`의
`READY_STEPS_IN_NAME_ORDER`다. 기존 `permutation_by`와 `dependency_ordered_by`만으로는
여러 ready node 중 누구를 먼저 선택할지 정해지지 않는다. 새 predicate는 현재 ready
집합에서 Unicode scalar 사전순 최소 이름을 고르는 **전체** 순서를 검사한다.

```cott
struct BuildStep:
    name: Str
    needs: Set[Str]

fn accept_order(order: List[Str], steps: List[BuildStep]) -> Bool:
    ensures result == ready_ordered_by(order, steps, BuildStep.name, BuildStep.needs)
```

위는 검증 의무이며 함수 본문/위상정렬 구현을 제공하지 않는다. 사용자가 실제 정렬을
반환하는 Result 함수라면 `ensures Result.Ok(order) => ready_ordered_by(...)`를 쓰고,
잘못된 graph의 오류 분류는 기존 `error` 절로 유지하면 된다. 기존 예제의 accepted
agent bytes나 generation record를 이 fixture로 대체하지 않았다.

## 닫힌 signature와 total 의미

- `order: List[Str]`, `steps: List[T]`, exact nominal `T`의 `Str` key field,
  `List[Str]` 또는 `Set[Str]` dependency field. alias는 기존 HIR 규칙을 따르고 newtype
  carrier·foreign owner·잘못된 dependency type·임의 callback을 받지 않는다.
- unique key의 graph에서만 참이 될 수 있다. empty/empty는 참.
- 중복 key, 미지 dependency, self edge, cycle, 빠진/중복/외부 order key는 거짓.
  중복 dependency edge는 하나로 취급한다. partial prefix를 전체 성공으로 인정하지 않는다.
- 비교는 case folding/normalization 없는 Unicode scalar 사전순이다. 빈 key나 공백 key는
  여기서 유효한 Str다. 이름 유효성 정책은 `any_blank_by` 등 별도 계약으로 표현한다.
- `b → a`, 독립 `z`이면 `b,a,z`가 맞고 `a,b,z`(global sort)와 `b,z,a`는 틀리다.
- 입력 node의 배열 순서가 바뀌어도 결과는 같다. 임의 함수 호출·무한 한정자·반복문을
  계약 언어에 추가하지 않는다. 정적 proof는 지원하지 않는 graph reasoning을 `unknown`으로 남긴다.

## 공유 corpus와 실제 관찰

`ready_ordered.json`에는 expected bool을 수동 명시한 23개 case가 있다. empty/single,
parallel ready, 매 단계 ready 집합 변화, diamond, 입력 재배열, 잘못된 tie-break,
중복 key/edge/output, missing dependency/output, cycle, 비BMP와 결합문자/prefix를 포함한다.
U+E000은 U+10000보다 먼저 와야 한다. Kotlin/Dart 기본 UTF-16 sort와 다른 case이므로
기존 canonical code-point comparator를 호출하는 구현을 실제 네이티브에서 확인한다.

`tests/ready_ordered.rs`는 이 **동일 corpus**를 List 및 Set dependency 두 형태로 바꿔
타깃마다 46개 scenario를 작성한다. Set literal은 중복 원소를 허용하지 않으므로 반복 edge
case를 Set으로 표현할 때만 동일 dependency를 한 번 적는다. graph 의미/expected는 같다.

fixture의 `decide_list`/`decide_set`는 expected bool을 그대로 반환하는 **독립 authored
binding**이다. requires에서 expected가 predicate 결과와 같음을 검사하고 ensures에서도
실제 반환값을 다시 predicate와 비교한다. 올바른 fixture는 실제 compiler emit/verify를
통과해야 하고 반환값을 뒤집은 binding은 실패해야 한다. 이는 predicate와 facade/runner
관찰 경로를 검사하는 회귀이지 생성 AI의 알고리즘 품질 벤치마크가 아니다.

타깃별 실제 clause `requires:0`/`ensures:1`의 evidence를 확인한다. Python의
`test observation`과 Kotlin/Dart/Rust의 `passed/positive_applicable`을 혼합하지 않는다.
각 scenario의 두 assertion도 실행돼야 한다. 단지 scenario가 성공했다는 이유로 실행하지
않은 clause를 증거로 채우지 않는다. 실패한 재검증은 current를 unverified로 유지하고
last_verified를 바꾸지 않는다. requirement link의 `observed`는 유한 관찰이지 자연어 전체
증명이 아니다.

## 실행

```sh
# 아래 변수들은 실제 설치된 지원 도구의 절대 경로만 사용한다.
COTT_CARGO=/usr/bin/cargo COTT_RUSTC=/usr/bin/rustc \
COTT_PYTHON=/path/to/python3.14.6 COTT_BASEDPYRIGHT=/path/to/basedpyright \
COTT_KOTLIN_HOME=/path/to/kotlinc JAVA_HOME=/path/to/jdk17 \
COTT_DART=/path/to/dart-sdk/bin/dart \
  cargo test --test ready_ordered -- --include-ignored --test-threads=1
```

도구 없이 실행되는 기본 회귀는 parser/formatter/HIR/closed IR/정적 unknown과 직접 Rust
runtime corpus 및 10,000-node chain 종료를 확인한다. native 항목은 위 명령처럼 명시적으로
실행하지 않으면 ignored이며, ignored를 native 통과라고 집계하지 않는다.
이번 tool versions/실제 명령/결과는 `benchmarks/results/rust-graph-checks.json` 참조.
