# cott 기본 설계 문서

**문서 상태:** Implemented v1.0
**프로젝트명:** cott
**파일 확장자:** `.cott`
**CLI 명령:** `cott`


## 1.0 릴리스 호환성

이 문서는 구현된 v1.0 언어와 Python, Kotlin/JVM, Dart backend를 규정한다. package version은
`1.0.0`이다. Python은 CPython `>=3.14.6,<3.15`, BasedPyright `>=1.39.9`, uv
`>=0.12.3`를 사용한다. Kotlin은 kotlinc-jvm `>=2.2.10`, JDK `>=17`, 고정 JVM target
`17`, compiler distribution과 일치하는 Kotlin stdlib 및
`kotlinx-coroutines-core-jvm` `1.8.0`을 사용한다. Codex CLI `>=0.147.0`, Claude Code CLI
`>=2.1.89`, OMP `>=17.2.12`를 지원한다. 각 실제 tool/runtime dependency의 full version과
content hash는 target provenance에 기록한다.
Dart target은 SDK `>=3.13.3,<4.0.0`을 사용하고 portable package를 Flutter가 직접 소비한다.
Dart runtime 검증 host에는 Linux bubblewrap과 Landlock ABI `>=3`이 필요하다.

Canonical IR schema는 세 backend 모두 **v8**이고 diagnostics schema는 **v1**이다. Python의
닫힌 compatibility identity는 generation schema/domain **v7**/`cott.generation.v7`, runtime
ABI **7**, contract-test strategy schema **v5**로 그대로 유지한다. Kotlin은 별도의 닫힌
generation schema **v1**, domain `cott.kotlin.generation.v1`, runtime ABI **1**을 사용하며
Python의 `public_python_symbols`·`python_symbol` 같은 field를 재사용하지 않는다. 각 reader와
runtime은 다른 backend 또는 다른 version의 record를 거부한다. `[project].version`은 compiler
version이 아니라 공개 API version이고 예제 project는 `0.1.0`을 유지한다.
Dart는 독립 generation schema **v1**, domain `cott.dart.generation.v1`, runtime ABI **1**을
사용하며 Python/Kotlin record나 target-specific field를 재사용하지 않는다.

구현된 v0.8 `.cott` source는 v1.0에서도 의미를 바꾸지 않고 유효하다. source compatibility는
serialized artifact compatibility가 아니다. 생성 target의 public ABI는 facade signature,
canonical constructor, nominal/runtime type identity와 validation behavior의 합이다. incompatible
ABI change는 해당 target ABI bump가 필요하다. package 또는 target identity가 다르면 artifact는
stale이며 `emit` 또는 `generate`로 재생성해야 하고 `verify`와 runtime은 이를 fail closed한다.
호환되지 않는 wire record용 legacy reader나 변환 경로는 없다.

`emit python`, `emit kotlin`, `verify`는 agent를 호출하지 않는다. `cott prompt`는 provider나
target compiler/checker 없이 초기 generation prompt만 렌더하고 publication과 journal recovery를
하지 않는다. Agent 호출은 `generate`에서만 조건부로 수행한다. 기존 project command의
`--project <dir>`은 subcommand 뒤 어느 위치에서나 한 번만 허용하며 기본은 현재 directory다.
`init`은 target path를 받고 `--project`를 거부한다. 이 문서와 implementation이 충돌하면
repository source와 closed schema validator가 authority이며 문서를 구현에 맞게 고친다.
---

## 1. 개요

cott는 함수, 데이터 구조, 오류, 제약 조건을 정밀하게 선언하고 그 typed intent에서 generation prompt를 렌더하거나 기존 구현을 안전하게 연결하는 **language-like typed intent/prompt authoring DSL**이다.

cott 자체는 범용 프로그래밍 언어가 아니다. 반복문, 분기문, 네트워크 호출, 파일 입출력 같은 실제 구현 기능을 제공하지 않는다.

cott의 역할은 다음 세 가지로 제한한다.

1. 프로그램의 구조와 타입을 선언한다.
2. 구현이 지켜야 할 계약과 typed intent를 선언한다.
3. scoped prompt를 렌더하고, 생성되거나 binding된 코드가 선언된 계약과 일치하는지 검증한다.

각 project manifest는 Python, Kotlin, Dart 중 정확히 하나를 선택하고 `cott init`의 default는
Python이다. Cott의 우선순위는 선언을 고정하고, scoped generation prompt와 intent fingerprint를
렌더·기록하며, 그 선언을 선택 target ABI로 결정적으로 투영하고, 구현 conformance·artifact
identity·실제로 확보한 evidence만 검사·기록하는 것이다. 선언은 intent의 완전한 형식화가 아니고,
통과한 검증은 구현 전반의 정확성 증명이 아니다. Implementation selection과 runtime observation은
이 순서를 바꾸거나 declaration 의미를 대체하지 않는다. runtime은 authored `.cott`를 live로 읽지
않는다. 이미 배포된 snapshot은 `emit` 또는 `generate` 전까지 옛 계약을 유지한다. 제품은 속도
주장이 아니다.

`doc`는 실행 계약이 아니다. `doc`만 바뀐 contract diff는 `DOCUMENTATION`이며 이 label은 regeneration 요구와 별개다. `doc`·적용된 rule과 그 base·계약 상수·참조 type·incoming scenario·retained generator rule 식별자 변경은 intent fingerprint를 바꾸고 agent-owned source를 stale로 표시할 수 있다. 관찰된 clause가 요구사항 완전성을 증명하지 않는다. `verified`는 해당 snapshot의 artifact/type/runtime/proof/runner 인증이며, 모든 semantic clause 관찰이나 coverage policy 통과를 뜻하지 않는다. coverage gate는 선택한 rule이 있을 때만 동작한다. 외부 effect와 일부 boundary는 trust declaration이다. proof와 sampling은 bounded다. unsupported formula 또는 proof budget exhaustion은 `unknown`이고, 실행 관찰이 없으면 capability에 따라 `미관찰` 또는 신뢰 선언이며, 어느 쪽도 성공으로 위장하지 않는다.

같은 작업의 유효한 baseline은 typed Python과 독립 테스트다. Cott 비용은 안정적인 public facade와 provenance/evidence 경계가 필요할 때 정당화된다. 일차 비교는 같은 AI model이 Cott를 통해 생성한 구현과 Python을 직접 생성한 구현이다. 사람 작성/검토 비용은 그 비교가 아니며 합성하지 않는다. `benchmarks/contract_value.py`는 이미 생성된 artifact의 mutation·runtime 비용 실험이며 generation/productivity 증거가 아니다. 실제 AI generation 비교는 `benchmarks/ai_generation.py`다. 두 arm은 같은 artifact-pipeline 작업과 숨겨진 독립 3130-case corpus, 깨끗한 구현, 고정 model/config를 쓰고, 각 trial은 Cott `generate` 한 번(native per-callable retry 포함)과 direct generation 한 번이며 jobs는 최대 3이다. generation wall time과 verify/acceptance는 분리한다. Cott native provenance는 duration과 stream digest만 있고 token usage는 없으며 추론하지 않는다. 이 비교는 한 작업의 3 pair이며, 같은 model/toolset을 쓰고, direct는 trial당 한 invocation, Cott는 native per-callable retry다. 저장소의 독립 acceptance script는 `cott verify`의 일부가 아니며 canonical evidence source가 아니다.

기록된 trial 숫자는 그 run의 compiler hash에 묶인 역사적 artifact이며 현재 prompt renderer의 성능 주장이 아니다.

```text
.cott 계약 (typed intent)
    ↓
파싱 및 타입 검사
    ↓
정규화된 Canonical IR 생성
    ↓
intent fingerprint와 scoped target prompt 렌더
    ↓
선택한 Python, Kotlin 또는 Dart target projection과 기존 구현 binding 해석
    ↓
미구현 callable이 있으면 사용자가 지정한 agent 호출
    ↓
target public facade/runtime 생성
    ↓
정적 target 검사, sandboxed runtime observation과 계약 검증
```

---

## 2. 목표

### 2.1 핵심 목표

cott는 다음 문제를 해결한다.

* 자연어만으로 AI에게 구조를 설명할 때 발생하는 모호성
* Python 타입 힌트의 선택적이고 느슨한 사용
* 생성된 코드가 최초 설계와 점점 달라지는 문제
* 함수의 실패 조건과 부작용이 코드 밖에 존재하는 문제
* AI가 코드 구조를 임의로 변경하는 문제
* 타입 설명을 반복해서 자연어로 작성해야 하는 문제

### 2.2 최종 사용 경험

사용자는 다음과 같은 선언을 작성한다.

```cott
fn process_bar(
    data: InputPayload,
    threshold: Probability,
) -> Result[OutputPayload, BarError]:
    doc """
    foo 입력을 bar 규칙으로 처리하고 원본 선언 크기와 형식을 기록한 출력을 반환한다.
    """

    ensures Result.Ok(output) => output.source_size == data.declared_size
    ensures Result.Ok(output) => output.format == data.format

    error BarError.InvalidPayload when data.data.len == 0
    error BarError.ServiceUnavailable

    effects [network]
```

AI는 이를 참고하여 Python 구현을 생성한다.

```python
def process_bar(
    data: InputPayload,
    threshold: Probability,
) -> Result[OutputPayload, BarError]:
    ...
```

위 `...`는 문서에서 body를 생략한 표기일 뿐이다. 실제 implementation의 `pass`, `...` 또는 `NotImplementedError` placeholder는 허용하지 않는다.

구현이 다음과 같이 계약을 위반하면 cott 검증 과정에서 실패해야 한다.

```python
def process_bar(data: InputPayload, threshold: float) -> OutputPayload:
    ...
```

위 구현은 다음 이유로 잘못되었다.

* `Probability` 타입이 `float`로 약화되었다.
* `Result` 오류 모델이 제거되었다.
* 실패 가능성이 함수 시그니처에서 사라졌다.

---

## 3. 설계 원칙

### 3.1 계약이 구현보다 우선한다

`.cott` 파일이 프로그램의 공개 구조와 계약의 원본이다.

Python, Kotlin, Dart 구현은 agent가 생성하거나 existing project function에 명시적으로 binding할
수 있다. 선언된 external type은 semantic Cott identity이고 선택 backend의
`target.<language>.external_types` projection으로 해석한다.
API 계약이 다를 때만 project-local typed adapter가 이를 맞춘다. test code, 문서와 agent 구현
지시는 모두 Cott 선언과 Canonical IR에서 파생된다.

생성되거나 binding된 target 구현이 Cott 선언과 충돌하면 target 구현이 잘못된 것으로 판단한다.

### 3.2 명시적 타입만 허용한다

함수 인자, 반환값, 구조체 필드는 반드시 타입을 가져야 한다.

다음과 같은 암묵적 타입은 허용하지 않는다.

```cott
fn load(path):
```

반드시 다음과 같이 작성한다.

```cott
fn load(path: Path) -> Result[Bytes, LoadError]:
```

### 3.3 `Any`와 `Unknown`은 명시적 타입이다

`Any`와 `Unknown`은 prelude에 포함되는 명시적 타입이며 누락된 annotation이나 추론 실패의 대체가 아니다.

```cott
struct ParsedEnvelope:
    payload: Any
    source: Unknown
```

`Any`는 의도적으로 제약하지 않는 값을, `Unknown`은 명시적 narrowing 또는 target-side adaptation 전에는 연산할 수 없는 값을 뜻한다. 두 타입의 사용은 계약과 evidence에 보존되며 compiler가 침묵하여 다른 타입으로 바꾸지 않는다. `Dynamic`과 `Object`는 source type이 아니다.

동적 데이터의 구조를 모델링할 수 있으면 여전히 명시적인 `JsonValue` 또는 `Opaque["external-library-object"]`를 사용한다. `Opaque`는 foreign-object identity를 나타내며 명시적 경계에만 제한되지 않는다.

### 3.4 암묵적 변환을 금지한다

다음 변환은 자동으로 수행되지 않는다.

* `Str` → `I32`
* `I32` → `F32`
* `Option[T]` → `T`
* `Child` → `Parent`
* 구조가 같은 서로 다른 명목 타입 간 변환

변환은 명시적인 함수를 통해서만 수행한다.

```cott
fn parse_i32(value: Str) -> Result[I32, ParseError]
fn to_f32(value: I32) -> F32
```

### 3.5 실패 가능성을 타입에 포함한다

정상적인 실패는 예외가 아니라 `Result`로 표현한다.

```cott
fn load_config(path: Path) -> Result[Config, ConfigLoadError]
```

값이 없을 수 있는 경우는 `Option`으로 표현한다.

```cott
fn find_user(id: UserId) -> Option[User]
```

`null`, `None`, 암묵적 예외는 cott 공개 인터페이스에서 허용하지 않는다.

### 3.6 익숙한 문법과 Python 호환성을 구분한다

cott 문법은 Python처럼 읽기 쉽고 들여쓰기를 사용한다.

그러나 cott 파일은 유효한 Python 코드일 필요가 없다.

Python 문법과 완전히 호환되도록 만들면 Python의 다음 문제까지 상속하게 된다.

* 타입 힌트가 실행 의미와 분리됨
* 선언과 실행 코드가 혼합됨
* `None`과 예외가 암묵적으로 침투함
* 동적 표현식을 어디까지 허용할지 경계가 흐려짐

따라서 cott는 **Python과 유사한 독립 문법**을 사용한다.

---

## 4. 비목표

v1.0에서도 다음 기능은 구현하지 않는다.

* 범용 코드 실행, 반복문, 일반적인 조건문
* 클래스 상속, 메타프로그래밍, 매크로, 런타임 리플렉션, 임의 Python 코드 삽입
* Rust ownership, borrow checker, lifetime
* `.cott` execution body, parameter default, generic overload
* Cott 밖 target call graph/effect inference, mutable Cott container state, arbitrary `old()`
* automatic refactoring/adapter/exception conversion
* 한 project에서 여러 target을 동시에 선택하는 manifest, 지원하지 않는 partial backend,
  Cott-owned Android/Flutter app·UI·Manifest·resource·APK/AAB·signing lifecycle, full IDE
  plugin, multi-project Python environment, external struct/enum direct binding
* dependency resolver/package manager, live reader transaction snapshot isolation, installed wheel whole-origin verification
* SMT 또는 무제한 정리 증명

async impl method, async protocol lifecycle, trait inheritance·specialization·variance·`Dyn`, guarded recursive nominal type, struct cross-field invariant, finite scenario와 compiler-owned fixture는 v1.0의 구현 범위다. `AsyncIterator`·`AsyncGenerator`는 native async-generator implementation 함수가 아니라 반환 protocol이다. `boundary`와 contract-test context의 wrapper는 각 async protocol operation을 runtime에서 강제하고, contract test는 configured lifecycle limit 안의 실제 관찰만 evidence로 남긴다.
## 5. 기본 문법

### 5.1 모듈

모든 cott 파일은 하나의 모듈을 선언한다.

```cott
module system.process
```

다른 모듈의 공개 type과 constant는 `use`로 가져온다.

```cott
use system.data.{InputPayload, OutputPayload}
```

전체 이름을 직접 사용할 수도 있다.

```cott
fn process(data: system.data.InputPayload) -> system.data.OutputPayload
```

`Bool`·고정 폭 숫자·`Str`·`Bytes`·`Path`·`Unit`·`Never`·`Any`·`Unknown`, container constructor, `Option`, `Result`, `Iterator`, `Generator`, `Factory`, `JsonValue`와 `Opaque`는 compiler prelude 이름으로 항상 scope에 있다. canonical identity는 `core.*`이며 project source가 `core.*` module이나 같은 prelude 이름을 선언할 수 없다. Python에서는 16.1의 `cott_runtime`이 유일한 runtime identity를 제공한다.

순환 module dependency는 금지한다. dependency graph는 `use`뿐 아니라 type, constant, contract와 enum variant의 모든 fully qualified reference를 포함한다.

Python target은 top-level `cott_runtime`·`_cott_impl`과 마지막 segment가 `_types`로 끝나는 cott module 이름을 예약한다. public cott top-level package나 compiler-owned `cott_runtime`·`_cott_impl`이 CPython 3.14 standard-library module 또는 lock artifact가 제공하는 top-level package와 충돌하면 거부한다. 모든 facade, type module, local implementation copy와 support package의 target path는 injective해야 하며 충돌은 emit 전 hard error다.

source file 경로는 module path와 정확히 대응하며 module qname은 `py.typed`를 담는 top-level package 아래에 놓이도록 최소 두 segment여야 한다. `module system.process`는 `<project.source>/system/process.cott`에만 올 수 있고 단일-segment module은 거부한다. 중복 module과 한 module path가 다른 path의 strict prefix가 되는 구성은 Python file/package 충돌이므로 거부한다.

`use`는 module 직후의 하나의 contiguous block에만 올 수 있고 source order를 보존한다. 단일 qname은 공개 type 또는 constant, grouped form의 prefix는 module이어야 한다. alias와 re-export는 MVP에 없다. 같은 canonical symbol 중복, 같은 short name을 둘 이상 import하거나 local declaration과 충돌하면 ambiguity error며 fully qualified name을 사용해야 한다. 모든 top-level cott declaration은 공개이고 module 안에서 이름이 유일하다.

---

### 5.2 주석

한 줄 주석은 `#`을 사용한다.

```cott
# 입력 데이터 타입
struct InputPayload:
    data: Bytes
```

문서 설명은 `doc` 블록을 사용한다.

```cott
doc """
입력 데이터와 메타데이터를 표현한다.
"""
```

`doc`은 단순 주석이 아니다. AI 구현 지시와 문서 생성에 포함되는 정식 메타데이터다.

다만 `doc`의 자연어는 implementation conformance를 판정하는 executable contract가 아니다. 보증 등급은 type·`requires`·`ensures`·`error`·`effects`에만 부여하며 `doc`만 바뀐 경우 diff는 `DOCUMENTATION`이다. 이 label은 regeneration 요구와 별개다. `doc` 변경은 해당 callable의 intent fingerprint를 갱신하고 agent-owned 구현을 stale로 큐에 넣을 수 있다.

triple string은 opening delimiter 뒤와 closing delimiter 앞에 newline을 필수로 두고 closing delimiter는 `doc`과 같은 indentation에 둔다. parser는 앞뒤 newline 하나를 제거하고 각 content line에서 그 indentation만 dedent한 LF text를 metadata로 저장한다. nonblank line이 그보다 적게 indent되면 오류이며 formatter는 decoded content를 바꾸지 않는다.

---

### 5.3 원시 타입

MVP는 다음 원시 타입을 제공한다.

```text
Bool

I8
I16
I32
I64

U8
U16
U32
U64

F32
F64

Str
Bytes
Path
Unit
Never
Any
Unknown
```

크기가 불분명한 `int`, `float` 타입은 제공하지 않는다. `Path`는 파일 시스템 경로 값이며 경로의 존재 여부처럼 외부 상태를 읽는 동작은 값의 속성이 아니라 `effects [file.read]`가 있는 함수로 표현한다.

`()`는 `Unit`의 유일한 source value literal이다. `Never`에는 value가 없다.

계약 표현식의 정수 산술은 overflow 없는 mathematical integer로 평가한다. 정수 type의 sign과 bit width는 값 생성과 runtime validation이 활성화된 public boundary에서 range로 검사하며 Python ABI compatibility에서도 별도 metadata로 비교한다.

numeric literal은 선언 type이나 typed operand에서 문맥 type을 얻어야 하며 문맥 없는 literal끼리의 연산은 오류다. unary sign까지 평가한 뒤 integer range를 검사한다.

`F32` 값과 문맥상 `F32`인 literal은 생성·statically concrete public boundary에서 IEEE 754 binary32로 반올림한 뒤 저장하고 구현에 전달한다. 이 ABI normalization은 `runtime_validation = "off"`에서도 유지한다. erased `TypeVar` 뒤의 숫자 관계는 정적으로만 검사한다. `F64`는 Python binary64 `float`를 그대로 사용한다.

`Str`은 Unicode scalar sequence이며 활성 runtime validation은 surrogate code point를 거부한다. `Str.len`은 scalar 개수, `Bytes.len`은 byte 개수, 컨테이너의 `.len`은 원소 또는 map 항목 개수이며 모든 `.len` expression의 cott type은 `U64`다. `off`에서 외부 `str`의 scalar 유효성은 trust declaration이다.

`JsonValue`와 `Opaque["tag"]`는 12.5의 명시적 경계 타입이며 일반 원시 타입의 암묵적 대체재가 아니다.

---

### 5.4 컨테이너와 표준 type constructor

```text
List[T]
Set[T]
Map[K, V]
Tuple[T1, ..., TN]
Array[T, N]
Buffer[N]
Option[T]
Result[T, E]
Iterator[T]
Generator[Y, S, R]
AsyncIterator[T]
AsyncGenerator[Y, S]
Factory[Concrete]
Dyn[Trait]
```

`Tuple`은 하나 이상의 heterogeneous type argument를 갖는 immutable native tuple이다. empty tuple type은 source type으로 제공하지 않고 `Tuple[T, ...]` 같은 homogeneous variadic shorthand도 없다. `Array[T, N]`은 `N`개의 같은 type 원소인 immutable fixed-length container, `Buffer[N]`은 정확히 `N` byte인 immutable buffer다. `N`은 `U8`·`U16`·`U32`·`U64` const parameter 또는 그 type의 compile-time constant expression이어야 한다. `Iterator[T]`·`Generator[Y, S, R]`와 `AsyncIterator[T]`·`AsyncGenerator[Y, S]`는 각각 sync·async lazy protocol이다. lazy value 생성은 소비나 effect 발생을 뜻하지 않으며 iteration, `send`, completion, `close`/`aclose` lifecycle에서 실제로 관찰한 범위만 evidence로 기록한다.

예시:

```cott
struct Collection[+T, const N: U32]:
    entries: Array[T, N]
    description: Option[Str]
```

`List`·`Set`·`Map`, `Array`, `Buffer`, `Tuple`과 `Factory`·`Dyn`의 argument는 invariant다. user generic과 trait generic은 declaration-site `+` covariance, `-` contravariance 또는 bare invariance를 선언할 수 있고, parameter는 contravariant, return type은 covariant position에서 polarity를 만족해야 한다. const parameter는 invariant다. `Set[T]`의 `T`와 `Map[K, V]`의 `K`는 compiler의 hash-stable 타입이어야 한다. 허용되는 기반 타입은 `Bool`, 정수, `Str`, `Bytes`, `Path`와 이들로만 구성된 newtype·payload 없는 enum·어떤 arity의 tuple이다. float, struct, recursive nominal type, Array/Buffer를 포함한 nominal container, `JsonValue`, `Opaque`, trait와 type parameter는 key position에서 거부한다.

Python 공개 ABI는 `CottList[T]`, `CottSet[T]`, `FrozenMap[K, V]`, native `tuple[...]`, `CottArray[T, Literal[N]]`, `CottBuffer[Literal[N]]`, `typing.AsyncIterator[T]`, `typing.AsyncGenerator[Y, S]`를 각각 사용한다. list/set/map wrapper는 private tuple/frozenset/mapping-proxy backing을, Array는 private tuple을, Buffer는 exact `bytes`를 보관한다. 모든 wrapper는 read-only operation만 노출하고 raw Python container를 공개 경계에서 암묵 변환하지 않는다.

`Factory[Concrete]`는 구현 class object를 나타낸다. bracket 안에는 정확히 하나의 type만 쓸 수 있고 alias를 해소한 결과가 type argument 없는 impl declaration일 때만 허용한다. Factory 값의 validation은 class identity만 검사하고 init을 호출하지 않으며, Factory는 hash-stable·state-legal·자동 candidate-generatable type이 아니다.

`Dyn[Trait]`는 exact nominal trait specialization을 가진 runtime wrapper다. source에서 trait에만 하나의 argument로 적용하고, Python에서는 `Dyn(value=<compiler-generated concrete>, trait=<exact Trait Protocol>)`로만 만든다. wrapper와 concrete 모두 compiler-owned exact trait carrier여야 하며 structural substitute·forged wrapper·다른 generic specialization은 거부한다. dynamic method call은 `dyn.value.method(...)`만 허용하고 inherited closure의 exact member를 dispatch한다.
### 5.5 어휘와 선언 문법
source는 UTF-8이다. identifier는 ASCII `[A-Za-z_][A-Za-z0-9_]*`로 제한한다. module·function·field·parameter·resource state는 `snake_case`, type·trait·enum variant는 `UpperCamelCase`, constant는 `UPPER_SNAKE_CASE`다. `module`, `use`, `alias`, `newtype`, `where`, `struct`, `enum`, `trait`, `impl`, `specialize`, `for`, `state`, `resource`, `initial`, `terminal`, `transition`, `transitions`, `invariant`, `init`, `const`, `external`, `type`, `fn`, `async`, `self`, `doc`, `rule`, `override`, `delete`, `remove`, `requires`, `modifies`, `ensures`, `when`, `with`, `matches`, `error`, `effects`, `old`, `true`, `false`, `and`, `or`, `not`은 keyword다. `result`는 pattern 없는 `ensures` expression scope에서만 예약되는 contextual keyword이므로 field와 payload에서는 사용할 수 있다. prelude type 이름도 user declaration으로 가릴 수 없다.

Python target validation은 CPython 3.14 hard keyword와 단독 `_`를 identifier로 거부하고 `_cott_` prefix 또는 `__`로 시작하거나 끝나는 user name도 예약한다. target projection 뒤 모든 이름에 같은 검사를 적용하므로 emitter가 identifier를 escape하거나 rename하지 않는다.

일반 문자열은 JSON escape를 사용하는 double-quoted literal이고 `doc`만 triple double quote를 사용한다. 정수는 10진수, float는 소수점 또는 exponent가 있는 10진수이며 빈 괄호 `()`는 `Unit` literal이다. 부호는 literal이 아니라 unary operator다. tab과 semicolon은 금지한다. parser는 일관된 space indentation을 받고 formatter는 4칸으로 정규화한다. `#`부터 newline까지는 comment다. blank 또는 comment-only physical line은 `NEWLINE`, `INDENT`, `DEDENT` token을 만들지 않는다.

다음 EBNF가 v1.0의 선언 surface다. `INDENT`와 `DEDENT`는 indentation token이고 `{x}`는 0회 이상, `[x]`는 선택이다.

```text
file          = module_decl, { use_decl }, { declaration } ;
module_decl   = "module", qname, NEWLINE ;
use_decl      = "use", qname, [ ".{", name_list, "}" ], NEWLINE ;

declaration   = ( [ doc_block ], ( alias_decl | newtype_decl | struct_decl
                | enum_decl | trait_decl | resource_decl | rule_decl | const_decl
                | external_type_decl | specialization_decl | scenario_decl ) ) | fn_decl | impl_decl ;
external_type_decl = "external", "type", type_name, NEWLINE ;
alias_decl    = "alias", type_name, "=", type, NEWLINE ;
newtype_decl  = "newtype", type_name, "(", type, ")", NEWLINE,
                [ INDENT, "where", expression, NEWLINE, DEDENT ] ;
struct_decl   = "struct", type_name, [ generic_params ], ":", NEWLINE,
                INDENT, { field }, { invariant_clause }, DEDENT ;
scenario_decl = "scenario", identifier, [ "for", qname ], ":", NEWLINE,
                INDENT, [ fixtures_block ], scenario_step, { scenario_step }, DEDENT ;
enum_decl     = "enum", type_name, [ generic_params ], ":", NEWLINE,
                INDENT, variant, { variant }, DEDENT ;
trait_decl    = "trait", type_name, [ generic_params ], [ "for", trait_ref, { "+", trait_ref } ], ":", NEWLINE,
                INDENT, { associated_type }, trait_method, { trait_method }, DEDENT ;
specialization_decl = "specialize", type_name, "for", trait_ref, ":", NEWLINE,
                INDENT, specialization_slot, { specialization_slot }, DEDENT ;
specialization_slot = function_name, "=", qname, NEWLINE ;
resource_decl  = "resource", type_name, ":", NEWLINE, INDENT,
                 "initial", state_name, NEWLINE, "state", state_name, NEWLINE,
                 { "state", state_name, NEWLINE }, "terminal", state_name, NEWLINE,
                 { "terminal", state_name, NEWLINE }, "transition", state_name, "->",
                 state_name, NEWLINE, { "transition", state_name, "->", state_name, NEWLINE }, DEDENT ;
rule_decl      = "rule", type_name, [ generic_params ], [ "(", type, ")" ], ":", NEWLINE,
                 INDENT, rule_clause, { rule_clause }, DEDENT ;
rule_clause    = [ "override" | "delete" | "remove" ], function_clause ;
impl_decl     = "impl", type_name, "for", trait_ref, { "+", trait_ref }, ":", NEWLINE,
                INDENT, { associated_assignment }, [ state_block ], { invariant_clause },
                [ init_decl ], impl_method, { impl_method }, DEDENT ;
associated_assignment = "type", type_name, "=", type, NEWLINE ;
state_block   = "state", ":", NEWLINE, INDENT, state_field, { state_field }, DEDENT ;
state_field   = field ;
invariant_clause = "invariant", guarded_condition, NEWLINE ;
init_decl     = "init", "(", [ parameter_list ], ")", ":", NEWLINE,
                INDENT, init_clause, { init_clause }, DEDENT ;
impl_method   = [ "async" ], "fn", function_name, "(", "self",
                [ ",", parameter_list ], ")", "->", type, ":", NEWLINE,
                INDENT, method_clause, { method_clause }, DEDENT ;
const_decl    = "const", const_name, ":", type, "=", const_expr, NEWLINE ;
const_expr    = expression | qname, "(", const_expr, ")" | "Tuple", "(", [ const_expr, { ",", const_expr } ], ")"
              | "Array", "(", [ const_expr, { ",", const_expr } ], ")" | "Buffer", "(", string_literal, ")" ;

field         = field_name, ":", type, [ "=", const_expr ], NEWLINE ;
variant       = variant_name, [ "(", parameter_list, ")" ], NEWLINE ;
trait_method  = [ "async" ], "fn", function_name, "(", "self", [ ",", parameter_list ], ")", "->", type,
                [ "=", qname ], NEWLINE ;
fn_decl       = [ "async" ], "fn", function_name, [ generic_params ],
                "(", [ parameter_list ], ")", "->", type,
                ( NEWLINE | ":", NEWLINE, INDENT, function_clause, { function_clause }, DEDENT ) ;
parameter_list = parameter, { ",", parameter }, [ "," ] ;
parameter     = parameter_name, ":", type ;

function_clause = doc_block | "rule", qname, NEWLINE | "requires", guarded_condition, NEWLINE
                | "ensures", guarded_condition, NEWLINE
                | "error", qname, [ "with", expression, "matches", pattern ], [ "when", expression ], NEWLINE
                | "effects", "[", [ qname, { ",", qname } ], "]", NEWLINE ;
init_clause   = doc_block | "requires", guarded_condition, NEWLINE | "ensures", guarded_condition, NEWLINE ;
method_clause = function_clause | "transitions", "self", ".", field_name, ":", qname, "->", qname,
                  { ",", "self", ".", field_name, ":", qname, "->", qname }, NEWLINE
                | "modifies", "self", ".", field_name, { ",", "self", ".", field_name }, NEWLINE ;
guarded_condition = expression | expression, "matches", pattern, "=>", expression ;
fixtures_block = "fixtures", ":", NEWLINE, INDENT, { fixture }, DEDENT ;
fixture       = "fs", identifier, ":", NEWLINE, INDENT, { "file", string_literal, scenario_data, NEWLINE }, DEDENT
              | "http", identifier, ":", NEWLINE, INDENT, { "route", string_literal, "->", http_outcome, NEWLINE }, DEDENT
              | "clock", identifier, ":", NEWLINE, INDENT, "start_ms", ":", integer, NEWLINE, "tick_ms", ":", integer, NEWLINE, DEDENT
              | "failure", identifier, ":", NEWLINE, INDENT, "point", ":", failure_point, NEWLINE,
                "occurrence", ":", integer, NEWLINE, "error", ":", failure_error, NEWLINE, DEDENT ;
scenario_data = ("text" | "bytes" | "hex"), "(", string_literal, ")" ;
http_outcome  = "response(status:", integer, ", body:", scenario_data, ", encoding:", string_literal, ")"
              | "redirect(status:", integer, ", location:", string_literal, ")" | "delay(ms:", integer, ")" | "disconnect()" ;
failure_point = "file.open" | "file.read" | "file.write" | "file.flush" | "file.replace"
              | "http.connect" | "http.read" | "clock.read" ;
failure_error = "permission_denied" | "not_found" | "disk_full" | "timeout" | "connection_reset" ;
scenario_arguments = expression, { ",", expression } ;
scenario_step = "call", binding_name, "=", qname, "(", [ scenario_arguments ], ")", NEWLINE
              | "spawn", binding_name, "=", qname, "(", [ scenario_arguments ], ")", NEWLINE
              | "await", binding_name, ("as", binding_name | "cancelled"), NEWLINE
              | "cancel", binding_name, NEWLINE | "tick", NEWLINE | "assert", expression, NEWLINE ;
doc_block     = "doc", triple_string, NEWLINE ;

generic_params = "[", generic_param, { ",", generic_param }, [ "," ], "]" ;
generic_param = [ "+" | "-" ], type_name, [ ":", trait_ref, { "+", trait_ref } ] | "const", const_name, ":", const_kind ;
const_kind    = "U8" | "U16" | "U32" | "U64" ;
trait_ref     = type ;
type          = qname, [ "[", type_arg, { ",", type_arg }, [ "," ], "]" ] ;
type_arg      = type | const_expr ;
qname         = identifier, { ".", identifier } ;
name_list     = identifier, { ",", identifier }, [ "," ] ;
type_name     = identifier ; state_name = identifier ; variant_name = identifier ;
function_name = identifier ; field_name = identifier ;
parameter_name = identifier ; binding_name = identifier ;
const_name    = identifier ;
```
여러 줄 parameter·generic 목록의 trailing comma는 허용하고 formatter가 붙인다. function·trait method·impl method parameter default와 overload는 문법에 없다. `self`의 무타입 표기는 trait와 impl method의 첫 parameter에서만 허용한다. `Tuple`은 적어도 하나의 type argument를 요구하고 `Array`는 type argument 하나와 const length 하나, `Buffer`는 const length 하나를 요구한다. `Tuple(...)` constant는 적어도 하나의 value, `Array(...)`는 0개 이상의 value, `Buffer("lowercasehex")`는 짝수 길이 lowercase hexadecimal byte string을 요구한다. `impl`은 top-level doc을 받을 수 없고 state block은 비어 있을 수 없다.

`external type`의 complete surface syntax는 한 줄뿐이다:

```cott
external type HttpRequest
```

external declaration은 target이나 source path를 갖지 않는 semantic named Cott type이다. AST와 HIR은 common declaration metadata와 name만 보존하며 `target`·`path` field를 두지 않는다. Canonical IR v8의 `external_type` declaration도 `annotations`, `doc`, `kind`, `name`, `public`, `source_order`, `span`만 가지며 target projection은 절대 serialize하지 않는다.

각 backend는 자신의 manifest projection table로 external declaration을 해석한다. Python에서는 `[target.python.external_types]`의 quoted fully qualified Cott external symbol을 key로, `module:Qualname`을 value로 사용한다. key는 존재하는 external declaration과 정확히 일치하고 value는 안전한 Python module/qualname이어야 한다. mapping의 누락·stale key·non-external key·malformed value는 emit 전에 hard error다. Target-side import or signature inspection은 별도 capability이며 declaration validity나 IR을 바꾸지 않는다. Rust와 TypeScript target/table은 구현되어 있지 않다.

`()`·`[]`·`{}` 안에서는 newline과 indentation token을 무시한다. clause expression은 한 logical line이어야 하며 여러 줄로 나누려면 괄호 안에 작성한다. `impl` body의 순서는 associated assignment, optional `state`, 0개 이상의 `invariant`, optional `init`, 하나 이상의 method다; assignment·state·init은 각각 최대 한 번의 해당 member로만 나타난다. `init`과 method block은 비어 있을 수 없고, `doc`은 최대 하나이며 첫 절이어야 한다. `requires` 뒤에는 method `transitions`, `modifies`, `ensures`, `error`, `effects`가 이 순서로 오며 `transitions`·`modifies`·`effects`는 각각 최대 하나다. init에는 `error`, `effects`, `transitions`, `modifies`가 없다.

function block에는 `doc` 최대 하나, `rule`, `requires`·`ensures`·`error` 각 0개 이상, `effects` 최대 하나가 이 순서로 온다. `rule`은 explicit clauses보다 앞에 오며 적용된 rule의 effective clauses와 effects를 합성한다. clause add는 추가, override는 같은 의무 치환, delete는 제거다. effects Add는 지정 key를 합집합하고, Override는 inherited effect set을 지정 set으로 바꾸며, Delete는 지정 effect key만 제거한다. 무시되는 action은 없다. 적용 전 inherited generic은 effective clause·guard·type에 치환하고, 호출부의 expression·result·guard type과 호환되어야 한다. Unit으로 낮춘 unguarded `result`를 다른 반환 type에 붙이지 않는다. error와 variant guard 동일성은 전체 canonical `SymbolId`다. 같은 module 정의 span은 유지하고, 원본 파일을 schema가 담을 수 없는 cross-module 복제 clause·effect·expression·pattern span은 적용 지점 span으로 재배치한다. top-level `doc`은 바로 다음 type, resource, rule 또는 constant declaration에 붙으며 orphan·중복 doc은 오류다.

expression precedence는 낮은 순서로 `or`, `and`, unary `not`, comparison, `+ -`, `* / %`, unary `+ -`, field/`.len`, primary다. comparison은 `== != < <= > >=`이며 연쇄 비교를 허용한다. primary는 scalar literal, `Unit` literal `()`, 현재 scope의 name·constant·enum singleton과 괄호식, method `ensures`에서만 쓰는 `old(self.field)`이다. 임의 call, index, collection literal과 attribute method call은 계약 표현식에 없다.

arithmetic operand는 같은 numeric type이어야 한다. `/`는 float에만, `%`는 integer에만 허용하고 unary `-`는 unsigned type에 허용하지 않는다. integer contract 중간값은 declared width를 넘을 수 있는 mathematical integer며 remainder는 `0 <= r < abs(divisor)`인 Euclidean remainder다. emitter는 `%`를 Python operator가 아니라 `cott_runtime._cott_euclidean_mod`로 낮춘다. zero divisor는 compile-time constant에서 semantic error, runtime clause에서 `CottContractViolation`이다. `F32` 중간 결과는 매 연산 후 binary32, `F64`는 binary64로 평가한다. compiler constant evaluator와 runtime clause·refinement evaluator는 같은 규칙을 쓴다.

```text
pattern = "_" | binding_name
        | qname, [ "(", [ pattern, { ",", pattern } ], ")" ] ;
```

`scrutinee matches pattern => condition`은 `requires`, `ensures`, invariant의 통일된 guard다. guard가 match할 때만 condition을 평가하며 binding은 condition scope에만 들어간다. `ensures Pattern => condition`은 호환 syntax로 `result matches Pattern => condition`이다. `error E with scrutinee matches pattern [when condition]`은 error guard와 optional boolean obligation을 함께 쓴다. pattern의 payload arity와 타입은 scrutinee type에 대해 검사한다.

---

## 6. 사용자 정의 타입

user type declaration은 같은 module의 forward reference와 guarded recursive nominal reference를 사용할 수 있다. alias와 newtype은 cycle을 언제나 거부하고, guarded recursion은 struct·enum nominal SCC에만 적용한다; alias/newtype은 그 SCC 주위에서 acyclic하게만 사용될 수 있다. struct·enum SCC의 cycle은 `Option`, `List`, `Set`, `Map`, `Result`의 productive branch, enum의 finite variant, 또는 compile-time length `0`인 `Array`를 거쳐야 한다. direct field cycle, nonempty `Array` cycle, finite branch 없는 `Result` cycle은 거부한다. trait bound/associated projection cycle은 type recursion과 별도 graph로 검사한다. emitter와 IR은 recursive `named` reference를 symbolic identity로 보존하고 recursive type을 hash-stable key로 만들지 않는다.

### 6.1 타입 별칭

`alias`는 기존 타입에 새로운 이름만 부여한다.

```cott
alias Timestamp = I64
alias Names = List[Str]
```

별칭은 원래 타입과 호환된다.

```cott
Timestamp == I64
```

도메인 구분이 필요하면 별칭이 아니라 `newtype`을 사용해야 한다.

---

### 6.2 Newtype

`newtype`은 기존 타입을 감싸는 새로운 명목 타입이다.

```cott
newtype UserId(U64)
newtype InputPayloadId(U64)
```

다음 두 타입은 서로 호환되지 않는다.

```cott
UserId
InputPayloadId
```

둘 다 내부적으로 `U64`를 사용하더라도 자동 변환되지 않는다.

Python ABI에서 두 wrapper는 서로 다른 class이며 `UserId(value=...)`처럼 keyword-only로 생성하고 read-only `.value`로 carrier를 읽는다. 생성자는 `runtime_validation`과 무관하게 alias를 해소한 carrier의 명목·scalar type, numeric range와 중첩 ABI를 재귀 검사하고 statically concrete `F32` path를 binary32로 normalize하며 raw Python container를 변환하지 않는다. equality는 같은 newtype class끼리만 성립하고 carrier가 5.4의 hash-stable type일 때만 hash를 제공한다.

newtype carrier는 `Never`와 trait를 제외한 cott immutable value type이어야 하며 alias를 먼저 해소한다. `Opaque` carrier는 허용되지만 compile-time constant와 hash-key position에는 여전히 쓸 수 없다.

---

### 6.3 Refinement newtype

`where`를 사용하여 값의 범위를 제한할 수 있다.

```cott
newtype Probability(F32)
    where 0.0 <= self <= 1.0

newtype Port(U16)
    where 1 <= self <= 65535

newtype NonEmptyStr(Str)
    where self.len > 0
```

refinement는 10.1의 계약 표현식 언어를 사용한다. 이 문맥의 `self`는 newtype의 기반 타입으로 해석하고 숫자 리터럴도 주변 피연산자의 타입을 따른다. newtype은 계약 표현식 안에서만 기반 타입과 투명하게 비교·산술할 수 있으며 공개 시그니처에서는 계속 명목 타입이다. 연쇄 비교는 허용하고 `and`로 정규화한다.

MVP에서는 조건을 완전히 정적으로 증명하지 않는다. 대신 다음 방식으로 사용한다.

1. 조건 표현식 자체를 타입 검사한다.
2. 가능한 리터럴 오류를 컴파일 시 검출한다.
3. 생성된 newtype 생성자가 carrier ABI를 모든 mode에서 재귀 검사하고 statically concrete `F32` path를 먼저 binary32로 normalize한 뒤 refinement 조건을 검사한다. 실패하면 carrier type 또는 refinement span을 가진 `CottContractViolation`이다.
4. `boundary`와 활성화된 `test-only` 경계가 중첩 값을 재검사한다.
5. 순수한 조건으로부터 계약 테스트 입력 전략을 생성한다.

---

### 6.4 구조체

```cott
struct Message:
    data: Bytes
    sequence: U64
    priority: Priority
```

필드는 기본적으로 필수다.

선택 필드는 `Option`으로 명시한다.

```cott
struct User:
    id: UserId
    name: Str
    nickname: Option[Str]
```

필드 기본값은 MVP에서 제한적으로 허용한다.

```cott
struct BarOptions:
    threshold: Probability = Probability(0.5)
    use_cache: Bool = false
```

필수 field는 default field보다 먼저 와야 한다. default는 13장의 compile-time constant expression이어야 하며 constructor가 실패하면 compile error다.

가변 필드는 기본적으로 제공하지 않는다.

Python 출력은 정확히 `@dataclass(frozen=True, slots=True, kw_only=True)`이고 generated struct class body는 명시적으로 `__hash__ = None`을 둔다. 동등성은 같은 generated class와 field 값으로 결정한다. 불변성은 container와 object graph의 membership을 바꾸지 못한다는 뜻이며 trait로 들어온 external object까지 deep-freeze한다고 주장하지 않는다.

field default의 계산된 Python value class가 `__hash__ = None`이면 emitter는 그 immutable value를 `<module>_types.py`의 private `Final` canonical instance에 두고 `dataclasses.field(default_factory=lambda: <instance>)`로 낮춘다. 그 밖의 hashable default는 직접 field default로 내보내며 두 방식 모두 같은 keyword-only constructor 값과 IR default 의미를 가진다.

---

### 6.5 열거형

값만 가지는 열거형:

```cott
enum Priority:
    Low
    Normal
    High
```

데이터를 포함하는 열거형:

```cott
enum BarError:
    InvalidPayload(reason: Str)
    ServiceUnavailable
    ProcessingFailed(message: Str)
```

상태를 타입으로 표현할 수도 있다.

```cott
enum JobState:
    Pending
    Running(started_at: Timestamp)
    Succeeded(result: JobResult)
    Failed(error: JobError)
```

Python의 문자열 상태 필드보다 tagged union을 우선한다.

다음 형태는 권장하지 않는다.

```cott
struct Job:
    state: Str
    error: Option[Str]
    result: Option[JobResult]
```

이 구조는 존재해서는 안 되는 상태 조합을 허용한다.

예를 들어 `state == "running"`인데 `result`가 존재하는 상황을 타입이 막지 못한다.

---

## 7. Trait

trait는 structural method signature, optional associated type, inherited trait closure와 default facade dispatch를 선언한다.

```cott
trait Summarizable:
    fn summary(self) -> Str

trait Prioritizable:
    fn priority(self) -> I32

trait TaskView for Summarizable + Prioritizable:
    fn inspect(self) -> Str
```

trait는 비어 있을 수 없고 associated type은 method보다 앞에 와야 한다. `trait Child[...] for Parent[...] + Other[...]`의 parent는 resolved nominal trait이며 graph는 acyclic이다. inherited member는 closure에 포함된다. 같은 depth의 서로 다른 parent가 incompatible same-name member를 제공하면 거부하고, child declaration은 parent member를 exact signature와 callable kind로 override한다. default dispatch와 specialization selection도 closure의 exact slot identity를 사용한다.

trait method는 signature·callable kind와 optional default target만 선언하며 독립 `requires`·`ensures`·`error`·`effects` body를 갖지 않는다. default/specialization target은 sync 또는 `async` verified public free-function facade이며 kind·receiver-first substituted signature가 exact match해야 하고, 그 free function의 contract/effects/proof obligation이 selected dispatch의 구현 계약이다. async method는 `Iterator`, `Generator`, `Never`를 return하지 않고 `AsyncIterator`·`AsyncGenerator` return은 lifecycle protocol이다. selected wrapper가 target을 direct call 또는 direct `await`한다.

`specialize Concrete for Trait:`는 existing non-impl concrete declaration을 exact trait closure에 연결하고 named slot을 verified free function으로 선택한다. each slot is unique, target kind/signature is exact, and an explicit `impl Concrete for Trait` slot takes precedence over specialization. specialization is compiler-owned dispatch metadata, not an agent implementation or manifest binding.

`impl Concrete for Trait [+ Trait ...]:`는 `Concrete`라는 새롭고 유일한 nominal Cott type을 선언하고 listed trait closure의 Cott-owned stateful class를 만든다. effective slots must all have the same callable kind. associated assignment, state/init, invariant, `modifies`, resource transition과 explicit slot coverage는 selected closure slot에 대해 exact로 검사한다.

Concrete에는 inheritance·subclassing·dynamic attribute·`__del__`가 없으며 identity equality와 identity hash만 제공한다. emitter owns the slotted shell, init, lock, public wrappers, ABI/contract/invariant/modifies/transitions checks. sync wrapper는 per-instance `RLock`으로 serialize한다. async wrapper는 task-aware reentrant lock으로 same task re-entry를 허용하고 other tasks를 serialize한다; cancellation은 helper exception처럼 wrapper boundary에서 state snapshot, transition/modifies, invariant and exception containment rules를 적용한 뒤 re-raise한다. cancellation does not manufacture a successful return or implicit cleanup.

각 explicit impl method의 agent implementation은 canonical symbol `<module>.<Concrete>.<method>`, durable path `python/_cott_impl/<module>/<Concrete>/<method>.py`, and one private exact top-level canonical function `_cott_impl_<Concrete>_<method>`를 가진다. async slot is an `async def` helper and is agent-only; trait default/specialization-selected slots have no durable agent source. compiler-generated `@runtime_checkable` Protocol, static verifier and runtime `Dyn` validation use exact trait origin, generic specialization and inherited closure; protocol member presence alone never substitutes for `Dyn` construction.

### 7.1 Resource 상태 타입

`resource`는 named immutable state type과 허용 edge를 선언한다.

```cott
resource Connection:
    initial disconnected
    state disconnected
    state connected
    state closed
    terminal closed
    transition disconnected -> connected
    transition connected -> closed
```

resource에는 정확히 하나의 declared `initial`, 하나 이상의 `state`·`terminal`·`transition`이 필요하다. state·terminal·edge는 source order로 보존되며 terminal과 edge의 양 끝은 declared state여야 한다. resource value는 generated singleton state class identity로 비교되며 impl state field에서만 lifecycle transition을 모델링한다. resource declaration은 enum·struct가 아니며 arbitrary transition, implicit cleanup, state payload는 제공하지 않는다.

---

## 8. 제네릭

### 8.1 Type 및 const generic

```cott
struct Page[+T, const N: U32]:
    items: Array[T, N]
    total: U64

fn first[T](items: List[T]) -> Option[T]
```

const generic parameter는 `const NAME: U8|U16|U32|U64`이며 type parameter와 같은 ordered
generic list에 섞을 수 있다. type use의 argument는 declaration order와 kind를 exact match해야
한다. const argument는 literal, compatible constant, arithmetic expression 또는 in-scope const
parameter이고 compile time에 canonical typed value로 계산된다. Kotlin/JVM projection에서는
free const generic과 값을 다른 argument에서 복구할 수 없는 constructor에
`_cott_const_<NAME>: CottConst` value witness를 명시해 erased JVM signature에서도 exact unsigned
mathematical value와 kind를 유지한다. witness omission, reflection 복구와 silent erasure는 없다.

### 8.2 Trait bound와 associated projection

복수 bound는 `T: Comparable + Serializable`로 쓴다. bound trait closure의 same-name member는
exact signature/kind여야 하며 otherwise HIR error다. associated projection은 trait declaration
identity와 associated name을 보존하고 impl selection 때 exact assignment로 치환한다. recursive
generic bounds are allowed only when their bound graph does not create an invalid
unresolved/self-expanding projection cycle. Kotlin은 abstract associated slot을 추가 bounded type
parameter로 lift하고, 예를 들어 `Reader<Item>`과 `Impl : Reader<Int>`처럼 표현한다. Concrete impl
assignment는 override 전에 concrete Kotlin type으로 치환한다. Base를 subtype으로 만들지 못하는
phantom wrapper, reflection 또는 blanket runtime witness는 사용하지 않는다.

### 8.3 변성과 `Dyn`

generic type parameter is invariant unless declared `+` or `-`; const parameter is invariant. The verifier checks parameter/return nesting polarity, including invariant constructors. nominal assignability follows declared variance and trait inheritance. `Dyn[Trait]` deliberately does not inherit this implicit conversion: construction is explicit and exact nominal runtime validation preserves the full trait specialization.

Python emitter는 declared variance를 `TypeVar`로, fixed length를 `Literal[N]`으로 projection한다.
Kotlin emitter는 declaration-site variance와 bounded generic을 유지하지만 JVM의 ordinary type과
associated generic은 erased된다. 따라서 그 input/return/associated 관계는 static guarantee이고
runtime에서 임의의 `T`를 per-call reify하거나 unify했다고 주장하지 않는다. Concrete associated
assignment와 explicit const value witness만 concrete runtime descriptor/value를 갖는다. 어느
backend도 generic 관계를 implicit `Any`로 약화하지 않는다.

---

## 9. 함수 선언

cott 함수는 execution body가 없는 sync 또는 explicit async declaration이다. free-function block에는 `doc`, `rule`, `requires`, `ensures`, `error`, `effects`만 들어간다.

```cott
async fn fetch_payload(id: PayloadId) -> Result[Payload, FetchError]:
    ensures Result.Ok(payload) => payload.id == id
    effects [network]
```

`async fn` is allowed for free functions, trait methods and impl methods. Its default/specialized
target and selected slot must match callable kind exactly. async callable return type cannot be
`Iterator`, `Generator` or `Never`; `AsyncIterator[T]` and `AsyncGenerator[Y, S]` model an explicit
async lifecycle protocol instead of a native async-generator implementation function. Canonical IR,
provenance, facade, binding signature and contract runner preserve `sync`/`async` callable kind.
Python facade는 implementation coroutine을 직접 await하고 Kotlin은 exact `suspend`, Dart는
`Future<T>` callable을 사용한다. Dart cancellation은 명시적 cooperative scope이며 임의 Future
preemption을 주장하지 않는다. Sync compatibility wrapper, thread bridge, nested event loop는
없고 callable kind 변경은 breaking이다.

함수 오버로딩과 parameter default는 금지한다. 호출 option은 default field가 있는 struct로
묶는다. Python parameter는 positional-or-keyword로, Kotlin은 Kotlin signature로, Dart는
target-private helper와 public Dart signature로 emit한다. Module 내 function 이름은 유일하다.

---

## 10. 계약

### 10.1 계약 표현식

refinement, `requires`, `ensures`, `error`, struct/impl invariant와 rule clause는 하나의 정규화된 순수 표현식 언어와 통일된 match guard를 사용한다.

허용 대상은 숫자·문자열·boolean·`Unit` literal, 현재 declaration parameter·constant, `ensures`의 `result`, struct/refinement/impl의 `self`, cott field와 `.len`, method `ensures`의 `old(self.field)`, 산술·연쇄 비교·동등성·`and`·`or`·`not`이다. struct invariant에서만 `starts_with(Str, Str)`, `ends_with(Str, Str)`, `contains(Str, Str)`, `unique_by(List[T], T.field)`, `descending_by(List[T], T.field)`의 다섯 total intrinsic을 추가로 허용한다. 후자의 selector는 resolve된 nominal element field여야 하며 runtime callable·문자열 selector가 아니다. `unique_by`는 canonical Cott equality를, `descending_by`는 orderable scalar의 non-increasing order를 검사한다. 빈/singleton list는 둘 다 참이다. guard의 scrutinee는 그 clause의 base scope에서 평가되고 pattern binding은 guard condition에만 보인다. `requires`와 invariant guard는 matched 경우에만 obligation을 만든다; `ensures` guard는 normal return 뒤 match한 경우에만 검사한다. legacy `ensures Pattern => condition`은 result scrutinee shorthand다.

선언되지 않은 ambient 이름, file/network/database/clock/random 접근, object method와 임의 Python function call, state change와 nondeterministic expression은 금지한다. 표현식의 모든 이름과 type은 HIR에서 해석한다. 숫자 literal은 문맥 type을 따르고 연쇄 비교는 short-circuit `and`로 정규화한다. equality operand는 같은 resolved non-trait cott value type이어야 하며 type parameter, trait 또는 `Opaque`를 transitive하게 포함할 수 없다. 모든 refinement, guard condition, `requires`, `ensures`, invariant와 `when`의 최종 type은 `Bool`이어야 한다.


### 10.2 사전 조건

`requires`는 호출자가 만족해야 할 조건이다.

```cott
fn slice(
    values: List[U32],
    offset: U64,
    length: U64,
) -> Result[List[U32], SliceError]:
    requires length > 0
    error SliceError.OutOfBounds when offset + length > values.len
```

호출자가 사전 조건을 만족하지 못하면 구현을 호출해서는 안 된다. 런타임 검사가 활성화된 경계에서는 항상 `CottContractViolation`을 발생시키며 cott `Result` 오류로 변환하지 않는다. `off`에서는 검사하지 않으며, 사전 조건을 어긴 호출의 결과는 계약 밖이다.

### 10.3 사후 조건

`ensures`는 정상 또는 오류 반환 이후 반드시 만족해야 할 조건이다.

```cott
ensures Result.Ok(part) => part.len == length
```

오류 결과에 대한 중첩 pattern도 선언할 수 있다.

```cott
ensures Result.Err(SliceError.OutOfBounds) => offset + length > values.len
```

pattern이 없으면 expression scope는 function argument, constant와 반환값 전체를 가리키는 `result`다. pattern이 있으면 일치하는 반환에서만 expression을 검사하고 scope는 function argument, constant와 그 pattern binding이며 `result`는 사용할 수 없다. impl method는 두 scope 모두에 `self`를 더하고 §7의 제한된 `old(self.field)` snapshot도 사용할 수 있다. 반환 type 검사 후 source order의 모든 applicable `ensures`를 검사한다.

`Result[T, E]` 반환 callable의 최종 resolved contract에 `error` 절이 하나 이상 있으면 적어도 하나의 정확한 top-level `ensures Result.Ok(binding) => Bool`이 있어야 한다. 이것이 성공 의무의 유일한 표기다. wildcard·`Result.Err`·중첩/별칭/boolean result 검사로는 충족하지 않으며, 여러 Ok `ensures`는 각각 독립 의무다. rule expansion·override/delete 뒤에 lint하므로 source fragment가 아니라 effective contract가 판정 대상이다. 없으면 callable span에 `Result contract with errors requires a guarded Result.Ok ensures success obligation`을 낸다.

```cott
fn append[T](
    values: List[T],
    value: T,
) -> List[T]:
    ensures result.len == values.len + 1
```

### 10.4 오류 조건

`error` 절은 함수가 반환할 수 있는 오류 variant를 완전한 이름으로 선언한다.

```cott
enum LoadDataError:
    FileNotFound(path: Path)
    UnsupportedFormat(path: Path)

fn load_payload(
    path: Path,
) -> Result[InputPayload, LoadDataError]:
    error LoadDataError.FileNotFound
    error LoadDataError.UnsupportedFormat
    effects [file.read]
```

`error Variant with scrutinee matches Pattern when condition` 또는 `error Variant when condition`은 match/condition이 참일 때 해당 variant를 반환해야 하는 조건부 도메인 의무다. 조건 없는 `error Variant`는 허용된 환경 실패 allowance일 뿐 conditional coverage 영역에 포함하지 않는다. `when true`도 conditional이며 bare error로 접지 않는다. 모든 requires-valid input에서 모든 조건부 predicate를 source order로 평가한다. 서로 다른 variant를 포함해 여러 predicate가 동시에 참이면 source-order 첫 conditional error가 규범적으로 반환 variant를 정하고, runner는 뒤의 applicable clause도 condition/applicability evidence로 기록하되 모순이나 별도 반환 의무로 취급하지 않는다. 같은 variant의 distinct clause도 각각 evidence를 가진다.

`Result` 함수에 `error` 절이 하나라도 있으면 그 목록은 허용된 오류 variant의 exhaustive set이다. 런타임 검사가 활성화된 facade는 모든 `Err` 반환이 이 집합에 속하는지 검사한다. `off`에서는 이 항목을 신뢰 선언으로 낮춘다. `error`는 `Result[T, E]` function 또는 impl method에만 올 수 있고 variant는 `E`에 속해야 한다.

`error`는 다음에 사용된다.

* AI 구현 지시
* 순수 함수의 계약 테스트 생성
* API 문서 생성
* 오류 분기 누락 검사

### 10.5 부작용

함수의 외부 부작용은 `effects`에 명시한다.

```cott
effects [file.read]
effects [file.write]
effects [network]
effects [database.read]
effects [database.write]
effects [clock]
effects [random]
effects [process.exit]
```

여러 효과:

```cott
effects [network, database.write]
```

`effects`가 없는 함수는 계약상 순수하다.

```cott
fn normalize_score(value: F32) -> Probability:
    requires 0.0 <= value <= 1.0
```

prelude effect 이름은 위 여덟 개다. CPU 계산 자체는 effect가 아니다. 다른 이름은 project manifest에 등록한다.

```toml
[effects]
"device.read" = true
"engine.compute" = true
```

manifest effect key는 qname 문법이고 value는 literal `true`여야 한다. false·non-boolean value, empty list, unknown name, prelude 재정의와 한 effects list 안의 duplicate는 오류다. Canonical IR은 effect set을 이름순으로 저장한다.


`effects`는 Canonical IR metadata이자 implementation-call-graph 검증 대상이다. implementation은 exact generated facade로만 다른 Cott free function을 호출할 수 있고, verifier는 canonical function에서 same-file private helper까지 도달하는 모든 그 call edge의 declared callee effect를 합집합으로 계산한다. caller effect set이 이를 포함하지 않으면 path를 포함한 implementation error다. async callee는 반드시 `await`, sync callee는 절대 `await`하지 않는다. stdlib·external projection·generated value constructor와 exact Factory constructor는 effect leaf이며, Cott 밖 코드의 실제 side effect와 import-time behavior는 여전히 trust declaration이다.

### 10.6 Struct invariant와 canonical constructor

`struct` body는 `field* invariant*`다. invariant 뒤 field는 syntax error이고 duplicate invariant는 source order 그대로 허용한다. invariant는 기존 `SCRUTINEE matches PATTERN => BOOL` guard를 그대로 쓴다. fields와 generic을 먼저 lower한 뒤 `self`를 `Named[Struct, declared generic args]`로 type-check하며 `result`, `old`, ambient name은 허용하지 않는다. intrinsic arity/type/selector 오류는 expression span에, Bool 이외 condition은 `struct invariant condition must be boolean`으로 보고한다.

IR의 모든 struct는 source-order `invariants`를 반드시 가진다(없는 경우 `[]`). 각 node는 `clause_id`, `guard`, typed `expression`, `span`이며, intrinsic은 closed name·typed arguments·resolved `{owner, field}` selector를 canonical JSON에 저장한다. AST/HIR/source spelling을 재해석하지 않고 이 IR만 emitter와 runner가 소비한다.

생성된 frozen keyword-only dataclass가 유일한 canonical smart constructor다. Python argument/default factory 평가 뒤 `__post_init__`가 declaration order로 field ABI를 validate·normalize하고 `object.__setattr__`한 다음 invariant guard/condition을 clause order로 평가한다. 첫 false는 `CottContractViolation`에 `symbol`, `clause="invariant:N"`, `phase="invariant"`, canonical span과 expected/actual을 담아 실패한다. guard non-match는 satisfied다. direct construction도 이 순서를 우회하지 않는다. active facade ABI boundary는 exact nominal type·concrete generic substitution·depth 64/node 1024/cycle 검사를 공유 traversal state에서 끝낸 뒤 같은 constructor로 재구성하므로 `object.__new__`, deserialization, mutation으로 만든 invalid value도 거부한다. `off`가 facade traversal을 생략해도 constructor invariant는 끄지 않는다. default가 명백히 false면 compile error이고, 그 외에는 repair·sort·deduplicate 없이 construction failure다.

### 10.7 Finite scenario, fixture와 workflow

scenario는 public facade만 호출하는 비공개 declaration이며 public target API symbol을 만들지
않는다. `call value = facade(args)`는 sync call 또는 async facade의 completion을 저장하고,
`spawn worker = async_facade(args)`는 async public facade만 허용한다. `await worker as value`,
`await worker cancelled`, `cancel worker`, `tick`, `assert Bool`만 있다. loop, branch, sleep,
callback, arbitrary code, private implementation/binding import와 widget/tree syntax는 없다. prior
value와 typed field만 다음 argument/assertion에 쓸 수 있고 worker reference는 ABI value가 아니다.

scenario는 최대 64 step이고 적어도 한 step을 가져야 한다. `verification.lifecycle_limit`
(1..64)은 동시 live worker와 총 tick의 상한이다. worker는
`pending -> completed(value)|failed(exception)|cancel_requested -> cancelled`이고 `cancel`은 live
worker에 한 번만, value/cancelled await는 terminal outcome에 한 번만 유효하다. scenario는
`ready -> running -> passed|failed -> cleaned`; 종료 시 live/unconsumed worker가 있으면 실패하고
모두 cancel/join한다. `tick`은 target scheduler의 정확히 한 cooperative turn이며 Python은
`asyncio.sleep(0)`, Kotlin은 `kotlinx.coroutines.yield()`를 사용한다. bounded join과 OS resource
limit은 containment이지 ordering evidence가 아니다.

`fixtures:` 안의 closed kind는 `fs`, `http`, `clock`, `failure`뿐이다. filesystem은 normalized relative POSIX path와 inline `text`/`bytes` file만, HTTP는 normalized `/path`와 `response(status, body, encoding)`·relative `redirect(status, location)`·`delay(ms)`·`disconnect()`만, clock은 unsigned `start_ms`/`tick_ms`만 가진다. failure는 `file.open|read|write|flush|replace`, `http.connect|read`, `clock.read`의 정확히 한 occurrence와 `permission_denied|not_found|disk_full|timeout|connection_reset`만 가진다. source/manifest/IR에는 host path, socket address, remote URL, script, plugin 또는 monkeypatch name이 없다. HIR은 target/argument/result/fixture reference를 resolve하고 required effect union과 fixture authority의 exact match를 강제한다. custom/database/random/process effect는 fixture backend가 없으므로 observed scenario가 될 수 없다.

scenario strategy는 source order, stable IDs/spans, resolved facade/callable identity, typed steps, required effects, closed fixtures, effective limits를 v5 JSON으로 serialize한다. scratch root, port, PID, host time은 strategy/evidence에 serialize하지 않는다. trace는 source order `{step_id, operation, facade?, worker?, outcome, value_binding?}`와 ABI type/assertion boolean만 기록하며 arbitrary/opaque value와 host exception text는 기록하지 않는다. successful scenario evidence는 bounds, cleanup outcome, referenced fixture event IDs를 가진 `test observation`; unavailable execution capability는 `unobserved`다. facade를 호출했다는 사실만으로 unrelated clause evidence를 credit하지 않는다.

## 11. 상태를 타입으로 표현하기

cott는 boolean 플래그보다 enum 상태 모델을 우선한다.

권장하지 않는 구조:

```cott
struct Config:
    is_loaded: Bool
    path: Option[Path]
    error: Option[Str]
```

권장 구조:

```cott
enum ConfigState:
    Unloaded
    Loading(path: Path)
    Ready(config: Config)
    Failed(error: ConfigLoadError)
```

이 방식은 잘못된 상태 조합을 타입 단계에서 제거한다.

cott의 타입 시스템은 단순히 값의 자료형을 설명하는 것이 아니라, **허용되는 프로그램 상태를 제한하는 도구**로 사용한다.

---

## 12. 표준 오류 모델

### 12.1 Result

```cott
enum Result[T, E]:
    Ok(value: T)
    Err(error: E)
```

복구 가능한 실패는 모두 `Result`로 표현한다. 계약 표현식에서는 `Result.Ok`와 `Result.Err`로 variant를 참조한다.

### 12.2 Option

```cott
enum Option[T]:
    Some(value: T)
    Nothing
```

값이 존재하지 않는 상황은 `Option`으로 표현한다. `Nothing`은 Python 예약어 `None`과 충돌하지 않는 표준 빈 variant다. `Option.Nothing`은 괄호 없는 payloadless qualified name이며, 기대 type이 `Option[T]`인 top-level `const` expression과 struct·state field default에서 모든 `T`(`Any` 포함)의 canonical absence value로 허용된다. 이는 `Unit` literal `()`와 별개의 값이다. `Option.Some`과 `Result`의 payload constructor는 이미 별도로 지원되지 않는 한 이 추가 범위에 포함하지 않는다.

### 12.3 Never

반환하지 않는 함수는 `Never`를 사용한다.

```cott
fn terminate(message: Str) -> Never:
    effects [process.exit]
```

### 12.4 예외 정책

cott 공개 함수에서 선언되지 않은 `Exception`이 발생하면 구현 계약 위반이다.

Python 라이브러리의 예외는 구현 경계에서 cott 오류 타입으로 변환해야 한다. 생성된 Python variant 생성자는 keyword-only다.

```python
try:
    data = path.read_bytes()
except FileNotFoundError:
    return Err(error=LoadDataError_FileNotFound(path=path))
```

### 12.5 경계 타입

`JsonValue`는 다음 cott 표준 tagged union으로 고정한다.

```cott
enum JsonValue:
    Null
    Boolean(value: Bool)
    Integer(value: I64)
    Float(value: F64)
    String(value: Str)
    Array(value: List[JsonValue])
    Object(value: Map[Str, JsonValue])
```

JSON integer는 `I64` 범위여야 하고 float는 유한한 IEEE 754 binary64 값이어야 한다. parser와 adapter는 범위 밖 integer, `NaN`과 infinity를 오류로 변환해야 한다. 이 제한보다 넓은 손실 없는 number가 필요하면 domain newtype `Str`과 명시적 parser를 사용한다.

`Opaque["tag"]` tag는 `[a-z][a-z0-9._-]{0,63}`이어야 한다. Opaque는 alias, newtype, struct field, enum payload, trait signature, container, function and method signature에 재귀적으로 놓일 수 있으며 manifest binding의 direct public boundary에 제한되지 않는다. 금지되는 위치는 declared property가 성립하지 않는 compile-time constant와 hash-key position뿐이다.

Python ABI는 invariant `cott_runtime.Opaque[Literal["tag"]]` frozen wrapper 하나로 고정하고 instance의 literal tag도 runtime에 저장한다. 두 wrapper는 tag가 같고 wrapped object가 `is`로 같을 때만 동등하며 wrapped object의 equality를 호출하지 않고 hash도 제공하지 않는다. `unwrap() -> object`를 제공하며 adapter는 concrete external type으로 명시적으로 `cast`한다. `Any`, `Unknown`, agent-generated function과 recursive placement의 `Opaque`도 declared contract대로 허용한다.

---

## 13. 상수

```cott
const MAX_PAYLOAD_LIMIT: U32 = 8192
const DEFAULT_THRESHOLD: F32 = 0.5
```

상수는 타입 검사 시 사용할 수 있다.

```cott
newtype PayloadSize(U32)
    where 1 <= self <= MAX_PAYLOAD_LIMIT
```

MVP constant expression은 scalar literal, imported constant 또는 같은 module에서 앞서 선언된 constant, arithmetic·boolean operator, enum singleton, `Option.Nothing`과 newtype constructor로 제한한다. `Option.Nothing`은 기대 type이 `Option[T]`일 때만 canonical absence value이며, 다른 기대 type에서는 unknown-name 중복 없이 type diagnostic 하나를 낸다. struct와 state field default도 같은 scope를 사용하며 다른 field를 참조하지 않는다. compiler가 타입 검사·평가·숫자 정규화·refinement 검사를 마친 canonical value를 IR에 저장하므로 module DAG와 source order상 value dependency도 acyclic하다.

---

## 14. 전체 예시

```cott
module foo.bar

const MAX_PAYLOAD_SIZE: U32 = 8192

newtype Probability(F32)
    where 0.0 <= self <= 1.0

newtype PayloadSize(U32)
    where 1 <= self <= MAX_PAYLOAD_SIZE

enum PayloadFormat:
    Raw
    Text
    Structured

struct InputPayload:
    data: Bytes
    declared_size: PayloadSize
    format: PayloadFormat

struct OutputPayload:
    data: Bytes
    source_size: PayloadSize
    format: PayloadFormat

enum BarError:
    InvalidPayload(reason: Str)
    ServiceUnavailable
    ProcessingFailed(message: Str)

struct BarOptions:
    threshold: Probability = Probability(0.5)
    use_cache: Bool = false

fn process_bar(
    data: InputPayload,
    options: BarOptions,
) -> Result[OutputPayload, BarError]:
    doc """
    foo 입력을 bar 규칙으로 처리하고 원본 선언 크기와 형식을 기록한 출력을 반환한다.
    """

    ensures Result.Ok(output) => output.source_size == data.declared_size
    ensures Result.Ok(output) => output.format == data.format

    error BarError.InvalidPayload when data.data.len == 0
    error BarError.ServiceUnavailable
    error BarError.ProcessingFailed

    effects [network]
```

---

## 15. 컴파일러 구조

cott 컴파일러는 다음 단계로 구성한다.

```text
소스 코드
  ↓
Lexer
  ↓
CST
  ↓
AST
  ↓
이름 해석
  ↓
HIR
  ↓
타입 검사
  ↓
계약 검사
  ↓
Canonical IR
  ↓
Target emitter
```

### 15.1 CST

Concrete Syntax Tree는 원본 토큰, 공백, 주석을 보존한다.

다음 기능에 사용한다.

* formatter
* IDE
* 자동 수정
* 정확한 오류 위치
* 소스 코드 재작성

### 15.2 AST

AST는 문법적인 구조만 표현한다.

예시:

```text
FunctionDecl
StructDecl
EnumDecl
TraitDecl
ImplDecl
StateBlock
StateField
InvariantClause
InitDecl
ImplMethodDecl
ModifiesClause
NewtypeDecl
RequiresClause
EnsuresClause
OldStateFieldExpr
```

HIR은 이름이 해석되고 type expression·const value·guard가 정규화된 내부 구조다. trait inheritance closure·specialization/default target, impl assignment와 explicit/default/specialized selected slot, resource state/edge, sync/async method kind, guarded recursive nominal graph를 type-check한 뒤에만 Canonical IR로 내린다. HIR은 state type/default·init mapping·exact signature union·associated bound·variance polarity·guard scope·`old` field identity·modifies write-set·resource edge를 검증한다.


예를 들어 다음 두 타입 표현은 HIR에서 같은 심볼을 가리킨다.

```cott
InputPayload
system.data.InputPayload
```

### 15.4 Canonical IR

Canonical IR v8는 에이전트나 특정 언어 문법에 종속되지 않는 정규 표현이다. normative `schema_version`은 **8**이며 compiler는 emit 직전과 IR load 직후 v8 schema를 검증한다. 다음 JSON은 필드 형태를 보여 주는 비규범 표시 fragment이며 schema-conformant instance가 아니다.

실제 IR file의 top-level object는 `schema_version`, fully qualified `module`, project-relative `source`, sorted `imports`와 `declarations`를 가진다. declaration은 공통 `annotations`·`kind`·fully qualified `name`·`public`·`doc`·`span`을 가진다. function과 trait/impl method는 `callable_kind` (`sync` 또는 `async`)를 보존한다. trait는 generic variance·ordered parent closure·associated type·method/default identity를, specialization은 concrete·trait·selected slot을, impl은 associated assignment·selected method slot·resource transition을, resource는 initial state·ordered states/edges를 추가한다. external type은 target projection이 아닌 semantic metadata만 가진다.

적용된 policy 정체성은 새 닫힌 IR 필드가 아니라 기존 annotation `{name, argument, span}`이다. compiler는 `name`이 `cott.applied_rule`이고 `argument`가 정확한 fully qualified rule symbol이며 `span`이 적용 지점인 metadata를 붙인다. 함수에는 직접 적용, method 적용은 enclosing impl(intent 단위가 owner methods를 포함), 중첩 적용은 rule 선언에 붙인다. IR base 정체성은 `base`다. `base_type`은 HIR-only generic substitution data이며 IR field가 아니다. 작성된 prose나 새 executable effect가 아니고 runtime ABI도 없으며 schema/ABI bump도 없다. source annotation 이름은 단일 identifier라 `cott.applied_rule`은 철자할 수 없는 compiler-internal 이름이다.

type node kind는 `primitive`, `named`, `type_parameter`, `associated_projection`, `any`, `unknown`, `list`, `set`, `map`, `tuple`, `array`, `buffer`, `option`, `result`, `iterator`, `generator`, `async_iterator`, `async_generator`, `factory`, `dyn`, `opaque`로 닫혀 있다. generic argument는 type 또는 canonical const value다. alias는 IR type에서 제거하고 `named`는 fully qualified declaration과 ordered argument를 가진다. recursive `named` edge is symbolic, never an expanded copy. `factory` node는 type argument 없는 impl declaration의 `named` node이고 `dyn` node는 exact trait reference다. expression과 match guard/pattern은 resolved cott type·symbol identity와 span을 가진다.

declaration kind와 추가 field는 닫혀 있다: `alias(target)`, `newtype(carrier, refinement)`, `struct(generics, fields, invariants)`, `enum(generics, variants)`, `trait(generics, parents, associated_types, methods)`, `specialization(concrete, trait, slots)`, `impl(traits, associated_types, state, invariants, init, methods, selected_methods)`, `resource(initial, states, terminals, edges)`, `rule(generics, base, contract)`, `const(type, value)`, `function(callable_kind, generics, parameters, return_type, contract, effects)`, `scenario(target, required_effects, fixtures, steps, lifecycle_limit)`, `external_type()`. scenario는 `public:false`이고 facade symbol이 아니지만 contract projection에는 포함된다. resource `terminals`는 terminal declaration의 state identity·source order·span을 별도로 보존하고 `states[].terminal` membership과 일치해야 한다. clause는 kind-specific fields, optional typed match guard, expression, source span과 stable clause ID를 가진다.

integer canonical value는 sign을 포함한 base-10 string, `F32`·`F64`는 width와 IEEE bit-pattern lowercase hex, `Bool`·`Str`은 JSON scalar, `Bytes`와 `Buffer`는 lowercase hex, `Unit`은 typed null로 저장한다. tuple/array child value는 declaration order, set element와 map entry는 typed canonical key JSON bytes order다. `Array` value의 item count와 `Buffer` byte count는 declared canonical length와 같아야 한다.

declaration, field, parameter와 contract clause array는 source order를 보존한다. 의미가 set인 effect와 import는 fully qualified name으로 정렬한다. source span은 raw UTF-8의 0-based start·exclusive-end byte offset과 1-based line·Unicode-scalar column을 함께 가진다. 한 IR module의 span.file은 그 module source다. 다른 module에서 복사한 확장 node는 적용 지점 span을 쓰며 호출부 텍스트에 외국 byte offset을 붙이지 않는다. schema에 없는 field는 거부한다. IR JSON은 sorted key, insignificant whitespace 없음, final newline 하나로 canonicalize하고 schema version을 `generation_id`에 포함한다.

normative schema는 repository의 `schemas/canonical-ir.schema.json` (v8), `schemas/generation.schema.json` (v7), `schemas/diagnostics.schema.json` (v1), `schemas/contract-test.schema.json` (v5)이다. 모두 JSON Schema Draft 2020-12이며 compiler binary가 embed하고 IR/generation/diagnostic/contract-strategy writer와 reader가 해당 current schema를 검증한다. v7 IR, v6 generation, ABI 6, v4 strategy의 reader/default/shim은 없다.

```json
{
  "kind": "function",
  "name": "foo.bar.process_bar",
  "parameters": [
    {
      "name": "data",
      "type": {"kind": "named", "name": "foo.bar.InputPayload"}
    },
    {
      "name": "options",
      "type": {"kind": "named", "name": "foo.bar.BarOptions"}
    }
  ],
  "return_type": {
    "kind": "result",
    "ok": {"kind": "named", "name": "foo.bar.OutputPayload"},
    "error": {"kind": "named", "name": "foo.bar.BarError"}
  },
  "contracts": {
    "requires": [],
    "ensures": [
      {
        "pattern": {
          "kind": "variant",
          "name": "core.result.Result.Ok",
          "arguments": [{"kind": "binding", "name": "output"}]
        },
        "expression": {
          "kind": "equal",
          "left": {
            "kind": "field",
            "base": {"kind": "binding", "name": "output"},
            "name": "source_size"
          },
          "right": {
            "kind": "field",
            "base": {"kind": "parameter", "name": "data"},
            "name": "declared_size"
          }
        },
        "span": {"file": "src/foo/bar.cott", "start": [43, 5], "end": [43, 74]}
      },
      {
        "pattern": {
          "kind": "variant",
          "name": "core.result.Result.Ok",
          "arguments": [{"kind": "binding", "name": "output"}]
        },
        "expression": {
          "kind": "equal",
          "left": {
            "kind": "field",
            "base": {"kind": "binding", "name": "output"},
            "name": "format"
          },
          "right": {
            "kind": "field",
            "base": {"kind": "parameter", "name": "data"},
            "name": "format"
          }
        },
        "span": {"file": "src/foo/bar.cott", "start": [44, 5], "end": [44, 62]}
      }
    ],
    "errors": [
      {
        "priority": 0,
        "variant": "foo.bar.BarError.InvalidPayload",
        "when": {
          "kind": "equal",
          "left": {
            "kind": "len",
            "value": {
              "kind": "field",
              "base": {"kind": "parameter", "name": "data"},
              "name": "data"
            }
          },
          "right": {"kind": "integer", "value": "0"}
        },
        "span": {"file": "src/foo/bar.cott", "start": [46, 5], "end": [46, 58]}
      },
      {
        "priority": null,
        "variant": "foo.bar.BarError.ServiceUnavailable",
        "when": null,
        "span": {"file": "src/foo/bar.cott", "start": [47, 5], "end": [47, 38]}
      },
      {
        "priority": null,
        "variant": "foo.bar.BarError.ProcessingFailed",
        "when": null,
        "span": {"file": "src/foo/bar.cott", "start": [48, 5], "end": [48, 36]}
      }
    ]
  },
  "effects": ["network"]
}
```

IR은 다음 목적으로 사용한다.

* Python facade·`.pyi`, Kotlin facade/runtime, Dart package facade/runtime source 생성
* target별 agent prompt 생성
* 문서와 deterministic test strategy 생성
* semantic contract·public target API 변경점 비교
* backend별 closed generation record와 verification plan 생성

에이전트 prompt의 semantic payload는 선택 symbol의 scoped transitive Canonical IR declaration context다. 대상 callable, explicit identifier·nominal reference·`constant_ref`로 닫히는 type·const·helper, `cott.applied_rule`과 그 base 및 그 `doc`, 관련 incoming scenario, retained generator rule 식별자, 사람이 읽을 수 있게 렌더한 `doc`·clause를 포함한다. raw `.cott` source는 workspace에서 read-only context로만 제공하고 agent나 target이 다시 parse한 결과를 계약 의미로 사용하지 않는다. runtime loader도 authored `.cott`를 live로 읽지 않는다.

`contracts.requires`, `contracts.ensures`, `contracts.errors`는 원본의 모든 절을 순서대로 보존한다. 각 절은 kind별 source-order `clause_id`, source span과 resolved expression을 가진다. `ensures.pattern`은 `null`이거나 `variant`·`binding`·`wildcard`의 재귀 node며 expression과 별도로 타입 검사한다. 조건부 `error`의 `priority`는 source-order identity/diagnostic ordering이면서 overlap precedence다. 동시에 applicable한 conditional error에서는 첫 priority만 반환 variant를 결정한다. 조건 없는 `error`는 `priority: null`, `when: null`을 가진다. target은 문자열을 재파싱하지 않는다.

상수는 `{"kind": "const", "name", "type", "value", "public", "span"}` declaration으로 저장한다.
값은 compile-time canonical value다. refinement·default·contract expression의 constant reference는
항상 canonical `constant_ref` node와 symbol identity를 보존하며 Canonical IR이나
`contract_surface`에서 값으로 inline하지 않는다. intent selector는 `constant_ref`와 nested
`kind: constant`를 같은 종속성 닫힘에 포함한다. target 최적화는 이 단계 뒤에만 값을 inline할 수
있다. Python `public_python_symbols(IR)`과 Kotlin/Dart `public_symbols`는 전체 공개 declaration의
결정적 target symbol 집합을 기록하며 compiler-synthesized support name은 제외한다.
Target record 간에 다른 backend의 projection field를 재사용하지 않는다.

기존 구현의 import 경로는 대상 언어에 종속되므로 Canonical IR에 포함하지 않는다. 대상 emitter와 verifier가 manifest binding을 IR과 함께 해석한다.

계약 의미의 원본은 Canonical IR뿐이다. target emitter의 결정적 입력은 Canonical IR, 선택한 target
manifest, compiler·runtime version, 해석된 implementation symbol identity·source/runtime
origin·content hash다. Python은 exact interpreter/platform·type checker·lockfile/dependency
identity를 추가하고 Kotlin은 exact kotlinc/JDK/JAR compile input과 runtime dependency identity를
추가한다. implementation 본문은 compiler 생성물이 아니지만 facade와 provenance에 포함되는
authenticated target input이다.

각 target의 `generation.json`은 이 입력, agent executable·version·initial prompt hash와 실제
verification result를 해당 target의 닫힌 schema로 기록한다. 결정적인 compiler 산출물과
비결정적인 implementation provenance는 별도 field로 구분한다.

---

## 16. Python 대상 생성

MVP compiler host와 runtime target은 `x86_64` 또는 `arm64` Linux/macOS의 CPython 3.14이다. interpreter의 canonical path, full version, `sys.implementation.cache_tag`, `sys.platform`, normalized `platform.machine()`과 `sysconfig.get_platform()`을 provenance에 기록한다. configured interpreter가 compiler host의 OS family·architecture와 다르거나 다른 Python implementation·minor version이면 거부한다. generated artifact는 configured CPython full patch version에 고정되므로 Python patch upgrade 뒤에는 `cott emit`·full `cott verify`와 package rebuild가 필요하다.

### 16.1 기본 생성물

cott는 Python 대상으로 다음 파일을 생성한다.

```text
generated/
├── python/
│   ├── cott_runtime/
│   │   ├── __init__.py
│   │   └── py.typed
│   ├── _cott_impl/
│   │   ├── __init__.py
│   │   └── foo/
│   │       ├── __init__.py
│   │       └── bar/
│   │           ├── __init__.py
│   │           └── process_bar.py
│   └── foo/
│       ├── __init__.py
│       ├── py.typed
│       ├── bar.py
│       └── bar_types.py
├── stubs/
│   └── foo/
│       └── bar.pyi
├── ir/
│   └── foo.bar.json
├── docs/
└── generation.json

```
`tests/generated/<module path>/<callable>.json`은 compiler가 실행하는 deterministic managed contract-test strategy v5다. callable은 free function의 `<function>` 또는 impl method의 `<Concrete>/<method>`다. 닫힌 object는 `schema_version`, `symbol`, `seed`, seven existing limits, `callable_kind`, `return_kind`, `classification`, ordered `clause_ids`, ordered `obligations:[{clause_id, role:"success"|"conditional_error"}]`, 그리고 `scenario:null|{id,required_effects,fixtures,steps,lifecycle_limit,limits}`를 가진다. scenario의 `steps`는 64개 이하이고 limits는 effective `verification.fixtures` ceiling이다. generated Python source는 strategy를 해석하지 않는다.

`cott_runtime` ABI **7**는 numeric alias `I8`…`U64`·`F32`·`F64`, `Option`·`Result`, `Ok`·`Err`·`Some`·`Nothing`, `Unit`·`UNIT`, `Opaque`, `Dyn`, `CottList`·`CottSet`·`FrozenMap`·`CottArray`·`CottBuffer`, numeric metadata, `JsonValue` union·variant와 `CottContractViolation`의 유일한 runtime identity 원본이다. ABI 7은 canonical struct construction/invariant, fixture adapter activation과 closed v7 generation snapshot validation을 포함한다. `Any`는 `typing.Any`, `Unknown`은 `object`, iterator protocol은 기존 direct Python typing projection을 쓴다. runtime ABI value가 expected ABI 7와 다르면 facade load는 실패한다.

Python environment 하나에는 generated cott project 하나만 설치한다. `cott_runtime`과 각 facade는 normalized `[project].name`, `[project].version`, runtime ABI 7를 embed하고 서로 다르면 import를 거부한다. `generated/python`은 public cott module, runtime과 verified local implementation copy를 함께 담는 단일 runtime/package root이며 `<module>_types.py`는 user type·constant만 정의한다.

`facade_exports(IR, resolved)`는 모든 public non-callable, resolved public free function, every selected slot이 explicit implementation, specialization 또는 verified trait default facade로 resolved된 impl class의 합집합이다. unresolved explicit sync/async impl method만 `generation.json.current.unresolved`에 기록한다. default/specialization-selected method에는 durable agent implementation source·record가 없다.

`impl Concrete for Trait [+ Trait ...]`는 agent가 class를 작성하는 기능이 아니다. emitter는 ordinary `@final` class, declaration-order state slot, `_cott_lock`, compiler-owned init과 selected sync/async method wrapper를 생성한다. explicit slot은 canonical helper를 call/await하고 default·specialization slot은 exact verified free-function facade를 receiver-first로 call/await한다. wrapper는 associated projection이 치환된 ABI, init/invariant, non-resource modifies와 resource transition checks를 적용한다.

`generation.json`은 두 snapshot을 가진다.

* `current`: 마지막 성공 emit/generate apply의 입력·구현·관리 파일 hash, unresolved 집합, `tools.cott_intent`와 `verified` 상태. 현재 emitted epoch baseline이다.
* `last_verified`: 마지막 full verify의 정규화 계약 snapshot, Python 공개 표면과 관리 파일 hash 또는 최초 검증 전 `null`. 역사적 certified baseline이며 current를 대체하지 않는다.

record의 필수 field를 보여 주는 다음 JSON은 객체·배열 entry 일부를 지면상 생략한 비규범 fragment이며, 그 자체로 schema-conformant record가 아니다. 실제 `contract_surface`와 `public_python_symbols`는 아래 규칙대로 축약 없이 저장한다.

```json
{
  "schema_version": 7,
  "current": {
    "generation_id": "sha256:...",
    "verified": false,
    "project_version": "0.1.0",
    "compatibility": {"generation_schema": 7, "canonical_ir_schema": 8, "runtime_abi": 7, "contract_strategy_schema": 5},
    "inputs": {"AGENTS.md": "sha256:...", "cott.toml": "sha256:...", "python/pyproject.toml": "sha256:...", "python/uv.lock": "sha256:...", "src/foo/bar.cott": "sha256:..."},
    "tools": {
      "compiler": {"version": "1.0.0", "executable": "/canonical/cott", "content_hash": "sha256:..."},
      "runtime": {"abi": "7", "version": "1.0.0"},
      "python": {"implementation": "cpython", "version": "3.14.6", "cache_tag": "cpython-314", "os": "darwin", "machine": "arm64", "platform": "macosx-15.0-arm64", "executable": "/canonical/python", "content_hash": "sha256:..."},
      "basedpyright": {"version": "...", "executable": "/canonical/basedpyright", "content_hash": "sha256:..."}
    },
    "ir": {"foo.bar": "sha256:..."},
    "contract_surface": {"foo.bar": {"declarations": [{"kind": "function", "name": "foo.bar.process_bar"}]}},
    "public_python_symbols": {"foo.bar": ["process_bar"]},
    "implementations": [
      {
        "cott_symbol": "foo.bar.process_bar",
        "owner": "agent",
        "python_symbol": "_cott_impl.foo.bar.process_bar:process_bar",
        "source_origin": "python/_cott_impl/foo/bar/process_bar.py",
        "runtime_origin": "generated/python/_cott_impl/foo/bar/process_bar.py",
        "content_hash": "sha256:..."
      }
    ],
    "dependencies": [
      {
        "name": "provider",
        "version": "10.4.0",
        "lock_artifact_hash": "sha256:...",
        "installed_metadata_hash": "sha256:...",
        "imports": {"provider.InputPayload": {"origin": "provider/InputPayload.py", "content_hash": "sha256:..."}}
      }
    ],
    "managed_files": {
      "generated/python/_cott_impl/foo/bar/process_bar.py": "sha256:...",
      "generated/python/foo/bar.py": "sha256:..."
    },
    "unresolved": [],
    "verification": null,
    "semantic_coverage": {
      "clauses": [],
      "summary": {"observed": 0, "unobserved": 0, "trust_declaration": 0, "unknown": 0},
      "policy": {"selected": 0, "passed": true, "violations": []}
    },
    "agent_runs": []
  },
  "last_verified": null
}
```

project-owned path는 project-relative POSIX path이고 dependency import origin만 distribution-relative POSIX path다. hash는 raw file bytes의 SHA-256 lowercase hex다. map key와 set-derived array를 정렬한 UTF-8 JSON으로 쓰며 file 끝 newline 하나만 둔다. `generation.json` 자체는 self-reference를 피하려고 `managed_files`에서 제외한다. `generation_id`는 canonical object `{"current": <normalized current>, "domain": "cott.generation.v7", "schema_version": 7}`의 hash이며 normalized current에서는 `generation_id`·`verified`·`verification`·`semantic_coverage`·`agent_runs`를 뺀다. coverage/policy는 semantic identity의 alternate source가 아니라 verification result이므로 generation identity를 바꾸지 않는다. `last_verified`는 pointer가 아니라 certified current snapshot의 deep copy다.

`current.tools.cott_intent`는 generation-7 identity를 바꾸지 않는 확장 metadata다. 닫힌 필드는 `version: 1`과 callable별 `hashes` map뿐이며 각 값은 `sha256:` digest다. fingerprint는 선택 context의 canonical JSON과 domain `cott.intent`를 hash한다. context는 `doc`, 적용된 rule과 그 base, 계약 상수, 참조 type, incoming scenario, retained generator rule 식별자를 포함한다. `cott_intent`가 없는 same-v7 record는 `current.contract_surface`와 현재 rule bytes에서 fingerprint를 derive한다. 부재를 fresh로 가정하지 않는다. `cott.toml` 또는 rules input hash 증거가 없거나 불일치하면 agent-owned source를 보수적으로 전부 invalidate한다. manifest-owned binding은 intent 변경으로 agent 작업이 되지 않는다.

`agent_runs`는 현재 agent implementation content hash와 일치하는 callable별 마지막 successful run만 담는다. 이후 emit·verify에서도 hash가 같으면 보존하고 agent 재생성 시 교체하며 user edit로 hash가 달라지면 제거한다. `current.unresolved`에 있고 authentic `AgentRun` hash가 일치하는 pending source는 emit과 checkpoint를 반복해도 기존 bytes를 유지하며 `generate`가 재생성할 때까지 그 소유권을 유지한다. path 또는 content hash가 기록과 다른 tampered agent file은 거부한다. 실패·폐기된 run과 무제한 history는 generation record에 누적하지 않는다.

implementation record의 `cott_symbol`은 free function 또는 `<module>.<Concrete>.<method>`이며 `python_symbol`은 file의 유일한 canonical contract function만 가리킨다. record kind는 `function`, `async_function`, `impl_method`, `async_impl_method` 중 하나이고 callable kind도 함께 기록한다. 같은 file의 private helper와 permitted `Final` constant는 별도 symbol·binding·facade export·provenance record를 만들지 않고 file 전체 `content_hash`로 함께 provenance된다. explicit async impl method에는 manifest binding이 없고 agent-owned exact `async def` helper만 허용된다.

canonical executable path와 binary hash를 포함하므로 `generation_id`는 같은 machine·tool installation의 generation instance identity이지 cross-machine reproducible build ID가 아니다. portable 비교는 Canonical IR, `contract_surface`, `public_python_symbols`, durable implementation content hash와 normalized lock·dependency identity를 사용한다. exact tool·runtime identity와 machine-specific constant를 embed한 managed artifact hash는 같은 target environment 안에서만 비교한다. `generation.json`은 machine-local state이고 wheel에 포함하지 않는다.

`dependencies`는 허용된 external import마다 normalized distribution name·version, 현재 platform에서 lock이 선택한 `lock_artifact_hash`, 관찰한 installed metadata content hash와 distribution-relative module origin·content hash를 기록한다. lock artifact hash는 기대값이고 immutable archive나 검증 가능한 installer receipt가 없는 MVP 설치 환경에서 installed bytes가 그 archive에서 왔음을 증명하지 않는다. 이 연결은 명시적 신뢰 선언이며 loader는 verify가 관찰해 고정한 installed bytes를 검사한다. dependency origin은 symlink가 아닌 regular file이어야 하며 uv cache가 설치한 hardlink는 허용하고 매 load에서 content hash를 재검사한다. generated module과 standard library는 제외하며 후자는 exact CPython provenance로 고정한다. 16.5.1의 verified Cott facade import도 external dependency가 아니며 implementation AST와 Canonical IR에 대해 별도로 검증한다. 그 밖의 project-local import는 허용하지 않는다.

`contract_surface`와 `public_python_symbols`는 축약 없이 필수다. 전자는 span·source path·implementation 정보를 제외하되 declaration kind·name·public, generic, resolved type shape, field·variant·default·constant value·refinement, ordered contract clause·effect, `doc`, annotation `name`/`argument`(compiler `cott.applied_rule` 포함)를 보존하는 module별 canonical diff projection이다. 후자는 15.4의 전체 target symbol을 module별로 정렬해 저장한다. `facade_exports`는 이 집합과 `implementations`·`unresolved`에서 결정적으로 유도하므로 별도 저장하지 않는다. 따라서 외부에 보관한 `last_verified` record만으로도 이전 artifact 없이 contract·documentation breaking 분류와 partial-generate surface guard를 수행할 수 있다.

`inputs`는 manifest, 모든 `.cott` source와 manifest가 참조하는 rules·target project metadata·존재하는 lockfile의 raw byte hash를 정렬해 담는다. `cott.toml`이 target manifest이므로 별도 숨은 설정은 없다.

실제 byte를 바꾼 `fmt`, `emit`과 부분 generate는 `current`를 새 emitted epoch로 두고 `current.verified = false`로 갱신하되 `last_verified`를 그대로 보존한다. full verify만 두 snapshot을 현재 세대로 함께 갱신한다. 파일 drift는 저장된 bit가 `true`여도 snapshot을 무효화하므로 cott와 배포 gate는 hash를 재계산한다. 이미 배포된 artifact는 `emit` 또는 `generate` 전까지 옛 계약을 유지한다.

---

### 16.2 타입 매핑

| cott | Python MVP ABI |
| --- | --- |
| `Bool` | `bool` |
| `I8` … `I64`, `U8` … `U64` | `cott_runtime.I*`·`U*` alias = `Annotated[int, CottInt(sign, bits)]` |
| `F32`, `F64` | `cott_runtime.F32`·`F64` alias = `Annotated[float, CottFloat(bits)]` |
| `Str` | `str` |
| `Bytes` | `bytes` |
| `Path` | `pathlib.Path` |
| `Unit` | `cott_runtime.Unit`과 singleton `UNIT` |
| `Never` | `typing.Never` |
| `Any` | `typing.Any` |
| `Unknown` | `object` |
| `Iterator[T]` | `typing.Iterator[T]` |
| `Generator[Y, S, R]` | `typing.Generator[Y, S, R]` |
| `AsyncIterator[T]` | `typing.AsyncIterator[T]` |
| `AsyncGenerator[Y, S]` | `typing.AsyncGenerator[Y, S]` |
| `Dyn[Trait]` | sealed exact `cott_runtime.Dyn[Trait]` wrapper |
| `Factory[Concrete]` | exact `type[Concrete]` generated class object |
| `List[T]` | invariant `cott_runtime.CottList[T]` |
| `Set[T]` | invariant `cott_runtime.CottSet[T]` |
| `Map[K, V]` | invariant `cott_runtime.FrozenMap[K, V]` |
| `Tuple[T1, ..., TN]` | native heterogeneous `tuple[T1, ..., TN]` |
| `Array[T, N]` | invariant `cott_runtime.CottArray[T, Literal[N]]` |
| `Buffer[N]` | invariant `cott_runtime.CottBuffer[Literal[N]]` |
| `Option[T]` | `Some[T] \| Nothing`; `Some(value=...)`, `Nothing()` |
| `Result[T, E]` | `Ok[T] \| Err[E]`; `Ok(value=...)`, `Err(error=...)` |
| 사용자 `enum E` | 모든 `E_<Variant>` frozen class의 `TypeAlias` union `E` |
| `struct` | `@dataclass(frozen=True, slots=True, kw_only=True)` |
| `trait` | inherited structural `typing.Protocol`; default는 verified free-function facade dependency |
| `specialize` | compiler-owned exact trait-slot selection |
| `impl` | compiler-owned `@final` ordinary slotted class; selected sync/async explicit/default/specialized method wrapper |
| `resource R` | generated `R_<State>` singleton state classes와 `R` union alias |
| `newtype` | 조건을 검사하는 명목 wrapper class |
| `alias` | type alias |
| `const` | `<module>_types.py`의 `Final[ABI type]` |
| `JsonValue` | `cott_runtime`의 고정 recursive tagged union |
| `external type Name` | `[target.python.external_types]`가 `Name`의 fully qualified Cott symbol을 Python `module:Qualname` projection에 join |
| `Opaque["tag"]` | invariant `cott_runtime.Opaque[Literal["tag"]]` |

Python projection table은 IR에 포함되지 않으며 generated alias는 `Annotated` CottExternal metadata를 유지한다. 누락·stale·non-external·malformed projection은 emit failure다.

`Factory[Concrete]` Python ABI 값은 exact generated `Concrete` class object뿐이다. instance, subclass, 다른 callable은 허용하지 않으며 validator는 object identity만 검사하고 init을 호출하지 않는다. `Concrete`의 compiler-generated init signature가 Factory callable signature다. 다른 module의 Python annotation은 `from <public cott facade> import Concrete`를 사용하며 `<module>_types`를 import하지 않는다.

다른 backend도 같은 semantic external declaration과 자체 manifest projection table을 join할 수 있다. Rust와 TypeScript table은 향후 확장 지점일 뿐 Python MVP에서 구현되거나 manifest에 허용되지 않는다.

`JsonValue`의 Python variant는 `JsonNull`, `JsonBoolean`, `JsonInteger`, `JsonFloat`, `JsonString`, `JsonArray`, `JsonObject`로 고정하며 union alias 이름은 `JsonValue`다. `Any`와 `Unknown` are preserved as declared Python ABI annotations; they are never inferred from a missing or incompatible annotation. `Unit()`은 singleton `UNIT`을 반환하고 모든 `Nothing()` 값은 같은 zero-payload variant끼리 동등하다.

모든 newtype 생성자는 alias를 해소한 carrier ABI를 모든 mode에서 검사하고 statically concrete `F32` path를 exact `float`에서 binary32로 normalize한다. public callable input·output의 statically concrete `F32`도 모든 mode에서 같은 처리를 한다. 그 밖의 public callable scalar runtime check가 활성화되면 exact `bool`·`int`·`float`·`str`·`bytes`, integer range와 `Str`의 surrogate 부재를 검사해 `bool`을 integer로, integer를 float로 받지 않는다. newtype carrier의 `Str` scalar 유효성은 생성자가 모든 mode에서 검사한다. `Path` runtime 값은 지원 platform의 exact `pathlib.PosixPath`여야 하며 user subclass는 거부한다.

표준 union variant는 `Ok(value=...)`, `Err(error=...)`, `Some(value=...)`, `Nothing()`으로 고정한다. 사용자 enum의 모든 variant도 keyword-only frozen class다. cott의 `BarError.InvalidPayload`와 `BarError.ServiceUnavailable`은 Python의 `BarError_InvalidPayload(reason=...)`, `BarError_ServiceUnavailable()`가 되고 `BarError`는 이 class들의 union alias다.

`Unit`, `Opaque`, nominal container, standard·`JsonValue`·사용자 enum variant, struct와 newtype의 concrete class는 모두 `@typing.final`이고 runtime validator도 exact class identity를 요구한다. trait `Protocol`만 member-presence 구조 검사를 사용한다.

alias 이름, trait `Protocol`, enum union alias와 underscore-delimited variant class, struct, newtype, impl class, public constant와 구현이 해석된 공개 free function은 facade가 re-export하는 IR-derived public Python symbol이다. compiler-synthesized `TypeVar`와 복수 bound 합성 `Protocol`은 private `_cott_` support name이며 export하지 않는다. payload·struct field와 impl state field의 선언 순서와 이름은 ABI다. `Result[Unit, E]`의 성공값은 `Ok(value=UNIT)`다. target symbol projection에서 이름 충돌이 나면 emit 전에 실패한다.

BasedPyright는 `Annotated[int, ...]`의 width 차이만으로 type을 구분하지 못하므로 cott static binding verifier가 implementation signature의 sign·width·precision metadata까지 비교한다. 일반 Python caller의 width 구분은 정적 증명으로 보고하지 않으며 활성 boundary의 value range 검사, `off`의 trust declaration으로 남는다. facade는 statically concrete `F32` path를 모든 mode에서 normalize하고 그 밖의 numeric range와 값은 구성된 validation mode를 따른다. `typing.NewType`은 runtime identity가 없으므로 사용하지 않는다.

`CottList`는 tuple-backed `Sequence`, `CottSet`은 frozenset-backed `Set`, `FrozenMap`은 private `MappingProxyType` 기반 read-only `Mapping`이다. `Tuple`은 wrapper가 아닌 native immutable heterogeneous Python tuple이며 tuple length와 each indexed ABI element를 재귀 검사한다. `CottArray`는 tuple-backed immutable `Sequence`이고 `CottBuffer`는 exact bytes-backed immutable `Sequence[int]`이며 validator는 declared `Literal` length와 원소/byte ABI를 확인한다. public boundary는 raw Python list/set/dict를 nominal wrapper로 암묵 변환하지 않는다.

nominal container equality는 같은 runtime class와 contents에 대해서만 성립하지만 native tuple은 Python tuple equality/hash semantics를 사용한다. compiler는 hash-key position의 모든 tuple component가 hash-stable일 때만 허용한다. `CottList`, `CottSet`, `FrozenMap`, `CottArray`, `CottBuffer`, struct, payload enum, standard union·`JsonValue` variant, `Unit`, `Opaque`, `Factory`는 hash-stable type이 아니다.

---

### 16.3 타입 검사

Python implementation은 compiler가 scratch에 만든 전용 BasedPyright config와 explicit `--project`로 검사한다. config의 `include`는 resolved free-function `_cott_impl/**/*.py`와 impl-method exact helper file set이며 compiler-owned generated root와 configured target environment의 deterministic `lib/python*/site-packages` directory는 import/type resolution용 `extraPaths`, tool-only stub root는 `stubPath`로 고정한다. target site-packages는 sandbox에 read-only로 mount된 locked environment 안에서만 해석한다. runtime·facade·`*_types`의 compiler-owned bytes는 emitter golden test와 cott static verifier가 검사하고 BasedPyright diagnostic 대상에는 넣지 않는다. user `pyproject.toml`의 BasedPyright 설정은 verification에 사용하지 않는다. static verifier는 compiler-owned impl class shell·slots·init signature와 each listed trait method union의 exact coverage를 IR과 비교한다. impl method helper file에는 canonical helper 하나만 top-level에 둘 수 있고 its name·`self` plus method parameter signature·return annotation은 exact ABI signature와 일치해야 한다; class definition, import-time executable code, a second helper, decorator, overload, dynamic attribute access와 placeholder는 거부한다.

locked external distribution의 generated stub이 concrete return type을 보존하면서 일부 member parameter를 `Unknown`으로 남기는 경우를 위해 `reportUnknownMemberType`만 끈다. 존재하지 않는 attribute, unknown argument·variable·return과 ABI mismatch 진단은 유지하며 external stub mismatch를 넘기기 위한 `typing.cast`는 concrete SDK return에서 declared external projection으로만 허용한다.

```json
{"typeCheckingMode": "strict", "reportInvalidTypeVarUse": "none", "reportUnknownMemberType": "none", "reportUnusedFunction": "none", "reportPrivateUsage": "none"}
```

manifest의 interpreter와 type checker executable은 shell 없이 canonical regular-file path로 실행하고 full version·content hash를 provenance에 기록한다. 설정된 interpreter가 CPython `>=3.14.6,<3.15` 범위가 아니거나 BasedPyright version이 `>=1.39.9`가 아니면 Python target 검증을 시작하지 않는다. compiler-owned config의 완화는 7장의 `reportInvalidTypeVarUse`, locked external stub의 partial member parameter를 위한 `reportUnknownMemberType`, 동적으로 load되는 private helper의 `reportUnusedFunction`, generated private bound Protocol의 `reportPrivateUsage`뿐이다. Cott static verifier와 remaining strict diagnostics가 exact contract signature, actual attribute absence, unknown value flow와 ABI를 계속 검사한다. source의 `type: ignore`·`pyright:` suppression과 checker command/config injection은 거부한다.

interpreter identity probe, BasedPyright version probe·검사 process와 그 runtime child는 compiler-owned containment 안에서 실행한다. 실제 project path는 보이지 않고 staging input, standard library와 locked distribution은 read-only이며 cache·temporary output만 scratch에 쓸 수 있다. network·device와 environment secret을 차단하고 compiler-version-fixed wall timeout, process·memory·open-file ceiling과 stdout·stderr 한도를 적용하며 종료 뒤 descendant를 모두 reap한다. 이 filesystem·process 격리를 강제할 수 없으면 검증을 시작하지 않는다.

다음 항목은 오류로 취급한다.

* 누락된 타입
* declared `Any`·`Unknown`과 누락되거나 incompatible annotation의 혼동
* 불완전한 제네릭
* Optional 오용
* 잘못된 override
* 반환 타입 불일치
* 미처리 union 분기

### 16.4 런타임 검증

런타임 검증은 설정으로 선택한다.

```toml
[target.python]
runtime_validation = "boundary"
```

| 항목 | `off` | `boundary` | `test-only` |
| --- | --- | --- | --- |
| verified loader와 embedded provenance | 항상 | 항상 | 항상 |
| statically concrete public callable `F32` exact type·ABI normalization | 항상 | 항상 | 항상 |
| newtype 생성자의 carrier 명목·scalar·중첩 ABI, `F32` normalization과 refinement | 항상 | 항상 | 항상 |
| compiler-owned impl init의 exact state assignment, lock, init `requires`·`ensures`와 post-init invariant | 항상 | 항상 | 항상 |
| sync/async impl method state snapshot, declared `modifies`, transition, successful normal return invariant | 항상 | 항상 | 항상 |
| cancellation의 exception containment 및 cancellation 뒤 invariant | 항상 | 항상 | 항상 |
| 미선언 `Exception` → `CottContractViolation` | 항상 | 항상 | 항상 |
| eager concrete public boundary type·numeric range | 신뢰 선언 | 런타임 검사 | test context에서 검사 |
| `Iterator`·`Generator` protocol/lifecycle | 신뢰 선언 | creation protocol만 검사 | test context에서 bounded lifecycle 관찰 |
| `AsyncIterator`·`AsyncGenerator` protocol/lifecycle | 신뢰 선언 | 모든 `__anext__`·`asend`·`athrow`·completion·`aclose` operation을 runtime에서 중재·검사 | 같은 operation enforcement와 configured bounded observation |
| 지워진 `TypeVar` 관계 | 정적 검사 | 정적 검사 | 정적 검사 |

free-function wrapper order는 고정한다: statically concrete argument `F32` ABI normalization → 활성 mode의 concrete input type·numeric range·refinement와 struct reconstruction/invariant → 모든 `requires`와 모든 applicable conditional `error` 기록 → sync implementation call 또는 async implementation coroutine의 direct `await` → return `F32` ABI normalization → 활성 mode의 concrete return type·numeric range와 struct reconstruction/invariant → allowed `Err` set·모든 recorded conditional error obligation·applicable guarded `ensures`. 서로 다른 conditional error가 동시에 applicable이면 implementation을 해석하기 전에 contract ambiguity다. async impl wrapper has the same sequence under the task-aware reentrant lock.

facade의 always-on ABI pass는 expected type에서 statically concrete `F32` path만 recursive traversal한다. 값이 반올림되면 같은 immutable cott carrier를 다시 만들며 raw Python container를 convert하지 않는다. 이 path의 shape mismatch는 `off`에서도 ABI violation이고 erased `TypeVar` 내부는 static-only다. 이와 별도로 newtype 생성자는 6.2의 carrier ABI와 refinement를 항상 재귀 검사한다.

validator는 alias를 해소하고 cott_runtime nominal class, struct·enum field, container element와 newtype refinement를 재귀 검사한다. ABI traversal has hard depth limit `64` and node limit `1024`, distinct from the contract-test candidate budget; an active nominal cycle is rejected, while memoized sharing of an already validated non-active object is accepted without re-traversal. `Dyn`은 sealed wrapper, exact compiler-owned concrete carrier, exact trait origin·specialization을 검사한다. trait Protocol member-presence는 non-`Dyn` structural boundary check일 뿐이다. `Never` 값은 항상 실패하고 `Opaque`는 wrapper identity와 literal tag를 확인한다. sync lazy protocol은 boundary에서 return object만 검사하고 consumption, yield/send, completion, `close`를 미리 실행하거나 전부 validated라고 주장하지 않는다. async lazy protocol은 `off`에서 신뢰 선언이고 다른 mode에서는 wrapper가 실제 operation마다 검사한다.

`test-only` context는 cott 계약 테스트 실행기만 활성화하며 일반 환경 변수로 켤 수 없다. `runtime_validation` 값은 emit 시 facade·wrapper bytes에 compile-time specialize되어 managed file hash에 포함된다. 설치된 runtime은 `cott.toml`, `generation.json`이나 environment에서 mode를 다시 읽지 않는다.

#### 16.4.1 검증 보증 등급과 bounded proof

Declaration syntax/name/type validity는 항상 checked다. target projection, implementation selection, bounded static proof, runtime verification, contract-test observation은 분리된 capability와 evidence entry다. missing runtime, sandbox, valid candidate, external provenance linkage, execution permission은 관련 evidence만 `미관찰` 또는 `신뢰 선언`으로 낮추며 valid declaration을 reject하지 않는다. unsupported formula 또는 fixed proof budget exhaustion은 bounded proof `unknown`이며 `미관찰`이나 신뢰 선언이 아니다. malformed syntax, unresolved name, invalid generic arity, impossible constant, invalid Opaque tag, inadmissible hash key와 static proof가 실제 반례를 찾은 contract는 hard error다.

bounded proof engine은 `bounded-dnf-difference-constraints` v2만 사용한다. refinement satisfiability와 unguarded `requires` conjunction consistency를 sound DNF difference-constraint theory로 증명한다. immutable field path와 `.len` path를 변수로 취급하고, `U64`를 포함한 모든 fixed-width integer domain을 checked wide-integer arithmetic으로 계산한다. 지원 atom은 boolean symbol 및 normalized `x - y <= c`의 equality·ordering뿐이며, nonlinear multiplication·division·modulo, floating-point, quantifier, SMT는 지원하지 않는다. configured proof node/branch budget과 fixed depth `128`, symbols `128`, atoms `1024`를 넘거나 지원하지 않는 formula는 `unknown`이며 proof가 아니다. `proved`는 sound proof, `disproved`는 counterexample과 함께 contract error, `unknown`은 unsupported formula 또는 budget exhaustion이다. An explicit impl method proves its own concrete method `requires`; a default- or specialization-selected slot proves the selected free function obligation instead and never duplicates it for the slot. 이 classification은 `verification.contract_proofs`에 static checker, runtime capability, contract-test entries와 분리해 기록한다.

| 등급 | 의미 | v1.0 예시 |
| --- | --- | --- |
| 정적 증명 | 실행 없이 결정적으로 검사 또는 bounded proof | public symbol, signature, variance/trait closure, guarded recursion, exact helper path; supported refinement/`requires`와 branch reachability의 `proved`; unsupported formula 또는 proof budget exhaustion의 `unknown` |
| 런타임 검사 | 실제 production mode의 실행 경계에서 검사 | eager ABI, canonical struct invariant, `requires`, refinement, allowed error, `ensures`, init/invariant/modifies/cancellation, async protocol operation |
| 테스트 관찰 | deterministic bounded valid case 또는 fixture scenario에서 확인 | pure sync/async callable, fixture-authorized effect scenario, configured prefix에서 관찰한 async protocol operation |
| 미관찰 | 실행 observation capability가 없어 실행 증거 없음 | finite recursive candidate 없음, depth/node/lifecycle limit exhausted, unavailable Linux isolated-loopback |
| 신뢰 선언 | 자동으로 증명/관찰하지 않음 | hidden effect, off-mode optional boundary check, effectful callable without executable scenario, archive-to-install linkage |

automatic input generator uses IR hash and callable FQN seed, at most configured `candidate_limit` candidates, container length 0–3, recursive `JsonValue` depth 4, recursive nominal node budget 64 and configured strategy lifecycle budget. It allocates only productive terminating recursive branches. Factory has no source literal, and `Dyn` requires a compiler-owned initialized concrete case; without one the clause is `미관찰`. impl method instantiates recorded `init_cases` in source order; an impossible required state candidate is `미관찰`. Struct candidate that fails its canonical invariant is discarded deterministically rather than being mistaken for an implementation failure.

automatic contract tests execute pure sync/async free functions and impl methods whose resolved transitive effect set is empty and whose return is not `Never`, each in a separate deny-by-default OS sandbox. A valid fixture-authorized scenario additionally executes its selected effectful facade. For `AsyncIterator`/`AsyncGenerator`, the pure runner uses the same per-operation wrapper enforcement, observes at most `lifecycle_limit` actual operations, checks send/yield ABI and contract evidence, and calls `aclose` when available. The configured prefix is an observation budget, not a lifecycle-enforcement boundary. effectful or `Never` callable without such a scenario remains `신뢰 선언` or `미관찰`; the runner does not import a facade solely to execute it.

For each requires-valid generated case the runner records `eligible_cases`, `applicable_cases`, `satisfied_cases`, `condition_false_cases` and deterministic first witness for every success/conditional-error obligation. It evaluates every conditional-error predicate; when several apply, only the source-order first clause must match the returned `Err`, while lower clauses retain condition/applicability counts without contradiction or satisfaction. An `Err` never satisfies an Ok obligation. A pure callable with valid cases but no observed Ok leaves each success obligation as stable `unobserved` evidence with its exact counters and no fabricated witness; default verification does not reject it solely for that absence. The required top-level Ok success-obligation lint remains, and semantic coverage policy can deny selected unobserved clauses, including always-Err implementations. Zero valid cases remains unobserved. Proof reports success-region and conditional-error reachability as `proved`/`disproved`/`unknown`, but never upgrades implementation coverage. contract report retains exact ids/spans and separate proof/runtime/test evidence.

`CottContractViolation`은 `Exception`의 하위 타입이며 `cott_runtime`에서 import한다. `symbol`, `phase`, clause `span`, expected·actual summary와 original `Exception` cause를 보존한다. verified loader의 identity·origin·hash preflight 실패도 target 호출 전에 `phase = "provenance"`인 이 exception으로 발생한다. facade exception boundary는 lazy load·symbol lookup과 invocation 전체를 감싼다. existing contract violation은 재포장하지 않고, module load `Exception`은 `implementation-load`, implementation `Exception`은 invocation violation으로 변환한다. `CancelledError` is re-raised after the async wrapper's cancellation invariant handling; other `BaseException` is not captured.

진단과 JSON 검증 결과에는 구성된 mode에서 각 계약 항목이 실제로 얻은 보증 등급과 separate evidence를 포함한다.

---

### 16.5 기존 구현 바인딩

라이브러리를 구현 내부에서만 사용한다면 cott에 등록하지 않는다. Python 구현에서 일반적으로 import하고 package와 version은 `pyproject.toml` 및 기존 lockfile로 관리한다.

Binding is optional implementation selection, not a second contract language or an authority over a declaration. 기존 Python 함수가 cott **free function**을 직접 구현할 때만 대상별 binding을 선언한다. impl method는 compiler-owned state shell의 일부이므로 manifest binding할 수 없고 agent helper로만 해석한다. Binding이 없으면 function은 unresolved이며 agent 또는 later implementation 대상이 될 수 있다.

```toml
[target.python.implementations]
"foo.data.load_payload" = "my_project.adapters.provider:load_payload"
```

키는 cott free function의 완전한 이름이고 값은 Python `module:function_name`이다. `<module>.<Concrete>.<method>` key는 configuration error다.

#### 16.5.1 바인딩 해석과 시그니처 호환성

manifest에 binding key가 있으면 해석 실패는 hard error다. 잘못된 binding을 미구현 함수나 agent 생성으로 대체하지 않는다.

manifest binding key는 현재 IR의 public free function을 정확히 가리켜야 하며 impl method key, stale·duplicate key는 configuration error다.

`cott check`, `cott emit`, `cott generate`, `cott verify`는 Python source와 stub을 import 없이 정적으로 해석한다. 타입 판정은 이번 transaction에서 staging에 생성한 `*_types.py`를 기준으로 한다.

**free-function binding** target은 regular `.py`에 선언된 decorator 없는 top-level function 또는 `async def`와 simple function name으로 제한한다. callable kind는 Cott declaration과 exact match해야 한다: async binding은 coroutine function이어야 하고 sync binding은 coroutine일 수 없다. overload, variadic parameter와 descriptor, extension·zip·custom loader는 거부한다. Python generator function은 sync `Generator[Y, S, R]` ABI와 호환될 때만 허용한다. implementation file의 canonical callable 하나는 exact name·signature를 가지며 same-file private helper는 synchronous fully annotated function만 허용한다.

target과 Python-local helper에서 optional docstring을 제외한 body가 `pass` 또는 `...`뿐인 placeholder, value placeholder로 대입·반환하는 `...`, `NotImplementedError`를 직접 발생시키는 코드는 정적 해석 단계에서 거부한다. 일반 `.py` type annotation의 `tuple[T, ...]`와 `.pyi` stub의 ellipsis는 placeholder가 아니다.

static verifier는 module 전체 AST의 import를 수집한다. generated `cott_runtime`·`*_types`, CPython standard library와 lockfile에 고정된 external distribution 외 project-local composition은 Canonical IR에서 derive한 compiler-generated Cott facade·parent package namespace로 제한한다. exact generated facade 또는 그 package prefix는 absolute `import <module> [as alias]`와 `from <parent> import <child> [as alias]`로 사용할 수 있고, exact facade의 non-private symbol은 alias 없는 direct import로 사용할 수 있다. generated value type annotation은 `from <module>_types import Type`을 사용한다. impl helper의 `self` concrete와 `Factory[Concrete]` identity는 generated facade 어디에서 re-export되더라도 static signature·runtime identity probe로 exact class임을 재확인하며 generated type module에서 concrete class를 가져오는 것은 거부한다. underscore-private facade symbol, star·relative import, 모든 `_cott_impl` import, Canonical IR에 없는 project-local module, `importlib`·`__import__` 등 dynamic import, `eval`·`exec`·`compile`, `builtins`·`__builtins__` reflection과 `__file__`·`__path__`·`__spec__`·`__loader__`·`__package__` 의존도 거부한다. 같은 정책을 optional helper를 포함한 file 전체에 적용하고 missing public name은 BasedPyright와 runtime signature probe가 거부한다.

target annotation은 exact builtin `bool`·`str`·`bytes`, `pathlib.Path`, imported generated type, `cott_runtime` ABI alias, `typing.Never`·`Literal`과 cott generic parameter를 조합한 `Name`·`Attribute`·subscript·union AST만 허용한다. explicit string-literal annotation, user type alias와 annotation call은 거부한다. `from __future__ import annotations`만 future import로 허용하고 runtime verifier는 static AST 검사가 끝난 module에 `typing.get_type_hints(include_extras=True)`를 적용한다. generic function은 module-level `T = TypeVar("T", bound=...)`의 invariant form만 허용하며 name·bound를 cott generic parameter와 구조적으로 비교한다.

runtime signature probe는 implementation마다 별도 CPython process로 16.4.1과 같은 deny-by-default sandbox를 먼저 적용한 뒤 staged generated copy를 verified loader로 import하고 `typing.get_type_hints(include_extras=True)`만 수행하며 target function은 호출하지 않는다. 이 규칙은 effect 유무와 관계없이 모든 binding·agent implementation에 적용하며 sandbox를 강제할 수 없으면 검증을 시작하지 않는다.

external top-level package는 installed `.dist-info` file inventory에서 lock의 한 distribution에 유일하게 귀속되어야 한다. namespace package, 여러 distribution이 같은 top-level package를 제공하는 경우와 inventory 밖 origin은 MVP에서 거부한다.

local binding의 top-level package는 public cott package, `cott_runtime`, `_cott_impl`, CPython standard library와 locked distribution의 top-level package에서 분리해야 한다. target까지의 source parent `__init__.py`는 없거나 compiler가 생성한 빈 파일이어야 한다. 이 규칙으로 generated copy의 canonical module name과 initialization semantics를 고정한다.

binding 함수는 cott 함수와 다음 항목이 정확히 같아야 한다.

* 매개변수 개수, 순서, 이름과 positional/keyword kind
* 기본값이 없는 매개변수
* 각 매개변수와 반환값의 명목 Python ABI 타입
* 숫자의 부호·폭·정밀도 metadata
* `Result` 오류 타입

cott 함수 매개변수에는 기본값이 없다. 기본값이 필요한 API는 options struct field로 표현한다. 추가 선택 인자는 직접 binding하지 않지만 declared `Any`·`Unknown`은 각각의 Python ABI mapping으로 signature compatibility를 검사한다. 선언된 `effects`는 16.4.1의 신뢰 선언이다.

binding 여부와 관계없이 각 public cott free function은 독립 symbol로 해석·signature 검사·생성·검증하며, 각 impl method도 독립 symbol로 agent 생성·검증한다. 다른 free function을 facade로 호출해도 두 free function을 하나의 binding이나 생성 단위로 합치거나 helper 구현을 caller에 inline하지 않는다.

```text
foo.bar.process_bar
→ <target.python.source>/_cott_impl/foo/bar/process_bar.py
→ _cott_impl.foo.bar.process_bar:process_bar

foo.bar.Counter.increment
→ <target.python.source>/_cott_impl/foo/bar/Counter/increment.py
→ _cott_impl.foo.bar.Counter.increment:_cott_impl_Counter_increment
```

free-function implementation resolution priority는 optional manifest binding → 위 exact agent file → unresolved다. manifest-owned binding은 intent fingerprint 변경으로 agent 작업이 되지 않는다. compatible agent file이 이미 있고 intent fingerprint가 같으면 재사용하고 agent를 호출하지 않는다. intent fingerprint가 바뀌었거나 selected generate에서 agent file이 없거나 signature가 현재 contract와 불일치하면 regeneration candidate로 staged overwrite할 수 있다. pending unresolved이며 authentic `AgentRun`이 있으면 기존 source를 유지한다. path·hash가 기록과 다른 tampered file은 거부한다. binding 불일치는 항상 hard error며 agent로 대체하지 않는다. impl method resolution priority는 exact agent helper file → unresolved뿐이다; compatible helper가 없거나 name/signature가 다르거나 intent가 stale이면 regeneration candidate고 manifest binding은 언제나 hard configuration error다.

compiler가 필요한 `_cott_impl/**/__init__.py`를 side-effect 없는 빈 파일로 생성한다. free-function agent와 impl-method agent는 선택 function file만 쓰며, 그 file에는 exact Cott symbol/signature의 canonical function 하나와 0개 이상의 위 private helper·permitted literal `Final` constant만 둘 수 있다. helper는 manifest binding, `generation.json` implementation symbol, facade와 `__all__`의 대상이 아니며 public behavior가 되면 별도 Cott function으로 승격한다. impl helper의 instance method coordination은 `self.<declared_method>(...)` public wrapper를 통해서만 한다.

binding target은 공개 facade와 달라야 한다. 외부 API가 계약과 다르면 사용자가 typed adapter를 작성한다. cott는 인자·예외 변환을 추측하지 않는다.

MVP binding target은 `target.python.source` 아래 module로 제한하고 project 밖 function을 직접 binding하지 않는다. 외부 API 함수를 Cott 계약과 다르게 호출해야 할 때만 project-local typed adapter가 import하며 16.1의 dependency provenance 규칙을 적용한다. MVP binding 대상은 함수로 제한하지만 external Python struct·enum·object는 `[target.python.external_types]` projection으로 해석한 declared `external type`으로 계약 경계를 직접 통과할 수 있다. Python projection이 필요하지 않은 foreign identity에는 12.5의 `Opaque`를 사용한다.

---

### 16.6 공개 facade와 구현 경계

호출자는 구현 위치와 관계없이 항상 compiler-generated Cott module 경로를 사용한다. implementation이 다른 project-local function을 호출할 때는 16.5.1의 exact public function import를 사용하고, annotation·constructor·Factory class object는 generated facade 또는 `<module>_types`의 verified symbol을 사용한다.

```python
from foo.bar import process_bar, validate_bar
```

이 composition은 Python implementation boundary에만 존재한다. `.cott`는 계속 실행 body·call-expression syntax 없이 function별 계약을 선언하는 contract-first language다.

cott는 `generated/python/foo/bar.py`에 fully typed free-function wrapper와 impl마다 compiler-owned ordinary class 및 public method wrapper를 생성한다. `bar_types.py`가 module 고유 type identity의 원본이고 standard ABI identity는 `cott_runtime`에 있다. implementation과 adapter는 custom value type을 우선 type module에서, standard type을 `cott_runtime`에서 import하며 Factory concrete나 facade가 이미 가져온 verified support symbol은 generated facade namespace로 참조할 수 있다. project-local function call은 declared public free function만 대상으로 하며 direct implementation symbol을 import하지 않는다. same-file private helper와 `Final` constant는 Cott declaration도 facade export도 아니며 `_cott_impl`을 import하지 않는다; canonical function과 private helper는 같은 file 안에서만 서로 직접 호출할 수 있다. impl canonical function의 cross-contract method call은 own `self`의 declared public method만 호출할 수 있다. imported Cott free function 또는 that public method call은 generated wrapper를 통과하므로 its own provenance, ABI, `requires`, return/error와 `ensures` 검사가 configured mode대로 각각 적용된다.

각 free-function wrapper와 impl class/method wrapper에는 project identity·expected `cott_runtime` ABI version, compile-time specialized `runtime_validation`, implementation의 canonical module·symbol, `generated/python` relative `runtime_origin`·content hash, exact CPython full version·cache tag·OS family·architecture와 16.1의 external dependency record를 immutable constant로 embed한다. impl class shell additionally embeds ordered state layout, defaults, init/invariant and method `modifies` metadata; helper symbol is `<module>.<Concrete>.<method>`. full `sysconfig` platform string은 generation provenance에만 둔다. durable `source_origin`은 `generation.json`에만 남고 verify가 generated copy와 byte identity를 확인한다. installed package에 project-side record가 없어도 검사는 동작한다.

`cott_runtime` verified loader는 먼저 facade와 runtime의 project identity·ABI version 및 embedded CPython full version·cache tag·OS family·architecture가 현재 runtime과 같은지 확인하며 OS point version은 비교하지 않는다. CPython patch version mismatch도 거부하며 16장의 재생성·재검증이 필요하다. 구현별 process 최초 resolution은 ordinary import보다 먼저 자신의 package 위치에서 generated root를 정하고 embedded `runtime_origin`을 no-follow로 열어 exact bytes의 hash와 provenance를 검사한다. 성공하면 canonical module name으로 단 하나의 module object를 만들고 실행 전에 `sys.modules`에 등록한 뒤 검증한 bytes 자체를 compile·execute한다. 실패하면 등록을 되돌린다.

이미 같은 canonical name이 `sys.modules`에 있으면 cott loader registry가 동일 object·origin·hash를 앞서 검증한 경우에만 재사용하고, 일반 import로 먼저 실행된 module은 거부한다. 검증된 symbol cache는 runtime origin과 `generation.json`의 regular-file identity·size·mtime·ctime을 함께 기록한다. 이후 같은 process의 호출은 이 두 stamp만 비교하며, 어느 하나라도 바뀌면 cache를 버리고 exact bytes hash·provenance preflight를 다시 수행한다. 이 stat fast path는 정상 호출의 file read·hash·JSON parse를 피하는 성능 최적화이며 metadata 위조를 방어하는 보안 경계는 아니다. process-global registry와 load transition은 canonical name별 reentrant lock으로 보호해 concurrent caller가 같은 module object 또는 같은 실패를 관찰하게 한다. 구현 module 직접 import는 지원 API가 아니다. custom loader, relative import 또는 실행이 필요한 parent `__init__.py`는 MVP에서 거부한다. compiler-owned empty parent package만 만들며 검증된 symbol을 cache한다.
implementation에서 import한 cott facade도 compiler-owned generated root에서만 해석하며 source root나 `_cott_impl`로 fallback하지 않는다. facade call chain의 각 edge는 해당 wrapper의 verified-loader 경계를 다시 통과한다.

cache miss 또는 stamp drift의 loader preflight는 target 실행 전에 recorded direct external module의 distribution identity·version·regular module-relative origin·content hash를 import 없이 확인하고, 이미 load된 module의 `__file__` origin이 다르면 실패한다. 이 preflight는 preloaded module이 과거에 같은 bytes로 실행됐거나 distribution의 transitive file·standard library 전체가 변조되지 않았음을 증명하지 않는다. external execution은 lockfile packaging과 exact CPython installation에 대한 신뢰 선언으로 보고한다.

`runtime_validation`은 16.4 표의 optional free-function/method ABI와 contract checks만 제어하며 provenance loader, impl init/state snapshot/invariant/modifies checks를 끄거나 직접 implementation re-export로 바꾸지 않는다. 구현 위치와 mode가 달라도 facade callable의 signature와 module identity는 같다.

`target.python.source`는 compiler input과 durable implementation root일 뿐 runtime import path가 아니다. 이 root에는 cott public module, compiler-owned `*_types` 또는 `cott_runtime`을 정의할 수 없다. runtime·BasedPyright는 generated root 뒤에 standard library와 locked distribution만 사용하고 stub root는 runtime path에서 제외한다. Python build는 모든 local runtime file을 generated root에서만 포함한다. independent installed-wheel whole-origin verification과 package installation은 v1.0 범위에서 제외하고 post-v1.0 roadmap으로 남긴다. v1.0에서는 embedded provenance check, 즉 exact metadata와 실제 imported regular-file origin·content hash의 preflight를 필수로 한다.

해석된 public free function과 every emitted impl class만 facade와 `__all__`에 포함한다. 미구현 free function 또는 impl method에는 placeholder를 만들지 않고 `current.unresolved`에 기록하며, unresolved method가 있는 impl class 자체도 emit하지 않는다. `cott verify`는 unresolved pending이 하나라도 있거나 verified facade projection이 전체 IR과 다르면 실패한다. 현재 facade에 없는 옛 managed implementation은 export하지 않는다.

### 16.7 Facade 우회 감사

계약 runtime entry point는 generated public facade뿐이다. compiler는 `PythonArtifactPlan` 뒤 binding/emission 전에 authored `target.python.source` tree를, type/proof/runtime 실행 전에 staged/current deployed artifact tree를 각각 AST로 감사한다. 두 tree 모두 lexical-relative regular single-link `.py`만 허용하며 parent/file symlink, non-regular file, Unix hardlink를 거부한다. dependency site-packages는 provenance 대상이지만 이 project-boundary scan 대상은 아니다.

| 대상/형태 | authored tree | deployed tree |
| --- | --- | --- |
| generated public facade의 exact public symbol import | 허용 | compiler-owned facade에서만 허용 |
| standard library·locked external distribution import | 허용 | runtime/facade 필요분만 허용 |
| exact manifest binding source | binding role로만 허용 | 없음 |
| exact hashed `_cott_impl/**/<callable>.py` loader origin | 없음 | generated implementation role로만 허용 |
| `import`/`from`/alias로 `_cott_impl` 또는 `cott_bindings` | 거부 | 거부 |
| literal `__import__`, `importlib.import_module` 또는 aliased equivalent로 private target | 거부 | 거부 |
| computed/unknown dynamic import target | 거부 | 거부 |
| `_cott_impl`·`cott_bindings` public re-export, `__all__` 노출 | 거부 | 거부 |

검사는 static import, `from`/alias, literal dynamic import와 unknown dynamic target을 rustpython AST/source range로 분류한다. comment/string은 대상이 아니며 first failure에서 멈추지 않는다. 모든 violation은 normalized path, source range, kind 순으로 정렬해 반환한다. `cott_bindings`는 authored binding location일 뿐 public package가 아니고 `_cott_impl`은 loader-only implementation storage다. generated facade는 path/hash verified loader를 사용하며 implementation module을 import/re-export하지 않는다. staged artifact에는 generation record가 허용한 exact runtime origin/hash 이외의 `_cott_impl` 또는 어떤 `cott_bindings`도 존재할 수 없다.

### 16.8 Fixture sandbox와 관찰 경계

fixture scenario는 fresh compiler-owned scratch 하나에서 serial로 실행한다. fixture setup 전에 facade import를 막고 authorization을 설치하며, setup → local endpoint start → facade invocation → clause/assertion observation → task/server stop → root inspection → delete/absence check 순서를 항상 지킨다. import root와 locked distribution은 read-only이고 fixture root만 writable이다. audit hook은 fixture root 밖 filesystem, active endpoint 외 socket/DNS, subprocess, process exit, dynamic code를 거부한다. direct time read는 CPython audit event가 아니므로 runtime clock adapter 밖의 clock access는 observed evidence가 아니라 bypass/unsupported diagnostic이다.

filesystem entry는 descriptor-relative no-follow creation으로 materialize하고 byte/file ceiling을 streaming 중 적용한다. HTTP는 sandbox의 compiler-owned loopback listener 한 개만 사용하며 exact route·relative redirect·body/request/redirect ceiling을 적용한다. transcript는 bounded source-order logical event `{seq, fixture, operation, relative_path|route, outcome, byte_count, occurrence}`만 담고 port, absolute root, PID, host duration, directory iteration order, raw exception은 담지 않는다. failure counter는 scenario-local이며 import/setup/cleanup은 occurrence를 소비하지 않는다. atomic replace evidence는 same fixture directory의 old-or-absent before, observed successful `file.replace`, exact after, declared temporary path absence를 모두 요구한다; injected flush/replace failure에는 old bytes와 cleanup absence가 모두 남아야 한다.

network mode는 `Disabled` 또는 `IsolatedLoopback`이다. 후자는 host network enable이 아니라 Linux bubblewrap network namespace 안에서 compiler-owned listener에만 connect/listen할 수 있다는 뜻이다. external interface·DNS·다른 local port는 계속 deny다. Linux+bubblewrap에서 loopback namespace를 실제로 establish하지 못하면 verification은 `effectful scenario fixtures require supported Linux bubblewrap isolation`으로 unobserved를 남기고 fail closed한다. macOS/Windows, missing/old bubblewrap도 같은 unavailable outcome이며 unsandboxed fallback, trust-to-observed downgrade, external service fallback은 없다. timeout·read/limit error에는 complete sandbox process group을 terminate하고 setup error·assertion failure·exception·cancel·timeout·success 모두에서 cleanup한다. cleanup failure는 success를 override한다.

### 16.9 Semantic coverage 정책

`verified`는 artifact/type/runtime/proof/runner verification이 성공하여 snapshot을 certify했음을 뜻하고, semantic coverage CI policy와 별개다. Canonical IR clause inventory `(symbol, kind:clause_id, span)`와 runner contract evidence의 one-to-one join만 coverage truth source다. normalized status는 positive valid-case `test observation`의 `observed`, `unobserved`, `trust declaration`, 그리고 missing/duplicate/contradictory/unrecognized evidence의 `unknown` 네 가지뿐이다. doc, generator rule, log, proof outcome, rerun은 `unknown`을 repair하거나 grade를 승격할 수 없다.

`[[verification.coverage.rules]]`는 exact canonical callable `symbol`, nonempty sorted-unique `clauses=["ensures:2","error:5"]`, 그리고 `allow_unobserved`, `allow_trust_declaration`, `allow_unknown` boolean만 가진 deny-unknown policy다. duplicate `(symbol, clause)` selection, invalid selector/qname와 empty clause list는 manifest error다. rule이 없으면 selected clause도 gate도 없다. selected clause는 manifest allowance가 없을 때 해당 status로 deterministic violation이 되고 unselected clause는 gate하지 않는다.

verify는 모든 evidence를 먼저 finalize하고 `current.verified=true`, closed `semantic_coverage={clauses,summary,policy}`와 `last_verified`를 atomic publish한다. 그 뒤 policy violation이면 verification certification을 되돌리지 않고 sorted violation과 coverage summary를 출력하여 distinct exit code `8`로 실패한다. policy passed이면 ordinary verify success다. runtime loader는 artifact `verified`만 보고 project coverage policy를 재평가하지 않는다. 따라서 policy-failed yet artifact-verified snapshot도 loadable이며 policy를 runtime의 두 번째 truth boundary로 만들지 않는다.

### 16.10 유지 example generation-first policy

작성된 inventory는 Python project 26개, Kotlin project 20개, Dart/Flutter project 1개다. Python set은 grammar
6개(`checked-add`, `assignment-rule`, `cta-row`, `fractional-range-values`, `portfolio-cost`,
`stock-record`), simple 3개(`alphabetical-file-groups`, `calculator`, `decimal-binary`), 순수
complex curriculum `artifact-pipeline`, 별도 full-generation fixture `process-bar`, focused
feature 7개(`declarations-generics`, `contracts-evidence`, `boundary-protocols`, `trait-protocol`,
`json-transform`, `effects-selection`, `workflow-scenario`), multi-module `order-management`,
FastAPI external projection `fastapi-hello`, real-world generation-first 6개(`real/yt-dlp`,
`real/harlequin`, `real/pgcli`, `real/posting`, `real/toolong`, `real/frogmouth`)다.
`examples/kotlin/`에는 19개 Kotlin lesson/fixture가 있고 `integrations/android-counter`는
Kotlin/JVM module과 standard Android consumer다. `integrations/flutter-counter`는 Dart module과
standard Flutter consumer다. `process-bar`는 curriculum count에 넣지 않는다.

유지되는 curriculum module의 source order는 type 선언, 작은 domain leaf function, 더 큰 composition function, domain-named final operation 순서다. 의미 있는 경계만 stage로 공개한다. grammar lesson은 의도적으로 leaf 하나일 수 있고 simple·complex lesson도 domain responsibility가 독립적인 경우에만 stage를 추가한다. `artifact-pipeline`은 순수 topological artifact-plan composition이고, `process-bar`는 `foo.bar` 전체의 unresolved-to-agent-generation 전환을 집중적으로 보이는 fixture다.

real project는 각자 독립 generation-first example이며 project API version은 `0.1.0`이다. adapter는 exact generated public facade만 사용하고 implementation·binding을 직접 import하거나 public re-export하지 않는다. 각 real project README의 H1은 canonical upstream URL이고, 다음 generation phase 뒤 verified generated artifact를 commit한다. binding은 essential host boundary인 `real.yt_dlp.transfer_media`, `real.harlequin.core.run`, `real.posting.client.send_request`, `frogmouth.document.load_document`에 각각 1개만 허용하며 나머지 real project의 binding은 0개다.

`.cott` declaration은 항상 bodyless다. free-function composition edge는 `from <exact cott module> import <declared public function>` 형태의 alias-free import로 exact generated public facade를 통과해야 하며 implementation file끼리 직접 호출하지 않는다. same-file private helper call은 implementation detail이고 impl canonical function의 only cross-contract method composition edge는 `self.<declared_method>(...)` public wrapper다. effect verifier는 caller와 same-file helper가 도달하는 Cott facade callee의 declared effects를 transitive하게 검사한다; external/stdlib operation은 declaration의 trust boundary로 남는다. helper가 Cott로 승격되어 public function이 되면 모든 ABI-valid input에 선언된 결과를 반환하거나 caller가 호출 전에 확립할 수 있는 Cott `requires`를 선언해야 한다.

`checked-add`는 manifest binding syntax를 집중적으로 가르치는 lesson이다. 구현 선택은 항상 각 project의 `[target.python.implementations]`과 generation record가 정한다. Binding은 compatible project-local implementation을 선택할 뿐 Cott contract를 정의하지 않으며, example마다 binding 또는 agent implementation을 임의로 일반화해서는 안 된다. checkout에 commit된 `generated/`는 compiler-owned result이고, agent-owned free-function `python/_cott_impl/<cott module>/<function>.py` 및 impl-method `python/_cott_impl/<cott module>/<Concrete>/<method>.py`는 matching `agent_runs` provenance가 있는 실제 `cott generate --agent <agent> --target python` 성공 결과다. `.venv/`, `.cott/`, `__pycache__/`는 transient이며 managed artifact나 evidence가 아니다.

`cott emit python|kotlin|dart`는 선택 target의 compiler-owned output과 unresolved metadata만
materialize하며 agent나 target compiler를 호출하지 않는다. `cott generate`는 선택
target의 eligible unresolved callable에만 durable source를 생성한다. 필요한 implementation
selection과 managed artifact가 모두 일치해야 explicit `cott verify`가 certify한다. 유지되는
Python example은 generic `run` function, forwarding alias, direct
implementation-to-implementation call, duplicated validation, nominal-wrapper-only helper를
금지한다.

`generate -j <jobs>`는 callable을 stable source-order wave로 최대 `jobs`개씩 실행하고
callable별 progress를 stderr에 기록한다. 한 generate 호출의 초기 prompt와 `prompt_hash`는
invocation 시작의 immutable resolution snapshot만 사용한다. 이후 wave candidate는 validation에만
쓰인다. Agent 또는 final bundle validation이 실패해도 source audit를 통과한 candidate는
`current.verified = false` checkpoint로 publish하고 exit `5`를 유지한다. 다음 generate는
unresolved callable만 재개한다. 성공한 generate도 certification이 아니며 explicit verify만
`verified = true`를 publish한다.

## 16A. Kotlin/JVM 17 module 대상

### 16A.1 닫힌 manifest와 source ownership

한 manifest는 `[target.python]`, `[target.kotlin]`, `[target.dart]` 중 정확히 하나만 가진다.
선택이 없거나 복수이면 configuration error이고 target mismatch는 tool 실행 전에 거부한다.
Kotlin table의 실제 field는 다음과 같다.

```toml
[project]
name = "example-module"
version = "0.1.0"
source = "src"

[target.kotlin]
source = "kotlin"
generated = "generated/kotlin"
compiler = "kotlinc"
java = "java"
jvm_target = 17
runtime_validation = "boundary"
classpath = ["libs/runtime-dependency.jar"]
compile_only = ["sdk/android.jar"]

[target.kotlin.implementations]
"example.module.callable" = "cott_bindings.example.callable"

[target.kotlin.external_types]
"example.module.PlatformValue" = "android.os.Bundle"
```

`source`, `generated`, `runtime_validation`은 필수다. `compiler`, `java`, `jvm_target`의 default는
각각 위 값이며 JVM 17 이외의 값은 거부한다. `generated`는 정확히
`<artifact-root>/kotlin` 형태다. `classpath`와 `compile_only`는 duplicate/overlap이 없는
normalized project-relative regular `.jar` path 목록이고 둘 다 compiler input으로 hash한다.
`classpath`는 runtime dependency이고 `compile_only`는 compile-time symbol만 제공하므로 배포하지
않는다. `[target.kotlin.external_types]` key는 declared external Cott FQN, value는 Kotlin FQN이다.
`[target.kotlin.implementations]`는 Cott callable FQN을 target source tree의 Kotlin
package/function FQN에 연결하는 binding table이며 Cott contract를 정의하지 않는다.

Manifest binding source는 `<target.kotlin.source>/` 아래에서 사용자가 소유한다. Agent source는
`<target.kotlin.source>/cott_impl/<module path>/<function>.kt`, method면
`<module path>/<Concrete>/<method>.kt`에 지속된다. Resolver는 symlink, non-regular file,
hardlink와 unsafe UTF-8 path를 거부하고 package, 하나의 canonical `internal` top-level function,
exact sync/`suspend` signature, permitted private helper, source/runtime origin, content hash, owner와
intent fingerprint를 감사한다. 미구현 callable과 소유권이 확인된 intent-stale agent source는
unresolved다. 기록되지 않거나 이동·변조·manifest-shadowed 상태인 agent source는 오류로
거부하며 이전 record에서 trust를 갱신하지 않는다. Manifest binding은 intent regeneration
대상이 아니지만 exact source bytes와 signature 검사를 통과해야 한다.

Audited implementation은 wildcard import, process 종료와 검증 관찰·제어 API 접근을 거부한다.
`CottRuntime` object를 값으로 전달하거나 보관할 수 없고, 승인된 ABI·수학·snapshot API만 직접
호출할 수 있다. Import alias가 승인된 runtime member 이름을 가리는 것도 거부한다. Manifest,
contract, implementation과 generator rules의 input hash는 실제 해석에 소비한 bytes에서 나온다.
Generator rules는 project load에서 한 번 읽어 freshness, prompt, retry와 publication에 공유하고,
publication 전 입력 drift가 확인되면 기존 output과 동시 편집을 그대로 보존하며 거부한다.

### 16A.2 emit, generic ABI와 public module

Kotlin public package는 Cott module FQN과 같고 identifier spelling을 보존해 필요한 경우 Kotlin
backtick escaping만 한다. 각 module의 compiler-owned output은 `Types.kt`와 `Facade.kt`이고
standard ABI는 `kotlin/cott_runtime/CottRuntime.kt`와 `CottMarkers.kt`가 제공한다. Resolved
implementation은 generated `kotlin/cott_impl/` copy로 들어가며 public consumer는 Cott module의
public facade만 import한다. `cott_bindings`와 `cott_impl` package는 public import/re-export
path가 아니다. Gradle consumer는 compiled JAR를 dependency로 사용하므로 Kotlin `internal`
implementation visibility는 module boundary에서 유지되며 raw generated source를 app source set에
합치지 않는다.

Alias는 transparent, newtype은 nominal, struct는 immutable, payload enum은 sealed, trait는
associated generic parameter가 포함된 interface로 projection한다. Associated projection은
additional bounded Kotlin type parameter로 lift하고 concrete impl assignment는 override 전에
concrete type으로 치환한다. Abstract associated generic과 ordinary `T`에는 blanket runtime
witness를 추가하지 않고 reflection이나 phantom `CottAssociated<Base, Marker>` wrapper도 쓰지
않는다.

JVM은 const generic parameter도 erase하므로 free const generic에는
`_cott_const_<NAME>: cott_runtime.CottConst` value-witness parameter를 public facade와 internal
helper signature에 넣는다. 값 metadata에서 복구할 수 없는 constructor에도 witness가 있다.
`U8|U16|U32|U64` kind/range와 exact mathematical value는 witness `.value`로 검사하며 contract의
free-N expression도 그 값을 사용한다. Explicit canonical const value도 같은 의미의 value
witness다. Canonical IR을 바꾸거나 witness를 silent omission하지 않는다.

`cott emit kotlin`은 agent, kotlinc, Java 또는 user code를 실행하지 않는다. Current IR,
runtime, facade, implementation copy와 `generation.json`을 transaction으로 publish하되 unresolved
callable facade와 placeholder/stub은 만들지 않는다. `emit ir`은 IR scope와 record만 갱신한다.
두 emit과 `generate --target kotlin`은 언제나 `current.verified = false`, `verification = null`로
publish하고 historical `last_verified`를 보존한다.

### 16A.3 compilation, runtime evidence와 certification

Kotlin generation record는 Python record와 구별되는 closed object다. Top-level
`schema_version = 1`; snapshot은 `target = "kotlin"`, compiler package `1.0.0`, Canonical IR
`8`, runtime ABI `1`, `public_symbols`, target symbol/source/runtime origin, managed file hash,
tools, evidence와 semantic coverage를 사용한다. Domain은 `cott.kotlin.generation.v1`이다.
Python `public_python_symbols`, `python_symbol`, generation v7 또는 runtime ABI 7을 Kotlin
truth로 재사용하지 않는다.

오직 `cott verify`만 Kotlin snapshot을 certify한다. Verify는 unresolved가 없고 current
source/manifest/implementation input 및 emitted managed source가 expected bytes와 일치해야
시작한다. 실제 kotlinc-jvm `>=2.2.10`, JDK `>=17`, compiler-matched stdlib, bundled
`kotlinx-coroutines-core-jvm` exactly `1.8.0`, manifest `classpath`와 `compile_only` identity를
확인한다. Source와 모든 compiler/JAR input을 read-only로 제공하고 scratch write, bounded
process/output/time/memory, sanitized Java environment와 default-disabled network를 적용하는
기존 sandbox 안에서 `-jvm-target 17 -Xjdk-release=17 -no-reflect`로 library를 compile한다.
Unsandboxed fallback은 없다.

실제 compile/runtime classpath에 넣는 JAR는 nonempty manifest `Class-Path`를 거부하여 기록되지
않은 transitive JAR를 로드하지 않는다. JDK manifest parser의 folded·case-insensitive attribute
처리와 multi-release logical class 검사를 적용한다. 단순히 identity를 기록하는 compiler
distribution 전체를 application classpath로 취급하지는 않는다.

Verifier는 real `library/cott-module.jar`와 bounded contract runner JAR를 별도로 compile하고
runner가 public facade를 실제 호출한 event만 evidence로 받는다. Canonical IR clause inventory,
bounded proof, derived strategy, actual eligible/applicable/satisfied case와 scenario trace를 closed
semantic-coverage join에 보존한다. Unsupported formula/budget exhaustion은 `unknown`, 실행
capability 또는 concrete candidate 부재는 `unobserved`이고 어느 것도 success로 바꾸지 않는다.
Ordinary `T`와 abstract associated generic은 JVM에서 erased되므로 arbitrary per-call runtime
unification을 주장하지 않는다. Runner가 concrete bounded type argument를 생성할 수 없거나
abstract associated projection만 있으면 실제 관찰을 만들지 않는다. Concrete associated
assignment와 const witness가 있는 path만 해당 concrete descriptor/value를 검사한다.

Runner event는 매 실행 새로 만든 256-bit key와 HMAC-SHA256으로 인증한다. Key는 one-way stdin
pipe로만 전달하고 trusted runner가 candidate 실행 전에 전부 소비한다. Sequence와 exact JSON
payload를 함께 인증하며 host는 순서, MAC과 authenticated final completion을 검사한다.
Key는 stdout, environment, command-line argument나 artifact에 노출하지 않는다. Candidate의 일반
stdout은 evidence authority가 아니고, public prefix를 흉내 낸 JSON과 exit `0`만으로 인증할 수 없다.

Full verification이 성공하면 `library/cott-module.jar`와 exact compiler-distribution coroutine
JAR를 `runtime-libs/kotlinx-coroutines-core-jvm.jar`로 managed publish하고 complete evidence를
기록한다. Kotlin stdlib version/hash는 required dependency로 기록하지만 Kotlin compiler 또는
Android Gradle plugin이 제공하므로 두 번째 copy를 bundle하지 않는다. Certification은
`current.verified = true`와 `last_verified == current`를 함께 atomic publish하는 verify-only
transition이다. Emit, generate 또는 실제 fmt 변경은 current를 unverified로 만들고 history만
유지한다. Coverage policy violation은 evidence와 certified snapshot을 보존한 채 exit `8`로
gate하고 deploy는 passed policy를 요구한다.

### 16A.4 deploy와 Android consumer 경계

Kotlin deploy는 verified, fully resolved, policy-passed, non-drifted current snapshot을 새
directory에 atomic no-replace 방식으로 package한다. Payload는 다음뿐이다.

```text
cott-module.jar
dependencies.json
generation.json
runtime-libs/
├── kotlinx-coroutines-core-jvm.jar
└── <verified target.kotlin.classpath JAR copies>
```

`dependencies.json` schema 1은 project identity, JVM target, module path/hash, Kotlin stdlib
provided dependency, 각 runtime library의 path/hash와 coroutine version을 기록한다. `.cott`,
manifest, authored Kotlin source, original generated layout, tests, compiler/JDK, Android SDK와
`compile_only` JAR는 배포하지 않는다. Cott deployment는 JAR publication이지 APK/AAB
publication이 아니다.

`cott init <path> --target kotlin`은 bodyless Cott module, Kotlin implementation root, closed
Kotlin manifest와 `.gitignore`만 만든다. Android app, Gradle build, UI, resource 또는 manifest를
scaffold하지 않는다. `--no-sync`가 없으면 installed Kotlin/JDK toolchain을 probe할 뿐 download나
Python/uv 작업을 하지 않는다.

`examples/integrations/android-counter`는 standard Gradle consumer와 Cott module을 명시적으로
분리한다. Cott source/binding lifecycle은 다음과 같다.

```bash
project=examples/integrations/android-counter
cott check --project "$project"
cott fmt --check --project "$project"
cott emit kotlin --project "$project"
cott verify --project "$project"
cott deploy --project "$project" --output dist/android-counter-module
```

Android project는 AGP `9.0.1`(bundled Kotlin `2.2.10`), compile/target SDK `36`, min SDK `26`,
JVM 17을 사용한다. 개발
중 repository binary를 쓰는 build는 official Gradle `9.1.0` distribution SHA-256
`a17ddd85a26b6a7f5ddb71ff8b05fc5104c0202c6e64782429790c933686c806`을 pin한 wrapper와
`COTT_BIN` override를 사용한다.

```bash
COTT_BIN="$PWD/target/debug/cott" \
  "$project/android/gradlew" --project-dir "$project/android" --no-daemon :app:assembleDebug
```

Gradle task가 verified module을 별도 directory에 deploy하고 `cott-module.jar`와
`runtime-libs/*.jar`만 dependency로 연결한다. Kotlin stdlib는 Android Gradle plugin이 제공하며
같은 coroutine library를 app graph에서 다시 선언해 duplicate class를 만들지 않는다. App source는
`example.counter.increment`와 `example.counter.decrement` public facade만 import한다. 독립 native
JVM consumer는 deployed module로 compile/run되어 `increment(0) == 1`,
`decrement(100) == 99`, invalid `increment(100)` rejection을 확인했고 두 callable의 여섯 clause에
unknown/unobserved 없이 observation이 기록되었다. 같은 pinned Gradle build는 debug APK를
assemble해 AOSP API 36 software emulator에 설치했고 UI의 bounded counter에서 `0 → 1 → 0`
전이를 관찰했다. 이는 software-emulator evidence이며 physical-device 성공 주장은 아니다.

Cott가 소유하는 범위는 Cott module compile/verify/deploy다. Standard Gradle/Android가 Kotlin UI,
`AndroidManifest.xml`, resource, application dependency graph, DEX, APK/AAB assembly, signing,
installation과 device lifecycle을 소유한다. Android device에서 Python을 실행하는 경로는 없다.

## 16B. Dart package와 Flutter consumer

### 16B.1 닫힌 target과 라이브러리 경계

Dart는 package `1.0.0`, Canonical IR `8`, generation schema `1`, domain
`cott.dart.generation.v1`, runtime ABI `1`을 사용한다. `DartGenerationRecord`는 별도의 closed
validator를 통과하며 Python/Kotlin record를 baseline이나 runtime identity로 받지 않는다.

```toml
[project]
name = "flutter_counter"
version = "0.1.0"
source = "src"

[target.dart]
source = "dart"
generated = "generated/dart"
sdk = "dart"
runtime_validation = "boundary"
# 의존성이 있는 module만 함께 지정한다.
# pubspec = "dart_package/pubspec.yaml"
# lockfile = "dart_package/pubspec.lock"

[target.dart.implementations]
"example.counter.increment" = "cott_bindings/counter/increment.dart:_increment"

[target.dart.external_types]
"example.counter.Moment" = "dart:core#DateTime"
```

Project name은 Dart package의 lowercase snake_case identifier다. `source`, `generated`,
`runtime_validation`은 필수이고 `sdk` default는 `dart`다. Output은 `<artifact-root>/dart`다.
Optional pubspec/lockfile은 함께 지정하는 normalized project-relative metadata이며
implementation source, output, rule 및 reserved cache 경계와 충돌할 수 없다.

Manifest binding은 `<target.dart.source>/<relative.dart>:<private function>`을 선택한다.
Agent는 `cott_impl/<module>/<function>.dart`에 exact prompt signature를 작성하며 method는
concrete owner path를 포함한다. Top-level private function과 허용된 typed private helper만
작성하고 library/part/export directive나 public replacement facade는 작성하지 않는다.
Tree-sitter AST가 signature, import prefix, callable reference, helper reachability, explicit
witness, owner/path/hash/intent를 검사한다. Compiler-private identifier는 `_cott_` namespace이며
exact canonical function/witness 외 접근, computed receiver를 통한 control 접근도 거부한다.

작성된 source에서 import와 body를 AST 범위로 분리하고 compiler가 `part of`를 넣는다.
Authored source hash와 managed part hash는 다르다. Public import는
`package:<project>/modules/<module path>.dart`, ABI 값은 `package:<project>/cott_runtime.dart`다.
Free wrapper는 callable별 library이며 stateful owner와 method wrapper/parts는 같은 private
library에 둔다. 공개 setter/schema로 state나 seal을 우회할 수 없다.

### 16B.2 정확한 Dart ABI

I8/I16/I32/U8/U16/U32는 범위 검사한 Dart `int`, I64/U64는 `BigInt`다. Contract 정수 연산은
수학적 BigInt 값으로 수행하여 native overflow와 web 53-bit 손실을 피한다. F32/F64는 finite
`double`이며 F32는 binary32 rounding을 적용한다. String은 Unicode scalar를 검사한다.
Unit, Option, Result, JsonValue, Path와 immutable container는 구별되는 Cott ABI 값이다.
Runtime은 Dart standard library만 사용하며 Flutter 의존성을 갖지 않는다.

Aliases, refined nominal newtype, struct/default/invariant, payload enum, trait/associated type,
concrete impl/default/specialization, const witness, Factory/Dyn/Opaque와 protocol을 같은 IR에서
투영한다. Dart generic reification만으로 Cott 정수폭·F32 구별이나 invariant/contravariant 관계를
복구할 수 없으므로 필요한 API에는 명시적인 `CottType<T>` witness가 있다. Generic nominal은
private carrier와 seal-bound typed view를 사용한다. Cott descriptor 관계를 검사한 뒤 새 typed
view를 만들며 원래 Dart covariant carrier를 억지로 cast하지 않는다. Multiple bound도 모두
검사한다. Const parameter는 `CottConst` witness를 사용한다.

Recursive descriptor forwarding은 값 graph edge가 아니며 별도 cycle/depth guard로 해석한다.
Value graph의 active cycle·depth·node 제한, shared DAG identity, immutable snapshot과 deep
equality를 보존한다. Nonconstant struct defaults는 private omission marker와 runtime constructor
검증으로 처리한다. Cott 함수 parameter default나 enum payload default 문법을 추가하지 않는다.

Async callable은 `Future<T>`다. Iterator/Generator 및 async protocol은 typed callback source와
명시적인 next/send/return/raise/close lifecycle을 사용하며 단순 Stream으로 정보를 버리지 않는다.
CancellationSource/TaskScope는 cooperative token과 명시적 owned task만 관리한다. Guard와 mutation
capability는 exact live lease를 요구하고 종료 시 revoke한다. Zone 상속으로 reentrant ownership을
부여하지 않는다. 임의 Future가 preempted되었다는 evidence는 생성하지 않는다.

### 16B.3 Frozen dependencies와 source identity

Manifest, contract, Dart source, generator rules, pub metadata는 실제 소비한 bytes를 한 번 고정해
hash한다. Initial prompt, retry, binding freshness와 publication은 같은 rule/dependency authority를
사용한다. 재읽은 새 bytes로 오래된 구현을 fresh로 바꿀 수 없다. Missing authentic source는
unresolved로 남고 current implementation/run identity만 제거한다. Moved, tampered, unrecorded
source는 실패한다. 성공한 provider의 source-audited candidate도 target 검증 실패 후에는
authenticated pending repair source로 남을 수 있지만 resolved/certified로 자동 승격하지 않는다.

Stdlib-only module에는 authored pub metadata가 필요 없다. 의존성이 있으면 pubspec name/version은
Cott project와 일치해야 하고 root/transitive declaration의 source kind, registry/name 또는
declaring-package-relative path와 전체 Dart/pub version constraint를 lock과 비교한다.
Prerelease/build 정보를 버리는 근사 비교, dependency override, project 밖 path는 허용하지 않는다.
허용 package import 집합은 frozen production/transitive closure에서만 오며 dev-only·미선택
package나 external type projection 자체는 import authority가 아니다.

Hosted package는 원본 locked archive를
`PUB_CACHE/hosted-archives/<registry-cache-key>/<name>-<version>.tar.gz`에 명시적으로 준비한다.
Cott는 compressed archive SHA256을 lock과 대조하고 size/member/expansion 한도 안에서
link/traversal/duplicate/special-file을 거부하며 archive tree와 extracted cache를 비교한다.
수정 가능한 hosted-hashes sidecar만으로 처음 본 tree를 신뢰하지 않는다. Archive가 없으면 필요한
경로와 locked identity를 진단하고 verify는 다운로드하지 않는다. Project-local path package도
해석한 정확한 tree를 snapshot에 포함한다. 원래 archive/tree는 private frozen material이며
portable record에 absolute cache path를 넣지 않는다.

Dependency record는 `{schema_version:1,pubspec_hash,lockfile_hash,packages}`다. 각 package에는
`name,version,source,source_identity,content_hash,dependencies,runtime`만 있고 이름/edge는 sorted,
unique, closed다. Hosted source_identity는 HTTPS registry와 locked archive SHA256, path는
normalized project-relative origin이다. Compiler-owned pubspec은 exact runtime vendor paths를
사용하고 `publish_to: none`이다. Flutter solver가 다른 transitive 코드를 몰래 선택하지 않는다.

### 16B.4 실제 검증과 process-memory 경계

`verify`는 SDK `>=3.13.3,<4.0.0` identity와 expected source/managed bytes를 검사하고 기존 sandbox
안에서 offline enforced pub resolution, strict Dart analyzer, facade kernel과 bounded runner
kernel compilation을 수행한다. Depfile로 실제 compiler input 경계를 확인한다. Native runner는
public facade만 호출하며 structured candidates, constructor/method/protocol 및 finite
filesystem·isolated-loopback HTTP scenario의 실제 결과를 기록한다. Genuine construction/budget/
observation 부재만 unknown/unobserved다. Malformed schema, 내부 renderer error, 잘못 생성된 코드,
실패한 clause를 unobserved로 바꾸지 않는다. Implicit safety guard를 없는 IR clause로 꾸미지 않는다.

Runtime 실행은 bubblewrap 안의 single-threaded compiler launcher에서 Landlock ABI `>=3`을 먼저
설치한 뒤 Dart VM을 exec한다. SDK/system/package는 read-only, scratch는 필요한 write만 허용하고
VM stack bounds에 필요한 정확한 `/proc/self/maps` file만 procfs rule로 연다. Self/thread-self
memory, environ, cmdline의 sync/async 접근은 거부된다. 후속 VM thread는 제한을 상속한다.
Landlock은 기존 descriptor를 revoke하거나 anonymous pipe magic link 전부를 금지하는 기능이
아니다. 따라서 source의 process/stdio/control 접근도 감사하고 key pipe는 candidate 전에 소진한다.
지원되지 않는 kernel이나 policy 설치 실패에는 unsandboxed fallback이 없다.

Fresh 32-byte key는 one-way stdin으로만 전달하고 trusted runner가 candidate 실행 전에 읽는다.
HMAC-SHA256은 sequence의 big-endian u64와 exact UTF-8 JSON을 함께 인증한다. Host는 MAC,
순서, closed event inventory와 final done을 검사한다. Key는 source, argv, environment,
artifact나 stdout에 저장하지 않는다. Pinned crypto `3.0.7`의 필요한 원본 source와 LICENSE는
compiler-only private support이며 사용자 package가 shadow하거나 deployment에 포함하지 않는다.

Emit과 generate는 항상 unverified다. Explicit verify만 complete evidence/coverage와
`current == last_verified`를 atomic publish한다. Selected coverage policy 실패는 인증 evidence를
보존하며 exit `8`로 gate한다. No unresolved/drift와 passing policy가 deployment 조건이다.

### 16B.5 Portable deployment와 Flutter

Dart deployment는 새 directory의 `lib/`, compiler-owned `pubspec.yaml`, unchanged
`generation.json`, `dependencies.json`, exact runtime `vendor/` closure다. Private part 경로를
보존한다. `verification/cott-module.dill`은 native 검증용이지 portable Flutter library가 아니므로
배포하지 않는다. 계약·원래 generated layout·authoring copy·runner·SDK·cache·추론한 app asset도
제외한다. Flutter는 deployed directory를 path dependency로 가져와 자신의 platform용으로 compile한다.

`examples/integrations/flutter-counter/tool/setup.dart`는 emit/verify/no-replace deploy 후 Flutter
pub get을 실행한다. App은 public `example.counter` facade만 사용한다. Flutter `3.47.4`/
Dart `3.13.3`의 browser에서 `0 → 1 → 0`와 `0..100` 경계를 확인했고 module의 여섯 clause는
observed다. Android/web platform scaffold, UI, plugin, resource, DEX/APK/AAB, signing, 배포와
device lifecycle은 Flutter/Gradle 영역이며 Cott는 Flutter app scaffolder가 아니다.

---

## 17. 에이전트 코드 생성 흐름

### 17.1 생성 입력

선택된 agent는 target별 implementation을 작성한다. Unresolved callable은 선언된 `Any`,
`Unknown`, external type, iterator/protocol 또는 recursive `Opaque` 때문에 자동 제외되지 않지만
Cott body를 추가하거나 contract를 약화하거나 기존 target code를 semantic authority로 취급할 수
없다.

1. 생성 대상 callable의 Canonical IR과 원본 `doc`
2. 사전 조건·사후 조건·오류 조건·부작용
3. 선택 target language/ABI 규칙과 project coding rule
4. explicit reference·`constant_ref`·applied rule/base·incoming scenario로 닫힌 transitive context
5. free function의 target binding identity와 read-only authenticated reference source
6. pending 대상의 existing durable source
7. impl method의 concrete/state/init/invariant/`modifies` 정보와 canonical helper signature
8. target별 external projection과 dependency context

callable prompt는 AUTHORITY, CURRENT INTENT, FORMAL DECLARATIONS, PROJECT RULES, REFERENCE
IMPLEMENTATIONS, target OUTPUT RULES, retry의 VALIDATION FEEDBACK을 분리한다. Formal declaration이
sole semantic authority이고 다른 prose/source는 이를 override하지 않는다. Python write path는
`implementation.py`, Kotlin은 `implementation.kt`, Dart는 `implementation.dart`다. Output rules는
각 target의 exact signature, generic/const witness와 public/private import boundary를 포함한다.
한 generate invocation의 모든 초기 prompt는 같은 frozen reference snapshot을
사용하고 accepted wave candidate는 validation에만 쓴다. `cott prompt` JSON은 target과 무관하게
`{symbol, intent_hash, prompt_hash, generation_required, context, prompt}`다.

초기 CURRENT INTENT의 관련 `doc`은 닫힌 선언 집합에서 오며 applied rule `doc`을 authored `doc`에
합쳐 semantic constraint로 승격하지 않는다.

### 17.2 에이전트 선택 및 호출

`cott generate`는 미구현 callable을 생성할 때 사용자가 `--agent`로 지정한 에이전트를 사용한다. cott는 모델 제공자 API를 직접 호출하거나 에이전트를 자동 선택하지 않는다.

MVP는 다음 세 가지 direct agent adapter와 각 adapter가 제공하는 CLI 인터페이스만 지원한다. `claude`는 Claude Code를 직접 호출하는 adapter다. OMP 안에서 Claude model을 선택해도 그 실행은 여전히 `omp`이며 `claude` adapter가 아니다.

| `--agent` 값 | 호출 인터페이스 |
| ------------- | --------------- |
| `codex`       | `codex exec`    |
| `claude`      | direct `claude` (Claude Code) |
| `omp`         | `omp -p`        |

cott는 17.1의 target-specific 입력을 하나의 callable별 구현 지시로 구성해 선택 interface에
전달한다. Binding된 symbol은 다시 구현하지 않는다. Python composition은 exact generated facade,
Kotlin composition은 exact public Cott package를 사용하고 private implementation package를
import하지 않는다. Impl method는 supplied canonical helper만 작성하고 compiler-owned
class/init/wrapper/state declaration을 만들지 않는다. Same-file private helper는 canonical function의
hashed implementation detail이고 public behavior가 되면 Cott declaration으로 승격한다.

`codex`, `claude`, `omp` 밖의 `--agent` 값은 에이전트를 호출하기 전에 오류로 거부한다.

#### 17.2.1 에이전트 실행 계약

선택 범위의 미구현 callable은 fully qualified symbol 정렬 순서로 처리한다. `-j <jobs>` (또는 `--jobs`)는 1..=64이며 기본값은 1이다. 기본값에서는 callable별 agent process를 순차 실행한다. 더 큰 값에서는 최대 `jobs`개의 callable을 정렬된 wave로 함께 실행한다. 모든 초기 prompt와 `prompt_hash`는 generate 시작의 한 immutable resolution snapshot에서 렌더한다. 이후 수락한 candidate는 다음 wave의 validation에만 쓰이며 광고된 초기 prompt를 바꾸지 않는다. 성공한 candidate는 symbol 순서로 merge한다. agent 또는 final validation 실패는 isolated workspace를 정리하지만, source audit를 통과한 candidate는 `current.verified = false` checkpoint로 publish하고 exit `5`를 유지한다. 다음 generate는 unresolved만 재개한다. `agent_runs`에는 최종 검증 성공 run만 이 실행 순서로 남긴다.

각 에이전트 adapter는 실행 파일, prompt 전달 방식, 작업 디렉터리, 환경 변수, 종료 상태를 명시한다.

compiler release마다 adapter별 minimum supported CLI version과 exact argv template를 고정한다. v1.0은 Codex CLI `>=0.147.0`, Claude Code CLI `>=2.1.89`, OMP `>=17.2.12`를 허용한다. executable은 `PATH`에서 한 번 resolve한다. version preflight는 main generation과 별개다. Claude는 probe를 실행하기 전에 canonical regular-file executable이 `cli.js`이거나 Node shebang을 가지면 거부한다. npm `cli.js` entrypoint는 허용하지 않으며 official native Claude Code installation이 필요하다. Claude probe의 exact argv는 `claude --version`이고 shell 없이 별도 argv로 실행한다. 이 probe는 credential(기존 `ANTHROPIC_API_KEY`를 포함)을 전혀 받지 않고 network가 disabled된 containment에서 실행하며 timeout 없이 status `0`으로 끝나야 한다. stdout 전체는 valid UTF-8의 정확히 하나인 strict SemVer token이어야 하고 그 값은 `>=2.1.89`여야 한다. version output이 해석 불가능하거나 minimum version보다 낮으면 본 실행 전에 실패한다.

v1.0의 exact main-process argv template는 다음과 같다. 각 항목은 shell 재해석 없이 별도 argv다. `<workspace>`·`<scratch>/omp.yaml`·`<seconds>`·`<absolute-prompt-file>`만 run별 값으로 치환한다.

* Codex: `codex exec --strict-config --ephemeral --ignore-user-config --ignore-rules --skip-git-repo-check --sandbox workspace-write --color never --cd <workspace> -`; prompt bytes는 stdin으로 전달한다.
* Claude: `claude --bare --print --input-format text --output-format json --permission-mode dontAsk --tools Read,Write --allowedTools Read,Write --disallowedTools Bash,Edit,Glob,Grep,WebFetch,WebSearch,Task,mcp__* --no-session-persistence`; exact UTF-8 prompt bytes는 stdin으로 전달하고 child cwd는 isolated workspace다.
* OMP: `omp -p --cwd <workspace> --no-session --no-rules --no-skills --no-extensions --no-lsp --no-pty --no-title --tools read,grep,glob,edit,write --approval-mode yolo --max-time <seconds>s --config <scratch>/omp.yaml @<absolute-prompt-file>`; compiler는 OMP 본 실행 전에 exact prompt bytes를 workspace 밖 scratch의 create-new regular file에 쓰고, 그 absolute path 앞에 `@`를 붙인 마지막 단일 argv로 전달한다.

다음 environment allowlist는 main generation process에만 적용하며 version preflight에는 적용하지 않는다. 공통 environment name은 `HOME`, `PATH`, `PYTHONDONTWRITEBYTECODE`, `TMPDIR`이며 host에 존재할 때만 `SSL_CERT_FILE`, `SSL_CERT_DIR`, `HTTPS_PROXY`, `HTTP_PROXY`, `NO_PROXY`를 추가한다. Codex는 존재하는 `CODEX_API_KEY`, `CODEX_ACCESS_TOKEN`, `CODEX_HOME`만, Claude는 존재하는 `ANTHROPIC_API_KEY`만, OMP는 존재하는 `PI_CODING_AGENT_DIR`만 추가한다. Claude에는 항상 `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1`, `DISABLE_TELEMETRY=1`, `DISABLE_ERROR_REPORTING=1`도 설정한다. Claude에는 OAuth, auth-token, base-url, cloud, provider, customization 관련 environment name을 전달하지 않는다. 그 밖의 host environment는 전달하지 않는다.

* shell을 사용하지 않고 executable과 각 인자를 분리하여 실행한다.
* main process 실행 전에 executable의 canonical regular-file path, version과 content hash를 기록한다. Claude native-entrypoint rejection은 위와 같이 `claude --version` probe 전에 수행한다.
* 작업 디렉터리는 17.4의 격리된 staging workspace다.
* 실제 project root는 agent sandbox namespace에서 보이지 않는다. 대상 계약, 직접 참조 helper 계약, 필요한 binding·rule·기존 구현과 compiler-owned facade는 staging의 read-only copy로만 제공하고 현재 implementation file과 별도 scratch directory만 쓸 수 있다. Codex credential path와 OMP native-addon cache만 project 밖에서 read-only로 열며, OMP의 `config.yml`과 `agent.db`는 매 실행 scratch로 복사하고 원본 credential directory는 열지 않는다. 이 sandbox를 강제할 수 없는 platform에서는 agent generate를 거부한다.
* prompt는 shell 문자열로 조합하지 않는다. Codex와 Claude만 stdin을 사용하며, OMP의 prompt file은 workspace mutation audit 범위 밖의 scratch에만 둔다.
* 환경 변수는 compiler version에 고정된 adapter별 name allowlist만 전달한다. secret value는 기록하지 않고 전달한 name만 기록한다.
* `PYTHONDONTWRITEBYTECODE=1`을 설정하고 `TMPDIR`, type checker·test cache와 agent 임시 상태를 scratch directory로 보낸다.
* `[generator].timeout_seconds`는 1–3600이며 default는 900이다. 모든 agent child는 compiler-owned process containment에 넣는다. parent가 정상 종료해도 남은 descendant를 전부 종료·reap하고 containment가 비었음을 확인한 뒤에만 candidate path를 staging workspace handle 기준 `O_NOFOLLOW`로 열어 regular file·`st_nlink == 1`인지 `fstat`으로 확인하고 읽는다. 그 밖의 file kind, 사용자 취소·timeout·비정상 종료나 descendant 정리 실패는 transaction을 폐기한다.
* containment에는 compiler version이 고정한 process·CPU·memory·open-file·writable-byte ceiling을 적용하고 candidate implementation file은 최대 1 MiB로 제한한다. 어떤 ceiling이라도 넘으면 agent 실패다.
* stdout·stderr는 끝까지 drain하며 전체 byte count·SHA-256와 truncation 여부를 계산하고 사용자에게 stream별 최대 1 MiB만 보여 준다. generation record에는 raw output을 넣지 않고 이 metadata, exit code, 실행 시간, adapter·executable path·version·content hash·prompt hash만 남긴다.

에이전트가 0이 아닌 상태로 종료되거나 timeout되면 staging과 scratch 변경을 폐기한다. stdout의 code block은 구현으로 채택하지 않으며 허용된 implementation file의 최종 bytes만 후보 입력이다. compiler는 그 후보의 끝 LF를 정확히 하나로 정규화한 뒤 검증·hash·publication하며 그 밖의 bytes는 바꾸지 않는다. 0으로 종료해도 target callable이 없거나 file이 바뀌지 않아 unresolved면 실패한다.
Claude adapter는 stdout이 JSON object이고 `type`이 `result`, `subtype`이 `success`, `is_error`가 `false`, `result`가 string인 경우에만 성공으로 받아들인다. JSON parse 또는 어느 field 검증이든 실패하면 fail closed한다. Claude provider process의 network egress는 기존 agent와 같이 enabled 상태로 남지만, 위 argv는 network-capable Claude tool을 하나도 노출하지 않는다.
agent가 file을 썼지만 candidate static validation에 실패하면 compiler는 기존 candidate bytes와 누적된 exact validation diagnostic을 같은 callable prompt에 넣어 최대 두 번 추가 실행한다. 각 retry 전 isolated target만 지우고 workspace·scratch containment, write allowlist와 전체 timeout을 새 agent run에 동일하게 적용한다. retry prompt만 VALIDATION FEEDBACK을 가지며 초기 `prompt_hash`에는 포함하지 않는다. agent 실행 자체의 실패·timeout에는 retry하지 않으며 세 번째 candidate도 invalid이면 그 callable은 unresolved로 남긴다. 이미 성공한 candidate는 16.10의 checkpoint로 publish한다. `agent_runs`에는 최종 검증 성공 run만 기록한다.


### 17.3 에이전트가 변경할 수 없는 요소

에이전트는 다음 요소를 임의로 변경할 수 없다.

* callable 이름·매개변수명·매개변수 타입·반환 타입·오류 타입·선언된 효과
* 공개 구조체 field와 enum variant
* impl concrete 이름, trait 목록, ordered state field·default, init contract, invariant와 `modifies`
* compiler-owned class shell, slot, lock, init, facade wrapper, provenance와 generated test

impl method agent는 exact private `_cott_impl_<Concrete>_<method>` canonical top-level function 하나를 작성해야 하며, 같은 file의 permitted private helper와 literal `Final` constant 외 public declaration·class·mutable module global을 작성할 수 없다. 계약 변경이 필요하면 `.cott` 파일을 수정하지 않고 변경 필요성을 결과로 보고해야 한다.

### 17.4 격리 실행과 원자적 반영

CLI argument parsing 뒤 compiler는 먼저 project root를 canonical directory handle로 고정한다. clean checkout에서 `.cott`이 없으면 root handle 기준 `mkdirat`으로 mode `0755` directory를 만들고 root를 fsync하며, 이미 있으면 no-follow directory인지 확인한다. `.cott/lock`은 그 handle 기준 `O_NOFOLLOW | O_CREAT`로 열어 regular file·`st_nlink == 1`을 확인한 뒤 exclusive OS advisory lock을 획득하며, 다른 project input은 lock 전 읽지 않는다. lock 안에서 `transactions` directory도 같은 방식으로 생성·검사한다. 모든 project command는 종료까지 lock을 유지하고 read-only command도 같은 coherent snapshot을 읽는다. lock metadata는 PID와 execution nonce를 기록하며 process 사망 시 OS가 lock을 해제한다. `cott prompt`는 이 lock과 metadata를 허용하는 inspection이며 pending journal이 있으면 recovery와 publication 없이 거부한다. `fmt`·`emit`·`generate`·`verify`·`diff` 등 일반 command는 같은 lock에서 미완료 journal을 복구한다.

Content input과 transaction destination의 각 path component는 project root handle 기준 no-follow로
연다. Symlink, `st_nlink != 1` regular file과 project root 밖 path는 hash 전에 거부한다. Manifest가
지정한 Python interpreter/type checker, Kotlin compiler/Java launcher, Dart SDK 및 agent executable은
canonical regular-file path로 symlink를 한 번 해소하는 예외다.

`.cott`, 모든 transaction destination과 staging payload가 같은 filesystem이 아니거나 그 filesystem이 same-directory atomic rename, exclusive advisory lock, regular file·directory의 durable `fsync`를 제공하지 않으면 multi-file apply를 시작하지 않는다.

lock 획득 직후 다른 입력을 읽기 전에 `.cott/transactions/`를 검사한다. transaction directory는 0개 또는 1개만 허용하며 둘 이상이면 application payload 및 기존 journal/state를 변경하지 않고 exit `6`으로 실패한다. 단, lock 획득을 위한 `.cott/lock` state 초기화는 예외다. journal의 `schema_version`이 현재 compiler와 정확히 다르거나 journal·pre-image가 unreadable·checksum-invalid이면 추측하거나 삭제하지 않고 exit `6`으로 실패한다. inspection command는 이 단계에서 recover하지 않고 pending journal을 거부한다.

1. transaction은 `schema_version`, nonce, 모든 destination의 file kind·mode·content pre-image, sibling temporary post-image, operation 목록·hash와 전체 journal checksum을 `.cott/transactions/<nonce>/`의 immutable journal에 저장한다.
2. backup file과 immutable journal을 fsync하고 transaction directory와 parent를 fsync한다. 상태는 journal과 분리한 marker이며 각 전이는 새 state와 journal checksum을 sibling temp에 쓰고 file fsync → same-directory atomic rename → transaction directory fsync 순서로 publish한다.
3. immutable journal과 pre-image 검증이 끝나면 `prepared`, 첫 project mutation 직전에 `applying` marker를 차례로 publish한다.
4. 각 regular-file post-image는 destination parent의 no-follow sibling temp에 final mode·bytes로 쓰고 file을 fsync한 뒤 hash를 재확인한다. `generation.json` 외 payload는 sibling rename 또는 삭제로 반영하고 매 operation 뒤 destination parent를 fsync한다.
5. `generation.json`을 포함하는 command는 같은 방식으로 만든 그 sibling temp를 모든 다른 payload 뒤 마지막으로 rename하고 parent를 fsync한다.
6. 적용 대상의 file·directory durability가 모두 확인된 뒤에만 `committed` marker를 publish한다.
7. `prepared`·`applying`, absent·unknown·checksum-invalid state marker는 immutable journal과 pre-image가 검증되는 경우 보수적으로 rollback하고, valid `committed` marker만 cleanup한다.

rollback은 idempotent해야 하며 recovery 자체가 중단되면 같은 journal로 다시 시작한다. 복구 결과의 file·directory fsync가 끝난 뒤에만 journal을 삭제하고 transaction parent를 fsync한다.

compiler payload의 regular file mode는 `0644`, directory mode는 `0755`로 고정하고 process umask와 무관하게 설정한다.

Transaction 시작 시 계약, manifest, referenced rule, selected target input/dependency, generated
tree와 compiler-owned evidence tree의 file list/content hash를 기록한다. Project binding과 existing
implementation도 포함한다. Python-specific scope는 아래와 같고 Kotlin은 16A, Dart는 16B의
durable source/private part/package scope를 따른다.

staging에는 대상 계약, allowed direct helper 계약, binding, rule, 기존 구현과 compiler 생성물의 사본을 제공하고 실제 project path는 agent에게 노출하지 않는다. 각 agent process의 workspace write allowlist는 현재 callable file 하나로 제한한다.

```text
<target.python.source>/_cott_impl/<module path>/<function>.py
<target.python.source>/_cott_impl/<module path>/<Concrete>/<method>.py
```

각 agent file에는 canonical function 하나와 same-file private helper 0개 이상, same private-name rule의 permitted literal `Final` immutable constant만 둘 수 있다. helper는 single-leading-underscore private name을 쓰고 facade·manifest binding·provenance symbol이 아니며 public behavior가 되면 별도 Cott declaration과 implementation file로 승격한다. 공개 cott helper의 implementation file, 필요한 `_cott_impl/**/__init__.py`, facade, type module, stub, IR, docs, generated tests와 provenance는 현재 agent가 쓸 수 없다. free-function binding file을 agent 생성 대상으로 함께 쓰거나 impl method binding을 선언하는 구성은 거부한다.

scratch는 workspace diff 대상이 아니며 실행 뒤 폐기한다. agent 실행 후 staging 전체 file list와 diff를 검사한다. `.cott`, manifest, binding, compiler 생성물, 비선택 구현 또는 allowlist 밖 변경은 실패다. agent가 workspace에 만든 cache·temporary file도 위반이다.

compiler-owned 관리 집합은 `<target.python.generated>`, `<target.python.stubs>`, `<artifact-root>/ir`, `<artifact-root>/docs`, `tests/generated`와 compiler-owned `<target.python.source>/_cott_impl/**/__init__.py`의 합집합이며, generation record는 `<artifact-root>/generation.json`이다. stale 삭제는 현재 command의 ownership 안에서만 수행한다. `emit ir`은 `<artifact-root>/ir`만, `emit python`과 `generate`는 전체 관리 집합을 소유하며 verify는 전체 집합을 재생성해 비교하되 반영하지 않는다. `emit ir`의 non-IR managed hash는 기존 trusted record를 유지하며 디스크의 무관 편집을 새 baseline으로 축복하지 않는다.

성공적으로 project source에 승격된 agent callable file은 비결정적이지만 durable implementation source로 취급하며 cott가 자동 삭제하지 않는다. IR에서 더 이상 참조하지 않는 file은 `cott diff`의 `IMPLEMENTATION STALE`로 보고하되 public facade나 verify 대상에는 포함하지 않는다. 사용자가 명시적으로 삭제한다.

각 command의 staging 검사가 성공한 뒤 시작 input와 해석된 tool/dependency identity/hash를 다시
비교하고 달라졌으면 덮어쓰지 않는다. `emit ir`은 IR scope와 record, target emit/generate는 해당
target의 durable implementation change와 compiler-owned managed set 및 record를 generation-last로
반영한다. `cott fmt`의 actual source edit는 기존 current certification을 invalidate하고 history를
보존한다. Python verify는 expected managed bytes를 비교하고 성공 record만 반영한다. Kotlin
verify는 16A.3의 compiled JAR/runtime dependency와 성공 record를 함께 반영한다.
Dart verify는 16B의 portable package/vendor identities, native kernel evidence와 성공 record를
publish하며 deployment에서는 kernel과 runner를 제외한다.

OS advisory lock은 Cott process끼리만 조정한다. 이를 따르지 않는 editor/package installer/build
process는 command 실행 중 같은 project destination이나 dependency를 바꾸면 안 된다. Final hash
재확인은 apply 전 drift를 탐지하지만 concurrent non-Cott writer의 수정 보존이나 실행 중 target
reader의 snapshot isolation은 보장하지 않는다. 배포된 target은 complete transaction 뒤 새
runtime/build process에서 사용한다.

실패, timeout, 취소 또는 검증 오류에서는 이전 세대를 유지한다. 프로젝트 밖 dependency는 sandbox에서 읽기 전용으로 제공한다.

### 17.5 생성 결과 검증

아래 full pipeline은 Python의 `emit python`, `generate --target python`, full `verify`를 상세화한다.
Kotlin의 대응 pipeline은 16A.2–16A.3에 규정한다. 두 target 모두 `emit ir`은 Canonical IR 뒤
IR-scope apply로 이동하고, emit/generate는 unverified publication이며 explicit verify만
certification을 publish한다.

```text
project lock 획득 및 미완료 journal 복구
  ↓
file list와 입력 hash 기록, staging·scratch 생성
  ↓
cott parse, type check 및 Canonical IR 생성
  ↓
Python runtime type, IR, stub, docs와 test strategy 생성
  ↓
이번 세대 type module과 Canonical IR을 기준으로 free-function binding, impl helper shape 및 exact cott facade import graph 정적 해석
  ↓
선택된 미구현 callable이 있으면 지정 agent 호출
  ↓
workspace allowlist 및 비선택 구현 불변 검사
  ↓
agent 이후 callable symbol·source origin·content hash, direct facade reference와 external import record 재계산
  ↓
local implementation을 canonical module path의 generated runtime copy로 복사
  ↓
embedded runtime provenance를 가진 facade, impl class shell과 staging `current` snapshot 생성
  ↓
public Python symbol projection과 compiler 관리 집합 검사
  ↓
BasedPyright, verified loader, mode별 wrapper와 생성된 순수 callable 계약 테스트
  ↓
실제 project file list·입력 hash와 tool·direct dependency provenance 재확인
  ↓
emit·generate는 durable journal로 generation.json을 마지막에 포함해 반영; verify는 expected managed bytes 일치 확인 후 generation.json만 반영
  ↓
project lock 해제
```

staging facade는 embedded identity·runtime origin·hash를 generated copy에서 검사하며 `current.verified` bit를 요구하지 않는다. full verify 성공 시 `current`와 `last_verified`를 같은 snapshot으로 기록하고, emit·generate는 `last_verified`를 보존한다.

full verify에는 agent 선택 범위가 없고 agent를 호출하지 않는다. staging에서 재생성한 managed set과 actual project set이 정확히 같아야 하며 검증 record 외 차이는 폐기한다.

free-function binding을 해석하지 못하거나 그 external import에 필요한 lock entry가 없으면 agent 호출 전에 실패한다. facade import가 exact module의 declared public free function으로 해석되지 않거나 금지된 형태면 같은 시점에 실패한다. implementation file이 canonical name/signature, same-file private helper/`Final` policy 또는 allowed `self` method call rule을 어기면 같은 시점에 실패한다. agent 결과의 facade·external import는 호출 직후 같은 규칙으로 다시 검사한다. clean checkout에서도 이번 세대 type module과 facade를 먼저 만들므로 이전 generated file에 의존하지 않는다.

특정 callable generate에서 agent가 바꿀 수 있는 durable source는 선택된 free-function 또는 impl-method file뿐이지만 compiler-owned 관리 집합은 항상 전부 재생성·반영한다. `last_verified`가 있으면 그 baseline에 존재한 비선택 declaration의 canonical `contract_surface` record는 byte-identical해야 하고 비선택 public symbol은 현재 `public_python_symbols`에도 남아야 한다. 새 declaration 추가는 허용한다. 최초 검증 전 `last_verified = null`이면 이 guard 없이 선택 범위를 생성하고 `current.verified = false`로 기록한다.

compiler 산출물은 결정적으로 다시 만들 수 있지만 agent implementation은 durable한 비결정적 source다.

### 17.6 검증 실패 예시

다음 구현은 거부한다.

```python
def process_bar(data, options):
    return engine(data)
```

거부 이유:

* 매개변수 타입 누락
* 반환 타입 누락
* `Result` 미사용
* 예외 변환 누락
* 출력 크기 계약 검증 불가

---

## 18. CLI 설계
전역 version form은 `cott (--version|-V)`다. 두 form은 token 하나만 허용하는 closed parse이며 뒤에 operand 또는 option이 있으면 CLI usage error (exit `2`)다. 성공하면 stdout에 정확히 `cott <package-version>` 한 줄을 쓰고 exit `0`을 반환한다. `<package-version>`은 Cargo `[package].version`에서만 derive하는 compiler/package identity이며 v1.0에서는 `1.0.0`이다.


### 18.1 프로젝트 초기화

```bash
cott init <path> [--target python|kotlin|dart] [--name <project-name>] [--no-sync] [--format json]
cott init path/to/python-project
cott init path/to/kotlin-module --target kotlin
cott init path/to/dart-module --target dart --name dart_module
```

`<path>`는 필수이며 absolute·relative path를 허용한다. 기존 parent를 canonicalize하고 그 안의
final component 하나를 새 target으로 사용한다. Target이 symlink를 포함해 이미 존재하면 exit
`2`다. 기본 project name은 target basename이고 invalid name에는 `--name`이 필요하다. Python과
Kotlin target 모두 normalized lowercase kebab-case project identity와 injective module path를
검사한다. Interactive prompt, `--force`, overwrite, dry-run은 없다.

`init`은 아직 project가 없으므로 project lock/journal 대신 private sibling staging,
mode `0600` closed `.cott-init` ownership record, fsync와 atomic no-replace rename을 사용한다.
실패 cleanup은 자신이 가진 nonce/marker가 일치하는 staging만 제거한다.

Default Python init은 `python/.python-version`, `pyproject.toml`, `uv.lock`과 선택적 `.venv`를
만들고 uv `>=0.12.3`, CPython `>=3.14.6,<3.15`, BasedPyright `>=1.39.9`의 기존 closed
install/lock/sync/probe contract를 따른다. Python `--no-sync`는 managed Python install/probe와
lock은 수행하고 environment sync와 root venv tool probe만 건너뛴다. Subprocess는 shell 없이
sanitized environment와 bounded output/time을 사용한다.

Kotlin init은 Cott source, empty Kotlin implementation root, closed `[target.kotlin]` manifest와
`.gitignore`만 만든다. `--no-sync`가 없으면 configured kotlinc/JDK/stdlib/coroutine identity를
probe하고, 있으면 그 probe를 건너뛴다. Kotlin init은 uv, Python, Gradle, network download 또는
Android scaffold를 실행하지 않는다. Kotlin name/tool probe/config failure는 exit `2`, filesystem
publication failure는 `6`으로 fail closed한다.

### 18.2 타입 및 문법 검사

```bash
cott check
cott check src/system/process.cott
```

### 18.3 포맷

```bash
cott fmt
cott fmt --check
```

`cott fmt`는 17.4의 project lock을 획득하고 journal을 복구한 뒤 locked source snapshot을 parse·format하여 old 또는 new complete source snapshot을 같은 journal로 반영한다. 실제 byte 변경이 있으면 기존 generation record도 같은 transaction에서 invalidated current로 갱신한다. `cott fmt --check`도 공통 lock 초기화와 journal recovery를 수행하지만 locked snapshot을 읽기만 하며 source, managed artifact 또는 generation record를 반영하지 않는다.

### 18.4 IR 생성

```bash
cott emit ir
```

이 명령은 `<artifact-root>/ir` scope와 `<artifact-root>/generation.json`만 원자 갱신하고 다른 compiler-owned managed bytes는 그대로 둔다. non-IR managed hash는 기존 trusted 값을 유지하고, IR-only emission이 무관한 managed 편집을 새 baseline으로 기록하지 않는다. `current.verified = false`이며 `last_verified`를 보존한다.

기존 target 산출물을 유지할 때는 current callable kind/intent와 일치하는
implementation·AgentRun·source input hash만 보존한다. 신규, intent-changed 또는 pending 대상은
unresolved다. 이 판정에 Python/Kotlin/Dart compiler나 checker를 실행하지 않는다.

### 18.5 Target source 생성

```bash
cott emit python
cott emit kotlin
cott emit dart
```

Manifest가 선택한 target과 explicit emit target은 일치해야 한다. 세 명령은 agent나 target
compiler 없이 compiler-owned source를 staging에서 만들고 원자 갱신한다. 미구현 callable은
facade에서 생략하고 `current.unresolved`에 기록하며 placeholder를 만들지 않는다. Authentic
pending agent source는 소유권을 유지한다. 결과는 항상 `current.verified = false`이고
`last_verified`를 보존하므로 배포 가능한 certification이 아니다.

### 18.6 구현 생성

```bash
cott generate [<fully.qualified.callable>] --agent codex|claude|omp --target python|kotlin|dart [-j <jobs>] [--project <dir>] [--format json]

cott generate --agent claude --target python
cott generate foo.bar.process_bar --agent omp --target python
cott generate example.module.calculate --agent codex --target kotlin
cott generate example.module.calculate --agent omp --target dart
```

Explicit `--target`은 필수고 manifest의 exactly-one target과 일치해야 한다. Selection은 exact
canonical free-function 또는 eligible impl-method FQN만 받고 glob/alias는 거부한다. 선택된
unresolved callable이 있으면 `--agent`가 필수이고 허용 값은 `codex`, `claude`, `omp`다. Binding
및 fresh accepted source는 재사용하고 stale/unresolved source만 target별 `implementation.py`,
`implementation.kt`, `implementation.dart` candidate로 생성한다. Source audit와 complete-candidate validation은 실제
target 규칙을 사용하고 failure checkpoint는 정확한 pending source provenance를 남긴다. 모든
generate 결과는 `current.verified = false`; 배포 gate는 explicit full `cott verify`다.

### 18.6.1 Prompt 검사

```bash
cott prompt <fully.qualified.callable> [--project <dir>] [--format json]
```

FQN은 generate와 같은 exact canonical callable symbol이다. Provider와 target compiler/checker를
요구하지 않고 같은 초기 frozen snapshot의 prompt bytes를 렌더한다. JSON은
`{symbol, intent_hash, prompt_hash, generation_required, context, prompt}`와 final newline이고
`prompt_hash`는 retry feedback 전 initial bytes만 hash한다. Python/Kotlin/Dart write path는 각각
`implementation.py`/`implementation.kt`/`implementation.dart`다. Inspection은 lock metadata를
쓸 수 있지만 pending journal을 recovery/publication 없이 거부한다. Formal source가 authority이고
project rule/reference source는 override하지 않는다.

### 18.7 구현 검증

```bash
cott verify
```

검증 범위:

* 공개 free-function 및 impl class/init/method signature와 `public_python_symbols(IR)` projection
* compiler-owned impl class shell, ordered state slots/defaults, identity equality/hash, no dynamic attribute/`__del__`, per-instance `RLock`, trait method union exact coverage와 unresolved-method class omission
* custom enum union·variant class, public const와 module type 구조
* 숫자 ABI metadata, 명목 container invariance와 structural trait bound
* facade와 tool-only stub의 독립적인 Canonical IR 일치
* BasedPyright strict 결과와 binding/agent source의 static signature
* binding/agent file의 canonical symbol/path·exact signature, same-file private helper/`Final` policy와 allowed `self` method edge
* deterministic init-case construction과 canonical struct candidate filtering을 포함한 pure/fixture scenario contract test, init/invariant/modifies/success/conditional-error clause별 counts·witness·unobserved evidence
* unresolved callable과 compiler-owned stale module·symbol, stale durable implementation 진단
* generated copy의 verified-loader runtime signature, facade/type/source/runtime origin·content hash와 copy byte identity
* authored/deployed tree의 facade-only AST audit, `_cott_impl`·`cott_bindings` direct/dynamic import·re-export와 symlink/hardlink/unknown import 거부
* 모든 external import의 selected lock entry, installed distribution identity·version·metadata·origin·content hash와 archive-to-install 신뢰 등급
* configured mode의 public callable `requires`, concrete 반환 타입, canonical struct invariant, allowed error variant와 `ensures`, always-on impl init/state checks
* recursive-placement `Opaque` tag/key admissibility와 reserved target path, staged sandbox/isolated-loopback fixture authorization·cleanup·process-group containment, closed semantic coverage/policy와 current/last_verified provenance

Python `cott verify`는 result cache를 사용하지 않고 current contract, manifest, lock,
implementation input에서 expected IR/Python/stub/docs/test artifact를 staging에 다시 만든 뒤 actual
managed set과 byte-for-byte 비교한다. Unresolved pending, missing/extra/hand-edited managed file과
start snapshot drift는 hard failure다. Current facade에 없는 old implementation은 export하지
않는다. Verify는 source/managed file을 고치지 않고 artifact verification이 성공한 뒤
`generation.json`만 journal transaction으로 갱신해 same snapshot의
`current.verified = true`, complete evidence/`semantic_coverage`, `last_verified`를 publish한다.
Selected coverage policy 위반은 certified record를 되돌리지 않고 exit `8`로 gate만 실패시킨다.

위 bullet은 Python target의 세부 verification inventory다. Kotlin verify는 16A.3의 별도
generation-1/runtime-1 pipeline으로 expected Kotlin source를 byte-compare하고 exact
kotlinc/JDK/stdlib/coroutine/classpath/compile-only identity를 확인한 뒤 sandbox에서
`cott-module.jar`와 real public-facade runner를 compile/run한다. Kotlin도 unresolved와 drift를
거부하며, complete evidence와 `semantic_coverage`를 가진 `current == last_verified` snapshot만
`verified = true`로 publish한다.
Dart verify는 16B.4의 offline package/analyzer/kernel/runner 및 pre-VM Landlock 경계를 사용한다.

### 18.7.1 실행용 배포

```bash
cott deploy [--output <dir>] [--project <dir>] [--format json]
```

`deploy`는 현재 verified generation snapshot의 실행용 directory package를 만든다. 기본 출력은
`<project>/dist/<project.name>-<project.version>/`이며 상대 `--output`은 호출 working directory
기준이다. 기존 target은 비어 있어도 덮어쓰지 않는다. Project input, managed artifact, `.cott`,
`.venv`, unsafe parent/target과 겹치는 output은 거부한다. Project lock/recovery 뒤 읽기만 하고
source, managed artifact 또는 generation record를 갱신하지 않으며 agent나 target compiler/checker를
호출하지 않는다.

gate는 closed generation schema/identity와 현재 compiler/runtime package version, project version,
`current.verified`, empty unresolved, passed semantic-coverage policy다. source inventory를 다시
발견하여 manifest·rules·target metadata·lock·선택 implementation을 포함한 기록된 input hash와
비교하고, 전체 managed inventory와 실제 bytes를 확인한다. 대상 regular file과 parent는 symlink와
hardlink를 허용하지 않는다. 읽은 input snapshot을 publication 직전에 다시 비교한다.

Python payload는 `python/` 아래 managed facade/type/runtime/implementation, authored runtime
adapter, byte-identical `generation.json`, exact `.python-version`, production
`requirements.txt`다. Existing facade-only audit와 uv frozen offline export 규칙은 그대로다.
`.cott`, manifest, IR, stub, strategy/test, authored private copy와 original generated path는
제외하며 non-Python application resource를 추론하지 않는다.

Kotlin payload는 `cott-module.jar`, byte-identical `generation.json`, schema-1
`dependencies.json`, `runtime-libs/kotlinx-coroutines-core-jvm.jar`와 verified
`target.kotlin.classpath` copy다. Kotlin stdlib는 required/provided dependency로 metadata에
기록하지만 bundle하지 않고 `compile_only`, compiler/JDK, Android SDK/source/resource도 제외한다.
두 target의 payload는 runtime에 필요한 target code와 provenance를 보존한다.

Python production dependency가 있으면 uv `>=0.12.3`의 bounded subprocess로 target metadata와
configured lock의 private scratch copy를 `export --frozen --offline --no-default-groups --no-dev
--no-emit-project --no-editable --no-header --no-annotate --no-config --no-cache
--no-python-downloads --format requirements.txt`로 export한다. Package/version/marker와 artifact
hash를 보존하고 local/editable/VCS requirement는 거부한다. Recorded installed Python runtime
dependency가 production export에 없으면 실패한다. Dependency-free Python project는 uv를
호출하지 않는다. Interpreter와 external distribution 자체는 bundle에 복사하지 않으며 destination이
기록된 CPython patch·OS·architecture 및 dependency identity를 만족해야 한다.

private sibling staging에 payload를 쓰고 fsync한 뒤 기존 init의 atomic no-replace rename으로
directory 전체를 publish한다. 실패한 staging은 제거하며 기존 output을 지우거나 수정하지 않는다.
성공하면 output path 한 줄과 exit `0`, CLI/manifest 오류는 `2`, snapshot/dependency gate 오류는
`4`, lock/output/publication 오류는 `6`이다. JSON은 기존 diagnostics schema v1 envelope를 사용한다.

### 18.8 변경점 확인

```bash
cott diff
cott diff --baseline path/to/generation.json
```

`cott diff`는 manifest 구성 뒤 cott semantic 분석 전에 baseline을 resolve한다. 기본 baseline은 `<artifact-root>/generation.json`의 `last_verified`다. 없으면 추측하지 않고 exit `2`로 종료한다. `--baseline`은 다른 generation record snapshot을 명시하며 baseline file이 없거나 unreadable·schema-invalid여도 exit `2`다.

출력 예시:

```text
CONTRACT BREAKING:
- process_bar return type changed:
  Result[OutputPayload, BarError]
  -> OutputPayload
- BarOptions.use_cache default changed:
  false -> true

CONTRACT NON-BREAKING:
- public function foo.bar.evaluate_bar added

IMPLEMENTATION:
- foo.data.load_payload binding changed
- foo.bar.process_bar implementation content hash changed
- unreferenced python/_cott_impl/foo/legacy/legacy_process.py
- dependency lockfile changed
```

public declaration 제거·rename, sync/async kind, signature·generic·type shape·variant·field·default·constant·refinement·contract clause·effect의 변경은 conservative하게 breaking이다. 새 top-level type·function·constant만 기존 target symbol과 충돌하지 않을 때 additive다. doc만 바뀌면 `DOCUMENTATION`이다. 이 label은 regeneration 요구와 별개다. diff는 semantic implication을 추측하지 않는다.

baseline/current `[project].version`은 restricted `x.y.z` API version이며 current가 baseline보다 작으면 diff error다. breaking change는 baseline major가 `0`이면 최소 minor, 그 밖에는 최소 major bump를 요구한다. additive change는 최소 minor bump를 요구하고 implementation/documentation-only change는 bump를 요구하지 않는다. insufficient bump는 `VERSION INCOMPATIBLE` change로 report에 추가되고 `--exit-code`는 7을 반환한다. report는 declaration removal에 “Remove uses …”, addition에 “Adopt …” migration advice를 함께 제공한다.

`cott diff`는 `generation_id` mismatch 자체를 change로 보지 않는다. 같은 target environment에서는
해당 compiler/runtime/tool identity와 managed artifact hash를 비교한다. 다른 machine에서는
machine-local identity를 제외하고 normalized contract/public target symbol, durable implementation
content와 dependency identity를 비교한다. 다른 backend의 record를 서로 baseline으로 읽지 않는다.

Generation result cache는 없다. Contract, manifest, rule, target input, exact Python
interpreter/checker/lock, Kotlin compiler/JDK/JAR 또는 Dart SDK/locked-package identity, implementation
source/runtime-origin/hash 중 하나라도 달라지면 새 target generation이다. `cott verify`도 항상
선택 target의 모든 검사를 실행한다.

### 18.9 언어 서버

```bash
cott lsp
```

`cott lsp` is the only language-server invocation and accepts no arguments. It serves stdio JSON-RPC using UTF-16 positions and full document sync; an open editor document takes precedence over its on-disk project source. It reuses the parser and HIR for push diagnostics, keyword/type/declaration completion, declaration/type/`doc` hover, and project-aware definition. It is editor analysis only: it never generates, publishes, or invokes an agent.

### 18.10 Exit code

| code | 의미 |
| --- | --- |
| `0` | 요청한 범위 성공 |
| `1` | formatter 비멱등성을 포함한 internal compiler error |
| `2` | CLI 사용법, init tool/name/path, manifest 구성 또는 diff baseline 오류 |
| `3` | Cott 문법, 이름, 타입 또는 계약 오류 |
| `4` | target 구현 누락·불일치, provenance drift 또는 verify 실패 |
| `5` | agent 또는 Python init uv 실행·probe 실패, timeout 또는 취소 |
| `6` | init filesystem/cleanup/atomic rename, lock, concurrent mutation, sandbox 또는 apply 실패 |
| `7` | `cott diff --exit-code`에서 breaking contract 발견 |
| `8` | certified semantic coverage policy gate 실패 또는 Kotlin `cott fmt --check` mismatch |
| `9` | Python `cott fmt --check` format mismatch |

`cott diff`는 기본적으로 차이를 출력하고 0을 반환하며 `--exit-code`에서만 breaking change를 7로 반환한다. `cott emit`의 미구현 진단과 `verified = false`는 emitter 자체가 성공했다면 0이지만 배포 성공을 뜻하지 않는다. policy-failed verify는 generic `verified` success line을 출력하지 않지만 record는 publication되어 diff/provenance가 policy failure를 관찰할 수 있다.

여러 문제가 동시에 있으면 argument·subcommand 및 init의 missing/unsupported uv·invalid args/path/name 오류 `2` → init filesystem·cleanup·atomic no-replace rename과 lock·journal recovery `6` → cleanup이 성공한 init target collision `2` → manifest 구성 `2` → diff baseline resolution `2` → cott semantic `3` → implementation·provenance `4` → agent 또는 init uv 실행·probe `5` → formatter 비멱등성 등 internal compiler error `1` → apply `6` → command-specific diff·coverage-policy·format 상태 `7`·`8`·`9` 순서에서 처음 검출된 실패 하나를 반환한다. code를 합치거나 더 늦은 오류로 덮어쓰지 않는다.

---

## 19. 프로젝트 구조

### 19.1 Python `cott init` 직후 구조

Default `cott init <path>`는 존재하지 않는 새 Python target에 다음 최소 scaffold를 만든다.
`<module>`은 project name에서 derive한 Python-safe module name이다.

이 tree는 성공한 command의 final state다. 실행 중에는 root에 mode `0600` transient `.cott-init` ownership record가 존재하며 final commit에서 제거된다. crash 뒤 이 file이 남은 directory는 ownership-marked incomplete 또는 completed state로 진단하고 자동 삭제·overwrite하거나 정상 project로 취급하지 않는다.

```text
<path>/
├── .gitignore
├── cott.toml
├── src/
│   └── <module>/
│       └── main.cott
├── python/
│   ├── .python-version
│   ├── pyproject.toml
│   └── uv.lock                 # --no-sync일 때도 생성
└── .venv/                      # default frozen sync가 만드는 Python 3.14 environment
```

`src/<module>/main.cott`의 전체 내용은 final newline을 포함한 `module <module>.main` 한 줄이다. init은 `.cott`, `generated`, `tests`, adapter, implementation, `AGENTS.md`를 만들지 않는다.

생성되는 root `.gitignore`는 다음 machine-local state와 Python cache만 ignore한다. deterministic compiler output 전체를 ignore하지 않는다.

```gitignore
.cott/
.venv/
generated/generation.json
__pycache__/
*.py[cod]
```

생성되는 `cott.toml`은 optional binding·effects·generator table을 만들지 않는다.

```toml
[project]
name = "<name>"
version = "0.1.0"
source = "src"

[target.python]
source = "python"
generated = "generated/python"
stubs = "generated/stubs"
lockfile = "python/uv.lock"
interpreter = ".venv/bin/python"
type_checker = ".venv/bin/basedpyright"
runtime_validation = "boundary"
```

생성되는 `python/.python-version`은 `3.14`이고, `python/pyproject.toml`은 build system 없이 다음 PEP 621 metadata와 uv default dev group만 가진다.

```toml
[project]
name = "<name>"
version = "0.1.0"
requires-python = ">=3.14,<3.15"
dependencies = []

[dependency-groups]
dev = ["basedpyright==<basedpyright-version>"]
```

`<basedpyright-version>`은 사용 중인 cott compiler release가 고정한 exact supported BasedPyright version을 렌더링하는 template parameter다.

### 19.2 Kotlin `cott init` 직후 구조

`cott init <path> --target kotlin`의 final tree는 다음과 같다. Android/Gradle file은 없다.

```text
<path>/
├── .gitignore
├── cott.toml
├── src/
│   └── <module>/
│       └── main.cott
└── kotlin/
```

`main.cott`는 `module <module>.main`과 bodyless `fn main() -> Unit`을 담는다. Kotlin
`.gitignore`는 `.cott/`, `generated/`, `dist/`, `.gradle/`, `build/`를 ignore한다. 생성 manifest는
다음과 같고 binding/external/effect/generator/verification table을 임의로 만들지 않는다.

```toml
[project]
name = "<name>"
version = "0.1.0"
source = "src"

[target.kotlin]
source = "kotlin"
generated = "generated/kotlin"
compiler = "kotlinc"
java = "java"
jvm_target = 17
runtime_validation = "boundary"
```

### 19.3 확장된 Python project

프로젝트가 성장하면 user-added `AGENTS.md`, adapter, implementation은 유지되고 다음처럼 확장된다.

```text
.gitignore
cott.toml
AGENTS.md
.cott/
├── lock
└── transactions/
.venv/

src/
└── foo/
    ├── data.cott
    └── bar.cott

generated/
├── ir/
│   ├── foo.data.json
│   └── foo.bar.json
├── python/
│   ├── cott_runtime/
│   │   ├── __init__.py
│   │   └── py.typed
│   ├── _cott_impl/
│   │   ├── __init__.py
│   │   └── foo/
│   │       ├── __init__.py
│   │       └── bar/
│   │           ├── __init__.py
│   │           └── process_bar.py
│   ├── my_project/
│   │   ├── __init__.py
│   │   └── adapters/
│   │       ├── __init__.py
│   │       └── provider.py
│   └── foo/
│       ├── __init__.py
│       ├── py.typed
│       ├── data.py
│       ├── data_types.py
│       ├── bar.py
│       └── bar_types.py
├── stubs/
│   └── foo/
│       ├── data.pyi
│       └── bar.pyi
├── docs/
└── generation.json

python/
├── .python-version
├── _cott_impl/
│   ├── __init__.py
│   └── foo/
│       ├── __init__.py
│       └── bar/
│           ├── __init__.py
│           └── process_bar.py
├── my_project/
│   └── adapters/
│       └── provider.py
├── pyproject.toml
└── uv.lock

tests/
├── generated/
└── manual/
```

`.cott/lock`, `.cott/transactions`와 source project의 `<artifact-root>/generation.json`은
machine-local state다. Release baseline으로 따로 보관한 record는 `cott diff --baseline`에
명시할 수 있다. Runtime deployment에는 source-control 여부와 무관하게 verified
`generation.json`의 byte-identical copy가 포함된다.

### 19.4 닫힌 manifest와 target 선택

Python manifest 예시:

```toml
[project]
name = "foo-app"
version = "0.1.0"
source = "src"

[target.python]
source = "python"
generated = "generated/python"
stubs = "generated/stubs"
lockfile = "python/uv.lock"
interpreter = ".venv/bin/python"
type_checker = ".venv/bin/basedpyright"
runtime_validation = "boundary"

[verification]
proof_node_limit = 1024
proof_branch_limit = 256
candidate_limit = 64
lifecycle_limit = 3

[target.python.external_types]
"foo.data.HttpRequest" = "starlette.requests:Request"

[target.python.implementations]
"foo.data.load_payload" = "my_project.adapters.provider:load_payload"

[generator]
rules = "AGENTS.md"
timeout_seconds = 900
```
Manifest schema는 닫혀 있고 `[target.python]` 또는 `[target.kotlin]` 중 정확히 하나만 허용한다.
Target별 `implementations`와 `external_types`, 공통 `[effects]`의 dynamic key 이외 unknown
table/field는 configuration error다. Python external projection value는 `module:Qualname`,
Kotlin value는 Kotlin FQN이고 각 key는 declared external type에 exactly one 대응해야 한다.
Missing/stale/non-external key와 malformed/prompt-unsafe value는 emit 전 configuration error다.
Projection table은 target configuration이며 Canonical IR이나 implementation authority가 아니다.

`[verification]`은 선택적 closed table이며 proof/candidate/lifecycle limit과 closed `[verification.fixtures]`, `[verification.coverage]`만 허용한다. 누락하면 default를 사용하고 zero, non-integer, unknown key 또는 hard maximum 초과는 configuration error로 즉시 fail closed하며 managed tree를 쓰지 않는다.

| field | default | hard maximum | 용도 |
| --- | ---: | ---: | --- |
| `proof_node_limit` | 1024 | 16384 | bounded proof node |
| `proof_branch_limit` | 256 | 4096 | bounded proof branch |
| `candidate_limit` | 64 | 1024 | contract-test candidate |
| `lifecycle_limit` | 3 | 64 | async worker/tick observation |
| `fixtures.scenario_timeout_ms` | 1000 | 60000 | scenario wall bound |
| `fixtures.filesystem_bytes` / `filesystem_files` | 16777216 / 256 | 268435456 / 4096 | compiler-owned fs ceiling |
| `fixtures.http_body_bytes` / `http_requests` / `http_redirects` | 1048576 / 64 / 8 | 16777216 / 4096 / 64 | local HTTP ceiling |
| `fixtures.transcript_events` | 1024 | 16384 | fixture evidence ceiling |

fixture limits are resource ceilings only: fixture content, path, route, host, command, script and plugin registration are manifest syntax가 아니다. `[[verification.coverage.rules]]`의 exact selector/allow booleans는 16.9 규칙을 따르며 별도 suppression/severity knob는 없다. effective verification budget과 fixture ceiling은 strategy v5와 verification evidence에 기록한다. limit 변경은 `proved`·`disproved`·`unknown`, test observation·`미관찰`의 의미를 바꾸지 않는다.

`[project]`의 `name`·`version`·`source`는 공통 필수다. Python target의
`source`·`generated`·`stubs`·`interpreter`·`type_checker`·`runtime_validation`은 필수이고
`lockfile`은 dependency에 따라 조건부다. Kotlin target의 `source`·`generated`·
`runtime_validation`은 필수이며 `compiler = "kotlinc"`, `java = "java"`,
`jvm_target = 17`, empty `classpath`/`compile_only`가 default다. 두 JAR list는 normalized
project-relative `.jar`이고 disjoint해야 한다. Target별 `implementations`, `external_types`와
공통 `[effects]`, `[generator]`, `[verification]`은 선택이다.

모든 content path는 project-relative normalized path이고 absolute path, `..`, symlink와 overlap을
거부한다. `[project].source`, selected target source, artifact root, `tests/generated`, `.cott`는
disjoint하다. Python generated/stubs 규칙은 기존 `<artifact-root>/python|stubs`를 유지한다.
Kotlin generated는 정확히 `<artifact-root>/kotlin`이고 IR/record 및 verify-only
`library`/`runtime-libs`는 같은 artifact root 아래에서 derive한다. Executable spec만 bare name
또는 normalized path를 허용하고 실행 전에 canonical regular file로 해석한다.

`core.*`는 source tree가 아니라 compiler prelude다. Python `target.python.source`는 `_cott_impl`과
user adapter를 포함하는 durable implementation root이고 `generated`는 public Cott module,
`cott_runtime`과 verified local implementation copy를 포함하는 runtime/package root다. Python
source에는 Cott public path, `*_types` 또는 `cott_runtime` 충돌을 둘 수 없다. Python runtime과
BasedPyright search path, target metadata/lock, CPython 3.14 compatibility와 uv init 위임은
16.1–16.8의 기존 규칙을 그대로 따른다.

Kotlin `target.kotlin.source`는 binding과 `cott_impl` durable source root이고 generated Kotlin
source는 public Cott package, `cott_runtime`과 authenticated implementation copy를 포함한다.
Kotlin dependency는 manifest JAR input이며 Cott가 resolve/download하지 않는다. Python init만 uv
managed Python install/lock/sync를 위임하고 Kotlin init은 configured local toolchain만 probe한다.

Python external import에는 기존 lock/dependency provenance가 필수다. 각 target
`generation.json`은 `current`와 `last_verified`, implementation owner, target symbol,
source/runtime origin, content hash와 managed set을 자신의 closed schema로 기록한다. Kotlin
classpath/compile-only는 raw input hash와 canonical tool metadata에 함께 기록한다.
Dart source/private parts와 frozen pub/archived dependency closure는 16B를 따른다. Ordinary Flutter
app dependency resolution은 Flutter가 소유하며 Cott verification은 offline이다.

Python uv lock의 frozen registry/install provenance 규칙은 그대로 유지한다. Kotlin compiler는
dependency를 resolve/download하지 않고 manifest에 지정된 existing JAR만 검사한다. Agent
implementation은 durable source file로 지속되고 compiler는 stale managed copy만 정리한다. Cott
mutation과 같은 project를 사용하는 target runtime/build process를 동시에 실행하지 않는다.

---

## 20. 진단 메시지

오류 메시지는 단순히 파싱 실패를 알리는 수준에 머물지 않는다. 없는 member는 그 name token span에서만 보고한다. 명목 값이면 메시지는 unknown member `{name}` on `{Type}` 이고, 그 밖의 값은 unknown member `{name}` on non-nominal value 다. 후속 cascade diagnostic을 만들지 않는다. intrinsic 인자 오류가 있으면 그로부터 파생된 argument-signature 오류만 억제하고, 독립된 실제 오류는 남긴다. 새 오류 코드나 schema를 추가하지 않으며 diagnostics schema v1을 유지한다.

```text
error[COTT-T102]: incompatible nominal types

  --> python/user.py:18:15
   |
18 |     load_user(data_id)
   |               ^^^^^^^ expected `UserId`, found `InputPayloadId`
   |
   = note: `UserId` and `InputPayloadId` both wrap `U64`, but are distinct newtypes
   = help: convert explicitly using `user_id_from_data_id(...)`
```

모든 진단 record는 다음 필드를 가지며 적용할 수 없는 위치·타입은 `null`, 수정 제안이 없으면 빈 배열로 둔다.

* 오류 코드
* 위치
* 예상 타입
* 실제 타입
* 오류 원인
* 가능한 수정 방법

AI가 진단 결과를 기계적으로 수정할 수 있도록 모든 subcommand는 global `--format json`을 지원한다.

```bash
cott check --format json
cott prompt <fully.qualified.callable> --format json
cott init <path> --format json
```

`--format json`은 성공 여부와 무관하게 stdout에 다음 closed schema의 object 하나와 끝 newline만 쓰고 human prose·색상은 섞지 않는다. human mode의 stdout/stderr 정보도 JSON mode에서는 `diagnostics`의 `message`·`help`로 표현한다. source span이 있는 diagnostic은 project-relative POSIX path, start byte, source-order, code 순으로 안정 정렬하고, `span: null` diagnostic은 그 뒤에 두며 null-span끼리는 source-order, code, message 순으로 안정 정렬한다.

```json
{
  "schema_version": 1,
  "diagnostics": [
    {
      "code": "COTT-T102",
      "severity": "error",
      "message": "incompatible nominal types",
      "span": {
        "path": "python/user.py",
        "start_byte": 412,
        "end_byte": 419,
        "start_line": 18,
        "start_column": 15,
        "end_line": 18,
        "end_column": 22
      },
      "expected": "UserId",
      "actual": "InputPayloadId",
      "reason": "distinct nominal newtypes",
      "help": ["convert explicitly using user_id_from_data_id(...)"],
      "related": []
    }
  ]
}
```

byte offset은 0-based end-exclusive, line·Unicode-scalar column은 1-based end-exclusive인 15.4의 span 규칙을 따른다. `severity`는 `error`, `warning`, `note`의 closed enum이고 `related` 원소는 `{span, message}`다. source가 없는 manifest·tool·sandbox 오류는 `span: null`이다.

### 20.1 그림자 명세 경고

`COTT-K101`은 warning `possible shadow specification`이다. 실행 가능한 증거나 proof가 아니며 command exit status를 바꾸지 않는다. scanner는 declaration doc의 exact sentence와 reserved generator directive만 본다. doc candidate는 `.`, `!`, `?`, newline에서 split한 원 source byte span이며 closed ASCII case-insensitive modal `must`, `shall`, `required to`, `must not`와 facet anchor를 모두 가져야 한다. facet은 source-order `return`, `limit`, `error`, `atomicity`, `cleanup`뿐이다. ordinary 설명, implementation instruction, modal-only prose와 arbitrary generator guidance는 인식하지 않는다.

generator rules의 reserved single-line syntax는 `cott-domain <fully.qualified.callable> <return|limit|error|atomicity|cleanup>: <nonempty UTF-8 text>`다. LF만 허용하며 malformed reserved line, unknown facet, bad canonical symbol, duplicate `(symbol, facet)`는 hard diagnostic이다. 원 bytes는 prompt에 그대로 남고 scanner가 rewrite하지 않는다. formal evidence가 effective resolved `ensures`이면 return, refinement/requires/ensures이면 limit, `error`이면 error, scenario fixture/atomic assertion이면 atomicity, scenario cleanup evidence이면 cleanup candidate를 suppress한다. scenario가 없는 경우 expressible clause/effect evidence만 suppress하며 나머지는 경고로 남긴다. diagnostic은 exact sentence/directive payload span, source order와 facet order로 안정 정렬하고 generator-file finding에는 callable declaration을 related evidence로 붙인다.

---

## 21. 포맷터 규칙

cott는 idempotent한 공식 format 하나만 제공한다.

* UTF-8, LF newline, file 끝 newline 하나
* indentation 4 spaces, tab·trailing whitespace 금지
* token 사이 spacing과 operator 양쪽 한 space
* module 뒤 빈 줄 하나; contiguous `use` declaration 사이는 붙이고 그 block 뒤와 top-level declaration 사이는 빈 줄 하나
* struct field 뒤 invariant group 앞에는 빈 줄 하나, fixture/step과 clause group은 source order를 보존
* parameter·import-name·type-argument·payload·effects comma-list는 rendered line의 Unicode-scalar column 수가 100 이하이면 한 줄로 유지하고, 넘으면 결정적으로 item별 line로 나누며 grammar가 허용할 때만 trailing comma를 붙임
* contract/scenario expression은 100 column을 넘으면 괄호를 추가한 뒤 낮은 precedence operator부터 결정적으로 나눔
* literal spelling, `doc` content와 comment attachment를 보존

parse error가 있으면 file을 쓰지 않으며 `cott fmt --check`는 formatter output과 raw input bytes를 비교한다. 두 번 format한 결과가 한 번 결과와 다르면 compiler bug다.

---

## 22. v1.0 구현 범위

### 22.1 v1.0에 포함

* v0.8 grammar, const generic, heterogeneous `Tuple`, `Array`, `Buffer`, aggregate constant, guarded recursion, `struct field* invariant*`와 five closed invariant intrinsic
* canonical frozen struct constructor와 active-boundary reconstruction, Result Ok success obligation, complete conditional-error overlap/reachability evidence
* sync/async free function·trait/impl method, task-aware reentrant async impl lock, bounded protocol observation
* finite facade-only scenario state machine, closed fs/http/clock/failure fixtures, compiler-owned Linux isolated-loopback sandbox, bounded trace/transcript와 cleanup/atomicity evidence
* `COTT-K101` shadow warning, authored/deployed facade bypass audit, deterministic canonical-evidence inventory와 separated certification/coverage-policy gate
* Python closed generation v7/domain `cott.generation.v7`/runtime ABI7/strategy v5와 Kotlin closed
  generation v1/domain `cott.kotlin.generation.v1`/runtime ABI1, 공통 Canonical IR v8,
  Dart generation v1/domain `cott.dart.generation.v1`/runtime ABI1, diagnostics schema v1 및 project API version identity
* Python facade/stub/runtime/verified loader, Kotlin JVM17 module JAR, Dart portable package, target별
  static ABI·sandboxed bounded proof/runner, `current`/`last_verified` provenance,
  `tools.cott_intent` version 1, prompt/generate/diff/deploy

### 22.2 v1.0에서 제외

* `.cott` execution body, parameter default, generic overload, arbitrary call/lambda/quantifier와 user-defined fixture/plugin
* ownership, borrow checker, lifetime, arbitrary/unbounded theorem proof·candidate expansion·lifecycle observation
* Cott 밖 target call graph/effect inference, private implementation entry, mutable Cott container
  state, arbitrary `old()`, automatic refactoring/adapter/exception conversion
* 한 manifest의 simultaneous multi-target, unsupported partial backend, Cott-owned
  Android/Flutter UI/Manifest/resource/DEX/APK/AAB/signing, full IDE plugin, multi-project Python
  environment, external struct/enum direct binding
* dependency resolver/package manager, live reader transaction snapshot isolation, installed wheel whole-origin verification
* non-Linux or unsandboxed effect-fixture execution; unavailable capability is explicit unobserved, never an alternate profile

---

## 23. v1.0 완료 기준

v1.0은 다음을 모두 자동 검증할 때 완료다.

1. clean checkout의 declared project가 parse, format, IR emit, selected Python/Kotlin/Dart emit,
   generate와 explicit verify를 수행하고 target public projection/facade/runtime이 동일 IR을
   소비한다.
2. 모든 declaration/type/clause/scenario/fixture가 Canonical IR v8와 target별 closed Python
   v7/v5, Kotlin generation v1 또는 Dart generation v1 record를 통과하고 cross-target/legacy identity를 fail closed한다.
3. struct invariant의 syntax/order/type/intrinsic selector, canonical bytes/hash, direct construction, defaults/generic/recursive values와 forged facade input/return rejection을 확인한다.
4. Result error contract의 top-level Ok success obligation lint, source-order conditional predicate priority, branch reachability와 bounded runner counts/witness를 확인하며 unobserved Ok evidence는 semantic coverage policy로 선택해 gate한다.
5. pure candidate generation은 refinement/requires/invariant를 만족하고 invalid constructor candidate를 결정적으로 skip하며 zero valid case를 observation으로 위장하지 않는다.
6. scenario는 public facade resolution만 허용하고 64-step/lifecycle bounds, worker terminal state, ordered trace, assertion, cancellation·stale exclusion·coalescing observable contract와 cleanup을 확인한다.
7. fixture parser/IR/strategy는 closed fs/http/clock/failure data shape, path/route normalization, exact effect match와 effective resource ceiling을 보존한다.
8. Linux bubblewrap isolated-loopback에서만 fixture observation을 얻고 external network/DNS/other port/filesystem escape/subprocess/dynamic code와 capability-missing unsandboxed fallback을 거부한다.
9. fixture transcript/atomic replace/encoding/redirect/failure occurrence/cleanup evidence는 bounded deterministic logical data만 기록한다.
10. `COTT-K101`은 exact doc/directive span과 formal-evidence suppression만 사용하고 ordinary prompt prose, semantic proof와 command exit을 바꾸지 않는다.
11. authored/deployed Python tree는 facade allow/deny matrix, exact generated implementation role/hash, no-follow/single-link rule과 all-violation diagnostic ordering을 통과한다.
12. semantic coverage는 IR inventory와 runner evidence만 join하여 `observed|unobserved|trust_declaration|unknown`을 만들고 policy-selected clause만 gate한다.
13. artifact verification은 policy 전 evidence와 `verified=true` snapshot을 atomic publish하며 policy failure를 exit `8`로 반환해도 runtime loader의 artifact trust와 `last_verified` baseline을 되돌리지 않는다.
14. `cott diff`는 project API version만 비교하고 compiler/package/wire version은 compatibility reader/writer boundary에서만 비교한다. example project public version은 `0.1.0`으로 유지한다.
15. agent/binding/implementation provenance, strict type checking, exact verified loader, transaction recovery, diagnostics v1, formatter idempotence와 init atomicity의 기존 guarantees를 보존한다.
16. Kotlin verification은 JVM17 module JAR와 coroutine runtime dependency를 실제 compile/run하고,
    erased generic/abstract associated observation을 과장하지 않으며 Android app lifecycle과
    certification boundary를 혼합하지 않는다.

---

## 24. 구현 언어 및 내부 구조

cott compiler는 Rust single crate다. Common `manifest`, `project`, parser/CST/AST/HIR/typeck,
`contract`, `ir`, `intent`, `agent`, `sandbox`, `transaction`, `diagnostics`, `formatter`, `lsp`와
unchanged Python emit/runtime/verify modules, `kotlin::{binding,emit,runtime,provenance,pipeline,
verify,runner,prompt,generation}`을 둔다. Emitter는 AST를 직접 참조하지 않고 모든 target contract
meaning은 Canonical IR, target connection은 exactly-one manifest에서 얻는다. Implementation
body/source origin/agent run은 durable provenance이고 verification result cache는 없다. LSP는
Python-only metadata를 요구하지 않고 두 target project의 parser/HIR editor analysis만 제공한다.
`cott prompt`는 선택 target prompt를 publication 없이 렌더한다.

---

## 25. 향후 확장

v1.0의 struct invariant, success/conditional-error coverage, fixture/workflow scenario, shadow warning, semantic coverage gate와 facade audit은 모두 구현 계약이다. 이 문서에는 이 기능의 partial profile, legacy reader, unsandboxed fallback 또는 second source of truth가 없다.

### v1.0 이후

* package installation
* IDE plugin
* official additional backend와 complete target parity

---

## 26. 핵심 설계 결정 요약

### 결정 1

cott는 실행 본문이 없는 선언형 계약 DSL이며 `.cott`와 typed Canonical IR이 의미 원본이다.

### 결정 2

MVP module graph는 비순환이고 source path mapping은 injective며 package 가능한 module은 최소 두
segment다. `core.*`와 target별 `cott_runtime`, Python `_cott_impl`/`*_types`, Kotlin `cott_impl`,
Dart private implementation parts와 `_cott_` compiler namespace를 예약한다.

### 결정 3

MVP type system은 fixed-width scalar, const generic, declared variance, heterogeneous tuple, Array/Buffer, guarded recursive nominal type, immutable struct/enum/resource, struct cross-field invariant/canonical constructor, associated type·inherited structural trait·specialization과 sealed `Dyn`을 가진 Cott-owned stateful impl을 제공한다.

### 결정 4

trait default/specialization facade dispatch, associated type, resource transition, transitive Cott effect check와 sync/async free·trait/impl callable은 구현되었다. async impl은 task-aware reentrant serialization과 cancellation invariant boundary를 가지며, `boundary`와 contract-test context의 async protocol wrapper는 모든 실제 operation을 강제한다. bounded observation evidence는 configured prefix에서 실제 관찰한 operation만 주장한다. ownership, unbounded lifecycle semantics와 unbounded proof는 범위 밖이다.

### 결정 5

계약 표현식은 닫힌 순수 언어다. pattern과 clause는 typed IR이고 constant reference identity, allowed-error exhaustiveness, Result.Ok success obligation과 source-order conditional-error applicability/priority evidence를 결정적으로 보존한다.

### 결정 6

Python ABI의 표준 identity는 project identity를 embed한 generated `cott_runtime` 하나가 소유한다. alias·trait, impl class, custom enum union·keyword-only frozen variant, struct·newtype, public constant와 resolved public callable의 공개 projection을 구분 없이 보존한다.

### 결정 7

`F32` binary32 normalization은 runtime mode와 무관하며 contract 산술의 매 operation에도 적용한다. integer range는 검사가 활성화된 concrete ABI boundary에서 확인하고 `off`에서는 trust declaration으로 남긴다.

### 결정 8

검증은 proof v2의 sound `proved`, counterexample `disproved`, `unknown`, runtime 검사, test 관찰, 미관찰과 trust declaration을 분리해 실제보다 강하게 보고하지 않는다.

### 결정 9

자동 계약 테스트는 유효한 bounded pure callable input과 deterministic impl init case를 staged facade를 통해 deny-by-default OS sandbox에서 실행한다. fixture-authorized effect scenario는 같은 facade-only boundary에서만 실행하며 pure async protocol은 wrapper가 모든 실제 operation을 강제하고 configured lifecycle prefix만 관찰한다. scenario 없는 effectful callable과 `Never` 반환 callable은 observation으로 위장하지 않는다.

### 결정 10

Python free function은 manifest의 plain top-level binding이거나 함수별 `_cott_impl` source다. 각 implementation file은 exact canonical function 하나로 Cott의 최소 public/observable contract를 충족하며 private helper와 literal `Final` constant는 같은 hashed/provenanced file의 비공개 구현 detail이다. explicit impl method는 agent-only canonical private sync/async function source이고 compiler가 ordinary slotted class·init·sync `RLock` 또는 task-aware async lock·public wrapper를 소유한다. default/specialization slot에는 agent source가 없다. local module은 canonical path의 generated runtime copy로 고정한다. 연결 정보는 Canonical IR가 아니라 target manifest와 provenance에 둔다.

### 결정 11

binding은 import 없이 staged type module에 대해 정적으로 해석한다. 모든 external implementation import에는 frozen production dependency closure의 selected lock hash와 observed installed distribution provenance가 필수며 archive-to-install 연결은 증거가 없으면 trust declaration이다.

### 결정 12

Python caller는 Cott path의 typed facade만 사용한다. Facade는 embedded provenance로 local
implementation copy와 external dependency를 preflight한 뒤 canonical name당 하나의 implementation
module만 lazy load한다. Python authored/deployed audit은 `_cott_impl`·`cott_bindings`
direct/dynamic bypass와 public re-export를 거부한다. Kotlin public/private module boundary는 16A를
따른다.

### 결정 13

Python의 `off`, `boundary`, `test-only`는 facade bytes에 compile-time specialize되어 optional
callable ABI/contract 검증 범위만 바꾸며 provenance, F32 normalization, newtype/impl state
guarantee와 sync/async containment는 끄지 않는다. Kotlin mode는 16A의 compiled runtime/facade
projection에 고정되고 verify-only certification이나 source provenance를 끄지 않는다.

### 결정 14

`cott generate`는 user-selected Codex CLI, direct Claude Code CLI 또는 OMP CLI를 callable별 process로, shell 없이 single-file write sandbox staging에서 호출한다. OMP가 Claude model을 선택해도 direct Claude adapter가 되지 않는다. `cott prompt`는 같은 초기 prompt를 provider 없이 검사한다.

agent는 실제 project를 쓰지 않고 선택 free-function 또는 impl-method file만 변경한다. scratch와 cache는 workspace 밖으로 격리한다.

### 결정 16

compiler output은 현재 IR과 command-owned scope에서 계산해 stale file을 정리한다. 성공 승격된 agent implementation은 durable source라 자동 삭제하지 않고 stale 상태만 진단한다.

### 결정 17

변경 command는 project lock, 시작·종료 hash, immutable pre-image journal, durable post-image와 atomic state marker를 사용한다. crash 뒤 old 또는 new complete snapshot으로 복구한다.

### 결정 18

runtime reader snapshot isolation은 보장하지 않는다. runtime은 authored `.cott`를 live로 읽지 않고 generated facade만 load한다. 변경 중 같은 project process를 실행하지 않고 배포는 완료 뒤 새 process로 시작한다.

### 결정 19

`generation.json.current`는 latest emitted epoch, `last_verified`는 latest artifact-verified historical baseline이다. fmt·emit·generate는 후자를 보존한다. verify는 complete evidence와 `semantic_coverage`를 publish한 뒤 policy failure도 baseline과 violation을 남긴 채 CI gate만 실패시킨다. pending unresolved가 있으면 verify는 실패한다.

### 결정 20

partial generate는 verified baseline의 기존 비선택 declaration과 symbol을 보존하되 새 declaration 추가는 허용하고, 최초 baseline 전에는 selected callable scope만 생성할 수 있다. 어느 경우도 배포 상태가 아니다.

### 결정 21

MVP는 generation·verification result cache를 두지 않고 emit·generate와 full verify를 매번 실행한다.

### 결정 22

배포 gate는 unresolved가 없고 current hash가 일치하는 full `cott verify`이며 selected semantic coverage policy가 허용하지 않는 status가 없을 때만 성공한다. artifact verification과 policy gate는 같은 boolean이 아니다.

### 결정 23

BasedPyright 검증은 user config가 아니라 compiler-owned strict config를 사용하며 유일한 diagnostic override는 cott static verifier가 대체하는 `reportInvalidTypeVarUse`다.


### 결정 24

MVP compiler host와 runtime target은 같은 OS family·architecture의 `x86_64` 또는 `arm64` Linux/macOS CPython 3.14이며, generated artifact는 configured CPython full patch version에 고정되고 Python environment당 cott project 하나다.

### 결정 25

`generation.json`과 `generation_id`, exact tool·runtime identity와 managed artifact hash는 machine-local state다. cross-machine diff는 ID 자체가 아니라 normalized contract·public symbol, durable implementation content와 normalized lock·dependency identity를 비교한다.

### 결정 26

`cott init`은 absent target에 selected Python/Kotlin/Dart minimal module scaffold만 만든다.
Python은 uv에 supported Python install/lock/sync를 위임하고 Kotlin/Dart는 installed toolchain을
probe한다. Cott는 dependency resolver/package manager나 Android/Flutter app scaffolder가 아니다.
### 결정 27

struct 생성·facade boundary·IR은 하나의 canonical constructor/invariant 의미를 공유한다. direct Python construction, fixture, runner, loader 어느 경로도 별도 validation profile을 갖지 않는다.

### 결정 28

success/conditional branch observation, scenario trace, fixture transcript와 semantic coverage는 provenance에 closed evidence로 남는다. proof와 doc은 이를 대체하거나 observation을 승격하지 않으며 `verified`와 CI policy도 같은 상태가 아니다.

### 결정 29

effect scenario는 compiler-owned fs/local HTTP/clock/failure adapter와 Linux isolated-loopback sandbox에서만 observed다. capability가 없으면 fail-closed unobserved이며 unsandboxed execution은 지원하지 않는다.

### 결정 30

Python facade는 유일한 public implementation entry이며 authored/deployed tree의
`_cott_impl`·`cott_bindings` direct/dynamic import, public re-export와 unsafe link/artifact shape를
verify가 거부한다. Kotlin consumer는 compiled Cott public package만 사용하고 `cott_impl`/
`cott_bindings`를 import하지 않는다.
Dart consumer는 deployed package의 generated module facade를 사용하며 private part를 독립
library로 import하거나 compiler-private state/control을 직접 참조하지 않는다.

### 결정 31

Manifest는 Python/Kotlin/Dart target 하나만 선택한다. Kotlin과 Dart는 Python compatibility
field를 재사용하지 않는 독립 generation-1/runtime-1 backend다. 각각의 domain은
`cott.kotlin.generation.v1`와 `cott.dart.generation.v1`이며 explicit verify만
`current == last_verified` certification을 publish한다.

### 결정 32

Kotlin deployment는 compiled `cott-module.jar`, closed metadata, exact coroutine/runtime classpath
JAR만 제공한다. Kotlin stdlib는 Kotlin/Gradle이 제공하고 compile-only dependency는 배포하지
않는다. Android UI/Manifest/resource/DEX/APK/AAB/signing/device lifecycle은 standard
Gradle/Android boundary이며 Cott는 이를 소유하거나 Python을 on-device 실행하지 않는다.
