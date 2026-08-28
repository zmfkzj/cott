# cott 기본 설계 문서

**문서 상태:** Draft v0.3
**프로젝트명:** cott
**파일 확장자:** `.cott`
**CLI 명령:** `cott`


## 0.3 릴리스 호환성

이 문서는 구현된 v0.3 언어와 Python backend를 규정한다. CPython `>=3.14.6,<3.15`, BasedPyright `>=1.39.9`, uv `>=0.12.3`, Codex CLI `>=0.147.0`, OMP `>=17.2.12`를 지원한다. 각 tool version은 이 lower bound 이상이어야 하며, full version과 content hash는 provenance에 기록한다.

Canonical IR schema는 **v5**, generation record schema는 **v2**, Python runtime ABI는 **2**다. 이 세 compatibility number는 generation snapshot에 함께 기록하며, 현재 값과 다른 record·runtime은 읽거나 load하지 않는다. `[project].version`의 제한된 `x.y.z` 값은 compiler version이 아니라 공개 API version이며 generation snapshot의 `project_version`과 facade runtime identity가 반드시 일치한다.

`emit python`과 `verify`는 agent를 호출하지 않는다. agent 호출은 `generate`에서만 조건부로 수행한다. 기존 project command의 `--project <dir>`은 subcommand 뒤 어느 위치에서나 한 번만 허용하며 기본은 현재 directory다. `init`은 target path를 받고 `--project`를 거부한다.
---

## 1. 개요

cott는 함수, 데이터 구조, 오류, 제약 조건을 정밀하게 선언하고, 이를 기반으로 AI 구현을 생성하거나 기존 구현을 안전하게 연결하는 **정적 타입 기반 계약 DSL**이다.

cott 자체는 범용 프로그래밍 언어가 아니다. 반복문, 분기문, 네트워크 호출, 파일 입출력 같은 실제 구현 기능을 제공하지 않는다.

cott의 역할은 다음 세 가지로 제한한다.

1. 프로그램의 구조와 타입을 선언한다.
2. 구현이 지켜야 할 계약을 선언한다.
3. 생성되거나 binding된 코드가 선언된 계약과 일치하는지 검증한다.

기본 대상 언어는 Python이다. Cott의 우선순위는 선언으로 agent intent를 완전하게 고정하는 것, 그 intent를 target ABI로 결정적으로 투영하는 것, 그리고 실제 확보한 검증 capability만으로 evidence를 보정해 보고하는 것이다. Implementation selection과 runtime observation은 이 순서를 바꾸거나 declaration의 의미를 대체하지 않는다.

```text
.cott 계약
    ↓
파싱 및 타입 검사
    ↓
정규화된 IR 생성
    ↓
Python 타입 생성 및 기존 구현 바인딩 해석
    ↓
미구현 함수가 있으면 사용자가 지정한 에이전트 호출
    ↓
Python 공개 facade 생성
    ↓
정적 타입 검사 및 계약 검증
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

Python 구현은 에이전트가 생성하거나 기존 project function에 명시적으로 binding할 수 있다. 선언된 external type은 semantic Cott identity이며 Python emitter가 `[target.python.external_types]` projection으로 해석한다. API 계약이 다를 때만 project-local typed adapter가 이를 맞춘다. test code, 문서와 agent 구현 지시는 모두 cott 선언에서 파생된다.

생성되거나 바인딩된 Python 구현이 cott 선언과 충돌하면 Python 구현이 잘못된 것으로 판단한다.

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

v0.3에서도 다음 기능은 구현하지 않는다.

* 범용 코드 실행
* 반복문
* 일반적인 조건문
* 클래스 상속
* 메타프로그래밍
* 매크로
* 런타임 리플렉션
* 임의 Python 코드 삽입
* Rust ownership
* borrow checker
* lifetime
* async impl method, async iterator와 async generator
* 완전한 정리 증명
* cott 자체의 프로그램 합성 엔진

`async fn`은 top-level free function의 명시적 callable kind로만 구현되어 있다. 기존 `fn`을 event loop·thread로 감싸거나 동기 facade로 중계하지 않으며, impl method·async iterator·async generator의 lifecycle/취소 의미는 아직 정의하지 않았으므로 거부한다.

특히 ownership과 lifetime은 MVP에서 제외한다.

이 기능은 Rust의 메모리 모델과 결합되어 있으며, Python 구현 계약에 그대로 적용하면 실제 의미 없는 장식이 될 가능성이 크다.

cott는 Rust 전체가 아니라 다음 개념만 빌린다.

* 명목 타입
* 구조체
* 열거형
* 제네릭
* trait 기반 제약
* `Option`
* `Result`
* 명시적 변환
* 엄격한 오류 모델
* 타입을 통한 상태 표현

---

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

다만 `doc`의 자연어는 implementation conformance를 판정하는 executable contract가 아니다. 보증 등급은 type·`requires`·`ensures`·`error`·`effects`에만 부여하며 `doc`만 바뀐 경우 diff는 `DOCUMENTATION`이다.

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
Factory[Concrete]
```

`Tuple`은 하나 이상의 heterogeneous type argument를 갖는 immutable native tuple이다. empty tuple type은 source type으로 제공하지 않고 `Tuple[T, ...]` 같은 homogeneous variadic shorthand도 없다. `Array[T, N]`은 `N`개의 같은 type 원소인 immutable fixed-length container, `Buffer[N]`은 정확히 `N` byte인 immutable buffer다. `N`은 `U8`·`U16`·`U32`·`U64` const parameter 또는 그 type의 compile-time constant expression이어야 한다. `Iterator[T]`는 `T`를 lazy하게 생산하는 값을, `Generator[Y, S, R]`는 yield `Y`, send `S`, completion `R`을 나타낸다. lazy value의 생성은 소비나 effect 발생을 뜻하지 않으며 iteration, `send`, termination, close의 lifecycle에서만 관찰 가능한 effect를 evidence로 기록한다.

예시:

```cott
struct Collection[const N: U32]:
    entries: Array[User, N]
    by_id: Map[UserId, User]
    description: Option[Str]
```

컨테이너는 불변이며 type과 const argument 모두 invariant다.

Python 공개 ABI는 `CottList[T]`, `CottSet[T]`, `FrozenMap[K, V]`, native `tuple[...]`, `CottArray[T, Literal[N]]`, `CottBuffer[Literal[N]]`를 각각 사용한다. list/set/map wrapper는 private tuple/frozenset/mapping-proxy backing을, Array는 private tuple을, Buffer는 exact `bytes`를 보관한다. 모든 wrapper는 read-only operation만 노출하고 raw Python container를 공개 경계에서 암묵 변환하지 않는다. `CottArray(values=(...))`와 `CottBuffer(data=bytes.fromhex("..."))`가 generated constant constructor다.

```text
List[Dog]는 List[Animal]의 하위 타입이 아니다.
```

공변성과 반공변성은 v0.3 범위 밖이다.

`Set[T]`의 `T`와 `Map[K, V]`의 `K`는 compiler의 hash-stable 타입이어야 한다. 허용되는 기반 타입은 `Bool`, 정수, `Str`, `Bytes`, `Path`와 이들로만 구성된 newtype·payload 없는 enum·어떤 arity의 tuple이다. float, struct, Array/Buffer를 포함한 nominal container, `JsonValue`, `Opaque`, trait와 type parameter는 key position에서 거부한다.

`Factory[Concrete]`는 구현 class object를 나타내는 prelude type이다. bracket 안에는 정확히 하나의 type만 쓸 수 있다. alias를 먼저 해소한 결과가 type argument 없는 impl declaration일 때만 허용한다. 따라서 trait, external type, struct, enum, newtype, alias가 남은 type, type parameter와 type argument가 있는 named type은 허용하지 않는다.

`Factory`에는 source value literal이나 constructor syntax가 없다. `Concrete`의 compiler-generated init signature가 Python ABI의 호출 signature를 정하며, Factory 값의 validation은 그 class object를 호출하지 않는다. Factory는 hash-stable이 아니므로 `Set` element나 `Map` key가 될 수 없고, impl `state` field에도 둘 수 없다. 자동 contract test는 Factory candidate를 만들지 않는다.

### 5.5 어휘와 선언 문법
source는 UTF-8이다. identifier는 ASCII `[A-Za-z_][A-Za-z0-9_]*`로 제한한다. module·function·field·parameter·resource state는 `snake_case`, type·trait·enum variant는 `UpperCamelCase`, constant는 `UPPER_SNAKE_CASE`다. `module`, `use`, `alias`, `newtype`, `where`, `struct`, `enum`, `trait`, `impl`, `for`, `state`, `resource`, `initial`, `terminal`, `transition`, `transitions`, `invariant`, `init`, `const`, `external`, `type`, `fn`, `async`, `self`, `doc`, `rule`, `override`, `delete`, `remove`, `requires`, `modifies`, `ensures`, `when`, `with`, `matches`, `error`, `effects`, `old`, `true`, `false`, `and`, `or`, `not`은 keyword다. `result`는 pattern 없는 `ensures` expression scope에서만 예약되는 contextual keyword이므로 field와 payload에서는 사용할 수 있다. prelude type 이름도 user declaration으로 가릴 수 없다.

Python target validation은 CPython 3.14 hard keyword와 단독 `_`를 identifier로 거부하고 `_cott_` prefix 또는 `__`로 시작하거나 끝나는 user name도 예약한다. target projection 뒤 모든 이름에 같은 검사를 적용하므로 emitter가 identifier를 escape하거나 rename하지 않는다.

일반 문자열은 JSON escape를 사용하는 double-quoted literal이고 `doc`만 triple double quote를 사용한다. 정수는 10진수, float는 소수점 또는 exponent가 있는 10진수이며 빈 괄호 `()`는 `Unit` literal이다. 부호는 literal이 아니라 unary operator다. tab과 semicolon은 금지한다. parser는 일관된 space indentation을 받고 formatter는 4칸으로 정규화한다. `#`부터 newline까지는 comment다. blank 또는 comment-only physical line은 `NEWLINE`, `INDENT`, `DEDENT` token을 만들지 않는다.

다음 EBNF가 v0.3의 선언 surface다. `INDENT`와 `DEDENT`는 indentation token이고 `{x}`는 0회 이상, `[x]`는 선택이다.

```text
file          = module_decl, { use_decl }, { declaration } ;
module_decl   = "module", qname, NEWLINE ;
use_decl      = "use", qname, [ ".{", name_list, "}" ], NEWLINE ;

declaration   = ( [ doc_block ], ( alias_decl | newtype_decl | struct_decl
                | enum_decl | trait_decl | resource_decl | rule_decl | const_decl
                | external_type_decl ) ) | fn_decl | impl_decl ;
external_type_decl = "external", "type", type_name, NEWLINE ;
alias_decl    = "alias", type_name, "=", type, NEWLINE ;
newtype_decl  = "newtype", type_name, "(", type, ")", NEWLINE,
                [ INDENT, "where", expression, NEWLINE, DEDENT ] ;
struct_decl   = "struct", type_name, [ generic_params ], ":", NEWLINE,
                INDENT, field, { field }, DEDENT ;
enum_decl     = "enum", type_name, [ generic_params ], ":", NEWLINE,
                INDENT, variant, { variant }, DEDENT ;
trait_decl    = "trait", type_name, [ generic_params ], ":", NEWLINE,
                INDENT, { associated_type }, trait_method, { trait_method }, DEDENT ;
associated_type = "type", type_name, [ ":", trait_ref, { "+", trait_ref } ], NEWLINE ;
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
impl_method   = "fn", function_name, "(", "self",
                [ ",", parameter_list ], ")", "->", type, ":", NEWLINE,
                INDENT, method_clause, { method_clause }, DEDENT ;
const_decl    = "const", const_name, ":", type, "=", const_expr, NEWLINE ;
const_expr    = expression | qname, "(", const_expr, ")" | "Tuple", "(", [ const_expr, { ",", const_expr } ], ")"
              | "Array", "(", [ const_expr, { ",", const_expr } ], ")" | "Buffer", "(", string_literal, ")" ;

field         = field_name, ":", type, [ "=", const_expr ], NEWLINE ;
variant       = variant_name, [ "(", parameter_list, ")" ], NEWLINE ;
trait_method  = "fn", function_name, "(", "self", [ ",", parameter_list ], ")", "->", type,
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
doc_block     = "doc", triple_string, NEWLINE ;

generic_params = "[", generic_param, { ",", generic_param }, [ "," ], "]" ;
generic_param = type_name, [ ":", trait_ref, { "+", trait_ref } ] | "const", const_name, ":", const_kind ;
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

external declaration은 target이나 source path를 갖지 않는 semantic named Cott type이다. AST와 HIR은 common declaration metadata와 name만 보존하며 `target`·`path` field를 두지 않는다. Canonical IR v5의 `external_type` declaration도 `annotations`, `doc`, `kind`, `name`, `public`, `source_order`, `span`만 가지며 target projection은 절대 serialize하지 않는다.

각 backend는 자신의 manifest projection table로 external declaration을 해석한다. Python에서는 `[target.python.external_types]`의 quoted fully qualified Cott external symbol을 key로, `module:Qualname`을 value로 사용한다. key는 존재하는 external declaration과 정확히 일치하고 value는 안전한 Python module/qualname이어야 한다. mapping의 누락·stale key·non-external key·malformed value는 emit 전에 hard error다. Target-side import or signature inspection은 별도 capability이며 declaration validity나 IR을 바꾸지 않는다. Rust와 TypeScript target/table은 구현되어 있지 않다.

`()`·`[]`·`{}` 안에서는 newline과 indentation token을 무시한다. clause expression은 한 logical line이어야 하며 여러 줄로 나누려면 괄호 안에 작성한다. `impl` body의 순서는 associated assignment, optional `state`, 0개 이상의 `invariant`, optional `init`, 하나 이상의 method다; assignment·state·init은 각각 최대 한 번의 해당 member로만 나타난다. `init`과 method block은 비어 있을 수 없고, `doc`은 최대 하나이며 첫 절이어야 한다. `requires` 뒤에는 method `transitions`, `modifies`, `ensures`, `error`, `effects`가 이 순서로 오며 `transitions`·`modifies`·`effects`는 각각 최대 하나다. init에는 `error`, `effects`, `transitions`, `modifies`가 없다.

function block에는 `doc` 최대 하나, `rule`, `requires`·`ensures`·`error` 각 0개 이상, `effects` 최대 하나가 이 순서로 온다. `rule`은 explicit clauses보다 앞에 오며 rule definition의 add/override/delete action으로 contract clauses를 합성한다. top-level `doc`은 바로 다음 type, resource, rule 또는 constant declaration에 붙으며 orphan·중복 doc은 오류다.

expression precedence는 낮은 순서로 `or`, `and`, unary `not`, comparison, `+ -`, `* / %`, unary `+ -`, field/`.len`, primary다. comparison은 `== != < <= > >=`이며 연쇄 비교를 허용한다. primary는 scalar literal, `Unit` literal `()`, 현재 scope의 name·constant·enum singleton과 괄호식, method `ensures`에서만 쓰는 `old(self.field)`이다. 임의 call, index, collection literal과 attribute method call은 계약 표현식에 없다.

arithmetic operand는 같은 numeric type이어야 한다. `/`는 float에만, `%`는 integer에만 허용하고 unary `-`는 unsigned type에 허용하지 않는다. integer contract 중간값은 declared width를 넘을 수 있는 mathematical integer며 remainder는 `0 <= r < abs(divisor)`인 Euclidean remainder다. emitter는 `%`를 Python operator가 아니라 `cott_runtime._cott_euclidean_mod`로 낮춘다. zero divisor는 compile-time constant에서 semantic error, runtime clause에서 `CottContractViolation`이다. `F32` 중간 결과는 매 연산 후 binary32, `F64`는 binary64로 평가한다. compiler constant evaluator와 runtime clause·refinement evaluator는 같은 규칙을 쓴다.

```text
pattern = "_" | binding_name
        | qname, [ "(", [ pattern, { ",", pattern } ], ")" ] ;
```

`scrutinee matches pattern => condition`은 `requires`, `ensures`, invariant의 통일된 guard다. guard가 match할 때만 condition을 평가하며 binding은 condition scope에만 들어간다. `ensures Pattern => condition`은 호환 syntax로 `result matches Pattern => condition`이다. `error E with scrutinee matches pattern [when condition]`은 error guard와 optional boolean obligation을 함께 쓴다. pattern의 payload arity와 타입은 scrutinee type에 대해 검사한다.

---

## 6. 사용자 정의 타입

user type declaration은 같은 module의 forward reference를 사용할 수 있지만 alias·newtype·struct·enum·trait·impl dependency graph 전체가 acyclic이어야 한다. container로 감싼 self-reference도 MVP에서는 거부하고 emitter는 resolved DAG를 topological order로 생성한다.

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

trait는 Python 객체가 구조적으로 제공해야 하는 method signature와 optional associated type·default facade dispatch를 선언한다.

```cott
trait Repository[Entity, Id]:
    type Item
    fn find(self, id: Id) -> Result[Option[Entity], RepositoryError]
    fn save(self, entity: Entity) -> Result[Unit, RepositoryError]
```

trait는 비어 있을 수 없고 associated type은 method보다 앞에 와야 한다. associated type은 `type Name` 또는 trait-bound `type Name: Bound + OtherBound`이며 type parameter처럼 declaration-scoped identity를 가진다. trait method에는 generic parameter, body, `doc`, inline contract와 `effects`를 붙일 수 없다. 다만 `fn method(...) -> T = module.free_function`은 하나의 declared synchronous free function을 default dispatch로 지정한다. 그 function은 exact substituted receiver-first signature를 갖고 verified public facade로 해석되어야 하며, impl이 method를 명시적으로 선언하지 않으면 compiler wrapper가 그 facade를 호출한다. default를 선택한 method는 default function의 contract/effects를 그대로 사용하고 `modifies`는 빈 set이다. default dispatch는 dynamic trait dispatch가 아니며 impl class의 concrete public wrapper를 위한 정적 선택이다.

`impl Concrete for Trait [+ Trait ...]:`는 `Concrete`라는 새롭고 유일한 nominal Cott type을 선언하고, 나열한 structural trait를 구현하는 Cott-owned stateful class를 만든다. `Concrete`는 generic parameter를 가질 수 없고 같은 module의 다른 declaration 이름과 충돌할 수 없다. 각 `trait_ref`는 해석 후 trait여야 하며 중복될 수 없다. trait reference의 type argument를 치환한 뒤 같은 method 이름이 둘 이상이면 parameter 이름·순서·resolved type과 return type이 정확히 같아야 하고, 다르면 HIR error다. 이 합집합의 각 slot은 exact explicit method 또는 그 trait의 default 중 하나로 선택된다. default 없는 slot은 explicit implementation이 필수다.

impl은 자신이 구현하는 각 associated type을 정확히 한 번 `type Name = ConcreteType`으로 지정한다. 여러 trait가 같은 associated name을 요구하면 assignment는 모호하여 거부한다. assignment는 cyclic projection일 수 없고 모든 declared bound를 만족해야 한다. trait method signature의 `Trait.Associated` projection은 selected impl class의 assignment로 치환되어 Python ABI·stub·wrapper signature에 나타난다.

`state` field는 source order의 고정된 instance storage다. type은 alias를 해소한 뒤 concrete이고 닫힌 ABI immutable Cott value type, projected `external type`, `Opaque["tag"]` 또는 resource type이어야 한다. `Never`, trait, type parameter와 `Factory`는 state type이 될 수 없다. external value의 in-place mutation은 Cott state transition으로 관찰하지 않으며 선언된 effect의 책임이다. required field는 default field보다 앞에 오며 default는 field type의 compile-time `const_expr`여야 한다. wrapper는 method 전 state field reference를 복사 없이 snapshot하고 slot identity로 replacement를 판정한다.

`Option` state default는 compile-time absence value `Option.Nothing`을 사용한다. state에 required field가 하나라도 있으면 `init`은 필수다. explicit `init`의 parameter는 state field와 같은 선언 순서의 subsequence이고, extra·중복 parameter는 없으며, 모든 required field는 같은 name과 exact resolved type의 parameter를 가져야 한다. default field parameter는 생략할 수 있고 생략하면 state default를 쓴다. `init`이 없으면 required state field도 없어야 하며 compiler가 모든 default를 채우는 zero-argument init을 합성한다. state가 없으면 `init`은 쓸 수 없고 zero-argument init만 합성한다. init assignment는 compiler-owned이며 agent body가 없다.

invariant expression은 `Bool`이어야 하며 scope는 `self`와 constant뿐이다. 통일된 guard를 쓰면 match binding도 condition scope에 들어간다. invariant는 init assignment와 init `ensures` 뒤, 그리고 method helper가 정상 반환한 뒤 반환값을 공개하기 전에 검사한다; `Result` method의 `Ok`와 `Err` 모두 정상 반환이다. helper exception이나 failed precondition은 정상 반환이 아니므로 invariant를 실행하지 않는다.

explicit impl method는 선택된 trait slot의 name·parameter name/order/type·return type과 exact match해야 하며 그 밖의 method를 선언할 수 없다. method `doc`, `requires`, guarded `ensures`, `error`, `effects`는 top-level function과 같은 의미를 가지며 scope에 `self`를 추가한다. `modifies`가 없으면 모든 non-resource state field가 호출 전과 같은 object identity를 유지해야 한다. 있으면 나열한 distinct non-resource state field만 다른 object로 교체할 수 있으며, 이는 permission이지 변경 의무가 아니다. `transitions self.field: Resource.from -> Resource.to`는 resource-typed impl state field에만 쓸 수 있고 해당 resource의 declared edge여야 한다; wrapper는 pre-state가 `from` singleton이고 post-state가 `to` singleton인지 identity로 검사한다. resource field는 `modifies`에 둘 수 없고 transition field도 `modifies`와 겹칠 수 없다. external object mutation을 관찰하지 않는다. `old(self.field)`는 snapshot reference를 읽고 method `ensures`에서만 허용된다.

Concrete에는 inheritance·subclassing·dynamic attribute·`__del__`가 없으며 identity equality와 identity hash만 제공한다. compiler-owned slotted shell, init, per-instance `RLock`, public wrappers와 ABI/contract/invariant/modifies/transitions checks를 제외한 implementation ownership은 없다. public method call은 같은 instance의 lock으로 직렬화한다. `close`는 magic lifecycle hook이 아니라 trait가 선언하고 impl이 위 규칙으로 구현하는 ordinary resource transition이며 implicit cleanup은 없다.

각 explicit impl method의 agent implementation은 canonical symbol `<module>.<Concrete>.<method>`, durable path `python/_cott_impl/<module>/<Concrete>/<method>.py`, 그리고 그 symbol과 exact signature를 가진 private top-level canonical function `_cott_impl_<Concrete>_<method>` 하나를 가진다. trait default-selected method에는 agent implementation file이 없다. implementation file의 private helper와 permitted literal `Final` constant 규칙, static Protocol checking, target checker suppression 정책은 기존 free-function 규칙과 같다.

Python emitter는 `@runtime_checkable` `typing.Protocol`을 생성한다. BasedPyright와 cott static verifier가 method name, parameter kind·type와 return type을 구조적으로 비교한다. boundary checker는 parameterized Protocol에 `isinstance`를 호출하지 않고 `inspect.getattr_static`으로 origin Protocol의 required member presence만 확인해 descriptor를 실행하지 않는다. annotation과 generic 관계는 정적 보증으로 보고한다.

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
struct Page[T, const N: U32]:
    items: Array[T, N]
    total: U64

fn first[T](items: List[T]) -> Option[T]
```

const generic parameter는 `const NAME: U8|U16|U32|U64`이며 type parameter와 같은 ordered generic list에 섞을 수 있다. type use의 argument는 declaration order와 kind를 exact match해야 한다. const argument는 literal, compatible constant, arithmetic expression 또는 in-scope const parameter이고 compile time에 canonical typed value로 계산된다.

### 8.2 Trait bound와 associated projection

```cott
trait Stream:
    type Item
    fn next(self) -> Option[Stream.Item]

fn save_all[T: Serializable](values: List[T]) -> Result[Unit, SaveError]
```

복수 bound는 `T: Comparable + Serializable`로 쓴다. Python emitter는 각 trait `Protocol`을 모두 상속하는 합성 `Protocol`과 invariant `TypeVar(bound=...)`를 사용한다. `TypeVar`의 선택형 constraints로 약화하지 않는다. bound trait끼리 같은 method 이름이 있으면 parameter·return signature가 구조적으로 동일해야 하며 다르면 HIR error다. associated projection은 trait declaration identity와 associated name을 보존하고 impl selection 때 exact assignment로 치환한다.

### 8.3 제네릭 규칙

* 모든 generic type과 const parameter는 invariant다.
* 생성된 Python nominal container와 사용자 generic은 invariant `TypeVar`를 사용하며 fixed length는 `Literal[N]`으로 투영된다.
* generic type reference의 type/const argument는 exact arity와 kind로 명시한다.
* generic function 호출의 type variable은 target static checker가 argument에서 추론하며 cott에는 call expression이나 explicit call-site type argument 문법이 없다.
* bound는 중복 없는 trait type만 허용하고 미해결 type variable과 암묵적인 `Any` 대체는 오류다.
* 재귀적인 무한 타입과 cyclic associated assignment는 거부한다.

Python runtime은 지워진 `TypeVar`·const parameter 관계를 복원하거나 호출별로 통합하지 않는다. `Array[InputPayload, 3]`처럼 facade 시그니처에 statically concrete한 nested type·length는 런타임 검사할 수 있지만 generic input/return 관계는 BasedPyright와 cott static verifier의 보증이다.

---

## 9. 함수 선언

cott 함수는 실행 본문을 가지지 않는 sync 또는 explicit async free-function declaration이다. function block에는 `doc`, `rule`, `requires`, `ensures`, `error`, `effects`만 들어간다.

```cott
async fn fetch_payload(id: PayloadId) -> Result[Payload, FetchError]:
    ensures Result.Ok(payload) => payload.id == id
    effects [network]
```

`async fn`은 top-level free function에서만 허용한다. return type은 `Iterator`, `Generator`, `Never`일 수 없고 trait method·impl method·binding default dispatch는 async일 수 없다. Canonical IR, provenance, facade, stub, binding signature와 contract runner는 callable kind `sync`/`async`를 보존한다. async facade는 implementation coroutine을 같은 loader/exception boundary에서 직접 `await`하고, runner는 완료 뒤 남은 background task가 없음을 검사한다. sync/async kind 변경은 breaking이며 `asyncio.run`, thread, sync compatibility wrapper는 제공하지 않는다.

함수 오버로딩과 parameter default는 금지한다. 호출 option은 default field가 있는 struct로 묶는다. 모든 parameter는 Python positional-or-keyword parameter로 emit한다. 같은 module 안에서는 함수 이름이 유일하다.

---

## 10. 계약

### 10.1 계약 표현식

refinement, `requires`, `ensures`, `error`, invariant와 rule clause는 하나의 정규화된 순수 표현식 언어와 통일된 match guard를 사용한다.

허용 대상은 숫자·문자열·boolean·`Unit` literal, 현재 declaration parameter·constant, `ensures`의 `result`, refinement/impl의 `self`, cott field와 `.len`, method `ensures`의 `old(self.field)`, 산술·연쇄 비교·동등성·`and`·`or`·`not`이다. guard의 scrutinee는 그 clause의 base scope에서 평가되고 pattern binding은 guard condition에만 보인다. `requires`와 invariant guard는 matched 경우에만 obligation을 만든다; `ensures` guard는 normal return 뒤 match한 경우에만 검사한다. legacy `ensures Pattern => condition`은 result scrutinee shorthand다.

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

`error Variant with scrutinee matches Pattern when condition`은 match한 반환 context에서 `condition`이 참이면 해당 variant를 반환해야 하는 검사 가능한 의무다. `with` guard가 없으면 `when`은 ordinary argument/constant (`impl`은 `self` 포함) scope에서 평가한다. 둘 이상의 applicable conditional error가 참이면 source order의 첫 번째만 의무가 되고 뒤 절은 면제된다. 조건 없는 `error Variant`는 허용된 환경 실패를 선언할 뿐 항상 일치하는 조건으로 취급하지 않는다.

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

HIR은 이름이 해석되고 type expression·const value·guard가 정규화된 내부 구조다. trait의 associated declaration/default target, impl assignment와 explicit/default selected slot, resource state/edge, method transition 및 function async kind를 type-check한 뒤에만 Canonical IR로 내린다. HIR은 state type/default·init mapping·exact signature union·associated bound·guard scope·`old` field identity·modifies write-set·resource edge를 검증한다.


예를 들어 다음 두 타입 표현은 HIR에서 같은 심볼을 가리킨다.

```cott
InputPayload
system.data.InputPayload
```

### 15.4 Canonical IR

Canonical IR v5는 에이전트나 특정 언어 문법에 종속되지 않는 정규 표현이다. normative `schema_version`은 **5**이며 compiler는 emit 직전과 IR load 직후 v5 schema를 검증한다. 다음 JSON은 필드 형태를 보여 주는 비규범 표시 fragment이며 schema-conformant instance가 아니다.

실제 IR file의 top-level object는 `schema_version`, fully qualified `module`, project-relative `source`, sorted `imports`와 `declarations`를 가진다. declaration은 공통 `kind`·fully qualified `name`·`public`·`doc`·`span`을 가진다. function은 `callable_kind` (`sync` 또는 `async`), ordered generic parameter·parameter·return type·contract/effects를, trait는 associated type과 method/default free-function identity를, impl은 associated assignment·selected method slot·resource transition을, resource는 initial state·ordered states/edges를 추가한다. external type은 target projection이 아닌 semantic metadata만 가진다.

type node kind는 `primitive`, `named`, `type_parameter`, `associated_projection`, `any`, `unknown`, `list`, `set`, `map`, `tuple`, `array`, `buffer`, `option`, `result`, `iterator`, `generator`, `factory`, `opaque`로 닫혀 있다. generic argument는 type 또는 canonical const value다. alias는 IR type에서 제거하고 `named`는 fully qualified declaration과 ordered argument를 가진다. `factory` node는 type argument 없는 impl declaration의 `named` node다. expression과 match guard/pattern은 resolved cott type·symbol identity와 span을 가진다.

declaration kind와 추가 field는 닫혀 있다: `alias(target)`, `newtype(carrier, refinement)`, `struct(generics, fields)`, `enum(generics, variants)`, `trait(generics, associated_types, methods)`, `impl(traits, associated_types, state, invariants, init, methods, selected_methods)`, `resource(initial, states, terminals, edges)`, `rule(generics, base, clauses)`, `const(type, value)`, `function(callable_kind, generics, parameters, return_type, contracts, effects)`, `external_type()`. resource `terminals`는 terminal declaration의 state identity·source order·span을 별도로 보존하고 `states[].terminal` membership과 일치해야 한다. `HirClause` stores its kind-specific fields, optional typed match guard, expression, source span, and stable clause ID.

integer canonical value는 sign을 포함한 base-10 string, `F32`·`F64`는 width와 IEEE bit-pattern lowercase hex, `Bool`·`Str`은 JSON scalar, `Bytes`와 `Buffer`는 lowercase hex, `Unit`은 typed null로 저장한다. tuple/array child value는 declaration order, set element와 map entry는 typed canonical key JSON bytes order다. `Array` value의 item count와 `Buffer` byte count는 declared canonical length와 같아야 한다.

declaration, field, parameter와 contract clause array는 source order를 보존한다. 의미가 set인 effect와 import는 fully qualified name으로 정렬한다. source span은 raw UTF-8의 0-based start·exclusive-end byte offset과 1-based line·Unicode-scalar column을 함께 가진다. schema에 없는 field는 거부한다. IR JSON은 sorted key, insignificant whitespace 없음, final newline 하나로 canonicalize하고 schema version을 `generation_id`에 포함한다.

normative schema는 repository의 `schemas/canonical-ir.schema.json` (v5), `schemas/generation.schema.json` (v2), `schemas/diagnostics.schema.json`, `schemas/contract-test.schema.json`이다. 모두 JSON Schema Draft 2020-12이며 compiler binary가 embed하고 IR/generation/diagnostic/contract-strategy writer와 reader가 해당 current schema를 검증한다.

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

* Python `.pyi` 생성
* 에이전트 프롬프트 생성
* 문서 생성
* 테스트 생성
* 변경점 비교
* 다른 언어용 emitter 개발

에이전트 prompt의 semantic payload는 선택 symbol의 Canonical IR과 사람이 읽을 수 있게 렌더한 `doc`·clause·관련 type이다. raw `.cott` source는 workspace에서 read-only context로만 제공하고 agent나 target이 다시 parse한 결과를 계약 의미로 사용하지 않는다.

`contracts.requires`, `contracts.ensures`, `contracts.errors`는 원본의 모든 절을 순서대로 보존한다. 각 절은 kind별 source-order `clause_id`, source span과 resolved expression을 가진다. `ensures.pattern`은 `null`이거나 `variant`·`binding`·`wildcard`의 재귀 node며 expression과 별도로 타입 검사한다. 조건부 `error`는 source-order `priority`를, 조건 없는 `error`는 `priority: null`, `when: null`을 가진다. target은 문자열을 재파싱하지 않는다.

상수는 `{"kind": "const", "name", "type", "value", "public", "span"}` declaration으로 저장한다. 값은 compile-time canonical value다. refinement·default·contract expression의 constant reference는 항상 canonical `constant_ref` node와 symbol identity를 보존하며 Canonical IR이나 `contract_surface`에서 값으로 inline하지 않는다. target 최적화는 이 단계 뒤에만 값을 inline할 수 있다. `public_python_symbols(IR)`은 모든 공개 declaration을 alias 이름, trait `Protocol`, struct·newtype class, enum union alias·variant class, constant와 function의 결정적 Python target symbol 집합으로 투영하며 compiler-synthesized `TypeVar`·합성 `Protocol`·support name은 제외한다.

기존 구현의 import 경로는 대상 언어에 종속되므로 Canonical IR에 포함하지 않는다. 대상 emitter와 verifier가 manifest binding을 IR과 함께 해석한다.

계약 의미의 원본은 Canonical IR뿐이다. target emitter의 결정적 입력은 Canonical IR, target manifest, compiler·runtime version, exact target Python identity·platform, lockfile, 해석된 implementation symbol identity·source/runtime origin·content hash다. implementation 본문은 compiler 생성물이 아니지만 facade의 embedded provenance 때문에 emitter 입력에 포함된다.

`generation.json`은 이 입력, agent executable·version·prompt hash와 검증 결과를 기록한다. 결정적인 compiler 산출물과 비결정적인 구현 provenance를 별도 필드로 구분한다.

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
`tests/generated/<module path>/<callable>.json`은 compiler가 실행하는 deterministic managed contract-test strategy다. callable은 free function의 `<function>` 또는 impl method의 `<Concrete>/<method>`다. 닫힌 object는 `{"schema_version":1,"symbol":<FQN>,"seed":"sha256:<hex>","candidate_limit":64,"container_length_limit":3,"json_depth_limit":4,"classification":"pure"|"effectful"|"never","clause_ids":[<source-order IDs>]}`이며 generated Python source가 해석하지 않는다. impl method strategy는 여기에 deterministic `init_cases`를 추가하며, 각 case는 required state field의 named ABI value와 defaulted field를 생략할지 여부를 source order로 기록한다.

`cott_runtime` ABI **2**는 numeric alias `I8`…`U64`·`F32`·`F64`, `Option`·`Result`, `Ok`·`Err`·`Some`·`Nothing`, `Unit`·`UNIT`, `Opaque`, `CottList`·`CottSet`·`FrozenMap`·`CottArray`·`CottBuffer`, numeric metadata, `JsonValue` union·variant와 `CottContractViolation`의 유일한 runtime identity 원본이다. `Any`는 `typing.Any`, `Unknown`은 `object`, `Iterator[T]`는 `typing.Iterator[T]`, `Generator[Y, S, R]`는 `typing.Generator[Y, S, R]`로 직접 투영된다. runtime ABI value가 expected ABI 2와 다르면 facade load는 실패한다.

Python environment 하나에는 generated cott project 하나만 설치한다. `cott_runtime`과 각 facade는 normalized `[project].name`, `[project].version`, runtime ABI 2를 embed하고 서로 다르면 import를 거부한다. `generated/python`은 public cott module, runtime과 verified local implementation copy를 함께 담는 단일 runtime/package root이며 `<module>_types.py`는 user type·constant만 정의한다.

`facade_exports(IR, resolved)`는 모든 public non-callable, resolved public free function, every selected slot이 explicit implementation 또는 verified default facade로 resolved된 impl class의 합집합이다. unresolved explicit impl method만 `generation.json.current.unresolved`에 기록한다. default-selected method에는 durable implementation source·record가 없다.

`impl Concrete for Trait [+ Trait ...]`는 agent가 class를 작성하는 기능이 아니다. emitter는 ordinary `@final` class, declaration-order state slot, `_cott_lock`, compiler-owned init과 selected method wrapper를 생성한다. explicit slot은 canonical helper를 호출하고 default slot은 exact verified free-function facade를 receiver-first로 호출한다. wrapper는 associated projection이 치환된 ABI, init/invariant, non-resource modifies와 resource transition checks를 적용한다.

`generation.json`은 두 snapshot을 가진다.

* `current`: 마지막 성공 apply의 입력·구현·관리 파일 hash, unresolved 집합과 `verified` 상태
* `last_verified`: 마지막 full verify의 정규화 계약 snapshot, Python 공개 표면과 관리 파일 hash 또는 최초 검증 전 `null`

record의 필수 field를 보여 주는 다음 JSON은 객체·배열 entry 일부를 지면상 생략한 비규범 fragment이며, 그 자체로 schema-conformant record가 아니다. 실제 `contract_surface`와 `public_python_symbols`는 아래 규칙대로 축약 없이 저장한다.

```json
{
  "schema_version": 2,
  "current": {
    "generation_id": "sha256:...",
    "verified": false,
    "project_version": "0.3.0",
    "compatibility": {"generation_schema": 2, "canonical_ir_schema": 5, "runtime_abi": 2},
    "inputs": {"AGENTS.md": "sha256:...", "cott.toml": "sha256:...", "python/pyproject.toml": "sha256:...", "python/uv.lock": "sha256:...", "src/foo/bar.cott": "sha256:..."},
    "tools": {
      "compiler": {"version": "0.3.0", "executable": "/canonical/cott", "content_hash": "sha256:..."},
      "runtime": {"abi": "2", "version": "0.3.0"},
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
    "agent_runs": []
  },
  "last_verified": null
}
```

project-owned path는 project-relative POSIX path이고 dependency import origin만 distribution-relative POSIX path다. hash는 raw file bytes의 SHA-256 lowercase hex다. map key와 set-derived array를 정렬한 UTF-8 JSON으로 쓰며 file 끝 newline 하나만 둔다. `generation.json` 자체는 self-reference를 피하려고 `managed_files`에서 제외한다. `generation_id`는 canonical object `{"current": <normalized current>, "domain": "cott.generation.v2", "schema_version": 2}`의 hash이며 normalized current에서는 `generation_id`·`verified`·`verification`·`agent_runs`를 뺀다. `last_verified`는 pointer가 아니라 verified current snapshot의 deep copy다.

`agent_runs`는 현재 agent implementation content hash와 일치하는 callable별 마지막 successful run만 담는다. 이후 emit·verify에서도 hash가 같으면 보존하고 agent 재생성 시 교체하며 user edit로 hash가 달라지면 제거한다. 실패·폐기된 run과 무제한 history는 generation record에 누적하지 않는다.
implementation record의 `cott_symbol`은 free function 또는 `<module>.<Concrete>.<method>`이며 `python_symbol`은 file의 유일한 canonical contract function만 가리킨다. 같은 file의 private helper와 permitted `Final` constant는 별도 symbol·binding·facade export·provenance record를 만들지 않고 file 전체 `content_hash`로 함께 provenance된다. impl method record는 `"kind":"impl_method"`, `"concrete":"<Concrete>"`, `"method":"<method>"`, `"owner":"agent"`, `"python_symbol":"_cott_impl.<module path>.<Concrete>.<method>:_cott_impl_<Concrete>_<method>"`, `"source_origin":"python/_cott_impl/<module path>/<Concrete>/<method>.py"`와 같은 runtime origin·content hash를 반드시 가진다. `current.unresolved`도 free function과 impl method의 canonical symbol·kind·source span을 각각 기록한다. impl method에는 manifest binding record가 없고 owner는 언제나 `agent`다.

canonical executable path와 binary hash를 포함하므로 `generation_id`는 같은 machine·tool installation의 generation instance identity이지 cross-machine reproducible build ID가 아니다. portable 비교는 Canonical IR, `contract_surface`, `public_python_symbols`, durable implementation content hash와 normalized lock·dependency identity를 사용한다. exact tool·runtime identity와 machine-specific constant를 embed한 managed artifact hash는 같은 target environment 안에서만 비교한다. `generation.json`은 machine-local state이고 wheel에 포함하지 않는다.

`dependencies`는 허용된 external import마다 normalized distribution name·version, 현재 platform에서 lock이 선택한 `lock_artifact_hash`, 관찰한 installed metadata content hash와 distribution-relative module origin·content hash를 기록한다. lock artifact hash는 기대값이고 immutable archive나 검증 가능한 installer receipt가 없는 MVP 설치 환경에서 installed bytes가 그 archive에서 왔음을 증명하지 않는다. 이 연결은 명시적 신뢰 선언이며 loader는 verify가 관찰해 고정한 installed bytes를 검사한다. dependency origin은 symlink가 아닌 regular file이어야 하며 uv cache가 설치한 hardlink는 허용하고 매 load에서 content hash를 재검사한다. generated module과 standard library는 제외하며 후자는 exact CPython provenance로 고정한다. 16.5.1의 verified Cott facade import도 external dependency가 아니며 implementation AST와 Canonical IR에 대해 별도로 검증한다. 그 밖의 project-local import는 허용하지 않는다.

`contract_surface`와 `public_python_symbols`는 축약 없이 필수다. 전자는 span·source path·implementation 정보를 제외하되 declaration kind·name·public, generic, resolved type shape, field·variant·default·constant value·refinement, ordered contract clause·effect와 `doc`을 보존하는 module별 canonical diff projection이다. 후자는 15.4의 전체 target symbol을 module별로 정렬해 저장한다. `facade_exports`는 이 집합과 `implementations`·`unresolved`에서 결정적으로 유도하므로 별도 저장하지 않는다. 따라서 외부에 보관한 `last_verified` record만으로도 이전 artifact 없이 contract·documentation breaking 분류와 partial-generate surface guard를 수행할 수 있다.

`inputs`는 manifest, 모든 `.cott` source와 manifest가 참조하는 rules·target project metadata·존재하는 lockfile의 raw byte hash를 정렬해 담는다. `cott.toml`이 target manifest이므로 별도 숨은 설정은 없다.

실제 byte를 바꾼 `fmt`, `emit`과 부분 generate는 `current.verified = false`로 갱신하되 `last_verified`를 그대로 보존한다. full verify만 두 snapshot을 현재 세대로 함께 갱신한다. 파일 drift는 저장된 bit가 `true`여도 snapshot을 무효화하므로 cott와 배포 gate는 hash를 재계산한다.

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
| `trait` | structural `typing.Protocol`; default는 verified free-function facade dependency |
| `impl` | compiler-owned `@final` ordinary slotted class; selected explicit/default method wrapper |
| `resource R` | generated `R_<State>` singleton state classes와 `R` union alias |
| 복수 trait bound | 모든 bound를 상속한 합성 `Protocol` |
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
| compiler-owned impl init의 exact state assignment, `RLock`, init `requires`·`ensures`와 post-init invariant | 항상 | 항상 | 항상 |
| impl method state snapshot, declared `modifies`, normal `Ok`/`Err` return invariant | 항상 | 항상 | 항상 |
| 미선언 `Exception` → `CottContractViolation` | 항상 | 항상 | 항상 |
| `Never` 정상 반환과 `SystemExit` 재전파 조건 | 항상 | 항상 | 항상 |
| 그 밖의 public callable 경계의 eager 구체화 타입·숫자 범위 | 신뢰 선언 | 런타임 검사 | test context에서 검사 |
| lazy `Iterator`·`Generator` protocol과 lifecycle | 신뢰 선언 | 생성 시 protocol만 검사; lifecycle은 관찰된 evidence | test context에서 관찰된 lifecycle만 검사 |
| 지워진 `TypeVar` 관계 | 정적 검사 | 정적 검사 | 정적 검사 |

free-function wrapper order는 고정한다: statically concrete argument `F32` ABI normalization → 활성 mode의 concrete input type·numeric range·refinement, 모든 `requires`와 첫 applicable conditional `error` 기록 → sync implementation call 또는 async implementation coroutine의 direct `await` → return `F32` ABI normalization → 활성 mode의 concrete return type·numeric range, allowed `Err` set·기록된 conditional error obligation과 applicable guarded `ensures`. async wrapper는 await 완료 뒤 새 background task가 남지 않음을 runner에서 검증한다. impl init과 sync impl method wrapper의 state/contract order는 동일하며 async impl method는 존재하지 않는다.

facade의 always-on ABI pass는 expected type에서 statically concrete `F32` path만 recursive traversal한다. 값이 반올림되면 같은 immutable cott carrier를 다시 만들며 raw Python container를 convert하지 않는다. 이 path의 shape mismatch는 `off`에서도 ABI violation이고 erased `TypeVar` 내부는 static-only다. 이와 별도로 newtype 생성자는 6.2의 carrier ABI와 refinement를 항상 재귀 검사한다.

validator는 alias를 해소하고 cott_runtime nominal class, struct·enum field, container element와 newtype refinement를 재귀 검사한다. trait는 7장의 member-presence 수준, erased TypeVar는 static-only다. `Never` 값은 항상 실패하고 `Opaque`는 wrapper identity와 literal tag를 확인한다. `Iterator`와 `Generator`는 경계에서 lazy protocol/반환 object만 검사하고 소비·yield·`send`·completion·close를 미리 실행하거나 모든 element와 lifecycle effect를 runtime-validated라고 주장하지 않는다; 그 lifecycle은 실제 iteration 또는 test에서 관찰된 범위만 evidence가 된다.

`test-only` context는 cott 계약 테스트 실행기만 활성화하며 일반 환경 변수로 켤 수 없다. MVP는 구현 내부 호출 지점을 계측하지 않는다.

`runtime_validation` 값은 emit 시 facade·wrapper bytes에 compile-time specialize되어 managed file hash에 포함된다. 설치된 runtime은 `cott.toml`, `generation.json`이나 environment에서 mode를 다시 읽지 않는다. `test-only`의 optional check는 계약 test runner가 만든 test context에서만 활성화되고 일반 호출에서는 `off`와 같으며, 그 context는 public API나 환경 변수로 만들 수 없다.

#### 16.4.1 검증 보증 등급

Cott accepts a declaration when the capability required for that declaration is available. Declaration syntax/name/type validity is always checked; target projection, implementation selection, static verification, runtime verification, and test observation are separate capabilities. Missing runtime, sandbox, valid test input, external provenance linkage, or execution permission degrades only the relevant evidence to `미관찰` or `신뢰 선언`; it does not reject an otherwise valid declaration. Malformed syntax, unresolved names, invalid generic arity, impossible constants, invalid Opaque tags, and inadmissible hash keys remain hard errors.

`cott verify`는 모든 계약 항목을 같은 수준으로 검증했다고 표현하지 않는다.

| 등급 | 의미 | MVP 예시 |
| --- | --- | --- |
| 정적 증명 | 실행 없이 결정적으로 검사 | 공개 symbol, signature, concrete type 구조, 숫자 metadata, trait·generic 관계, impl method union coverage·helper name/path, 계약 표현식 타입 |
| 런타임 검사 | 실제 production mode의 실행 경계에서 검사 | 구체화된 중첩 값, `requires`, refinement, allowed error variant, `ensures`, init/invariant/modifies |
| 테스트 관찰 | deterministic하게 생성한 유효 사례에서 확인 | 순수 free function 또는 impl method의 conditional `error`와 `ensures` |
| 미관찰 | 유효한 사례를 만들지 못해 실행 증거 없음 | 만족 가능한 input·init case를 만들지 못한 절 |
| 신뢰 선언 | MVP가 일반적으로 증명할 수 없음 | 숨은 부작용, off mode 검사, effectful callable의 실행 조건, archive-to-install dependency provenance |

자동 test input은 모든 refinement와 `requires`를 만족해야 한다. generator는 IR hash와 callable FQN을 seed로 경계값 우선 64개 candidate를 만들고 container 길이 0–3, enum variant와 recursive `JsonValue` 깊이 4로 제한한다. Factory에는 source value literal이 없으므로 자동 contract test가 Factory candidate를 만들거나 Factory init을 호출하지 않는다. impl method는 method candidate 전마다 recorded `init_cases`를 source order로 instantiate한다: required state field에는 exact-name input candidate를 넣고 defaulted field는 deterministic하게 omitted 또는 explicit candidate로 둔다. init `requires`를 만족하지 않는 case는 버리고 모든 required state field를 채울 수 없으면 해당 method clause를 `미관찰`로 기록한다.

자동 계약 테스트는 resolved caller effect set이 비어 있고 반환 type이 `Never`가 아닌 sync/async free function과 impl method만 callable별 별도 CPython process의 deny-by-default OS sandbox에서 실행한다. classifier는 verified Cott call graph를 포함한 declared transitive effect set을 사용하며, 외부 code/import-time effect는 trust declaration으로 남고 sandbox를 완화하지 않는다. `Never` callable은 자동 호출하지 않고 clause별 `미관찰` reason을 기록한다.
선택 scope에 실행할 pure clause가 없으면 runner는 facade를 import하지 않고 IR strategy만으로 effectful clause를 `신뢰 선언`으로 기록한다. effectful impl method의 constructor dependency로만 포함된 pure initializer도 실행하지 않고 그 clause를 `미관찰`로 기록한다. 따라서 실행하지 않을 SDK module의 import-time device·memory side effect를 계약 테스트가 유발하지 않는다.


contract test runner는 free-function candidate를 staged facade symbol으로, impl-method candidate를 staged facade class의 compiler-owned init과 public method wrapper로 호출한 뒤 같은 typed IR evaluator로 init/method `requires`, 반환 type, conditional `error`, `ensures`, `modifies`와 invariant를 독립 판정한다. `test-only` project에서는 runner만 test context를 활성화하고, 다른 configured production mode도 바꾸지 않는다. 따라서 `off`도 실제 facade를 통과해 실행된 pure case의 테스트 관찰 evidence를 얻지만 설치된 facade의 optional production check가 활성화되었다고 보고하지 않는다. facade를 통과하지 않은 실행은 테스트 관찰로 기록하지 않는다.

verification report는 contract symbol과 source-order clause ID마다 `{symbol, clause_id, span, evidence: [{grade, mode, valid_cases, reason}]}`를 기록한다. runtime capability, static result와 실제 test 실행은 별도 evidence entry이고 단일 최고 등급으로 합치지 않는다. 0 case를 테스트 관찰로 승격하지 않는다.

`CottContractViolation`은 `Exception`의 하위 타입이며 `cott_runtime`에서 import한다. `symbol`, `phase`, clause `span`, expected·actual summary와 original `Exception` cause를 보존한다. verified loader의 identity·origin·hash preflight 실패도 target 호출 전에 `phase = "provenance"`인 이 exception으로 발생한다. facade의 동일한 exception boundary는 lazy load·symbol lookup과 implementation invocation 전체를 감싼다. loader가 이미 만든 `CottContractViolation`을 포함한 기존 contract violation은 재포장하지 않고, module compile·execute·import·symbol lookup의 `Exception`은 cause를 보존한 `phase = "implementation-load"` 위반으로, implementation이 새로 발생시킨 `Exception`은 invocation 위반으로 변환한다. `SystemExit`은 load 또는 invocation 중 반환 type이 `Never`이고 `process.exit`가 선언된 경우만 재전파하며 그 외에는 contract violation이다. 다른 `BaseException`은 포획하지 않는다. `Never` implementation이 정상 반환하면 위반이다. 어떤 exception도 cott `Result` error로 자동 변환하지 않는다.

진단과 JSON 검증 결과에는 구성된 mode에서 각 계약 항목이 실제로 얻은 보증 등급을 포함한다.

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

free-function implementation resolution priority는 optional manifest binding → 위 exact agent file → unresolved다. compatible agent file이 이미 있으면 재사용하고 agent를 호출하지 않는다. selected generate에서 agent file이 없거나 signature가 현재 contract와 불일치하면 regeneration candidate로 staged overwrite할 수 있다. binding 불일치는 항상 hard error며 agent로 대체하지 않는다. impl method resolution priority는 exact agent helper file → unresolved뿐이다; compatible helper가 없거나 name/signature가 다르면 regeneration candidate고 manifest binding은 언제나 hard configuration error다.

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

`target.python.source`는 compiler input과 durable implementation root일 뿐 runtime import path가 아니다. 이 root에는 cott public module, compiler-owned `*_types` 또는 `cott_runtime`을 정의할 수 없다. runtime·BasedPyright는 generated root 뒤에 standard library와 locked distribution만 사용하고 stub root는 runtime path에서 제외한다. Python build는 모든 local runtime file을 generated root에서만 포함한다. 설치된 wheel 전체의 독립 검증은 v1.0 범위지만 embedded provenance check는 MVP package에서도 필수다.

해석된 public free function과 every emitted impl class만 facade와 `__all__`에 포함한다. 미구현 free function 또는 impl method에는 placeholder를 만들지 않고 `current.unresolved`에 기록하며, unresolved method가 있는 impl class 자체도 emit하지 않는다. `cott verify`는 unresolved가 하나라도 있거나 verified facade projection이 전체 IR과 다르면 실패한다.

#### 16.6.1 유지 curriculum generation-first convention

유지되는 curriculum module의 source order는 type 선언, 작은 domain leaf function, 더 큰 composition function, domain-named final operation 순서다. 의미 있는 경계만 stage로 공개한다. grammar lesson은 의도적으로 leaf 하나일 수 있고 simple·complex lesson도 domain responsibility가 독립적인 경우에만 stage를 추가한다.

`.cott` declaration은 항상 bodyless다. free-function composition edge는 `from <exact cott module> import <declared public function>` 형태의 alias-free import로 exact generated public facade를 통과해야 하며 implementation file끼리 직접 호출하지 않는다. same-file private helper call은 implementation detail이고 impl canonical function의 only cross-contract method composition edge는 `self.<declared_method>(...)` public wrapper다. effect verifier는 caller와 same-file helper가 도달하는 Cott facade callee의 declared effects를 transitive하게 검사한다; external/stdlib operation은 declaration의 trust boundary로 남는다. helper가 Cott로 승격되어 public function이 되면 모든 ABI-valid input에 선언된 결과를 반환하거나 caller가 호출 전에 확립할 수 있는 Cott `requires`를 선언해야 한다.

`examples/grammar/checked-add`만 manifest binding syntax를 가르치는 lesson이다. 이 project만 `[target.python.implementations]` mapping과 `python/cott_bindings/<cott module>/<function>.py`의 authored source를 checkout에 둔다. 16.5의 manifest binding과 source/runtime provenance 규칙은 일반 product feature로 계속 지원하지만 다른 유지 example의 authoring model은 아니다.

나머지 41개 curriculum project와 `examples/complex/process-bar`에는 implementation mapping이나 authored `cott_bindings` function source가 없다. checkout에 유지하는 free-function `python/_cott_impl/<cott module>/<function>.py`, impl-method `python/_cott_impl/<cott module>/<Concrete>/<method>.py`와 `generated/` tree는 모두 실제 `cott generate --agent <agent> --target python` 성공 결과여야 하며 generation record의 matching `agent_runs` provenance를 보존한다. 이 generated source를 제거한 clean contract state에서 `cott emit python`은 agent를 호출하지 않고 unresolved metadata만 materialize하고, `cott generate`는 각 미구현 callable의 Cott contract와 allowed direct helper contract로 prompt를 만들어 callable별 durable source를 다시 생성한다. 생성 뒤 composition도 위 exact facade 경계를 통과하며 모든 public free function과 impl method가 생성되어야 `cott verify`가…

유지되는 curriculum은 generic `run` function, forwarding alias, direct implementation-to-implementation call, duplicated validation, nominal-wrapper-only helper를 금지한다.

---

## 17. 에이전트 코드 생성 흐름

### 17.1 생성 입력

선택된 에이전트에게 전달되는 정보는 다음과 같다. Unresolved function is eligible regardless of declared `Any`, `Unknown`, external type, `Iterator`, `Generator`, or recursively placed `Opaque`; agent code may implement the contract but cannot add a Cott body, weaken a declaration, or treat Python implementation code as contract source.

1. 생성 대상 callable의 Canonical IR과 원본 `doc`
2. 사전 조건·사후 조건·오류 조건·부작용
3. 생성 대상 언어 규칙과 프로젝트 코딩 규칙
4. 관련 타입 선언과 현재 implementation file
5. free function일 때 구현 바인딩과 바인딩된 심볼 목록 및 읽기 전용 프로젝트 내부 바인딩 파일
6. free function이 facade로 직접 참조하는 각 public helper function의 `doc`, signature, 관련 타입, 전체 contract와 effects
7. impl method일 때 concrete name, ordered state fields/defaults, init contract, invariants, method `modifies` clause, canonical helper name/path와 `self` public-method call rule
8. Canonical IR 밖에서 fully qualified Cott symbol 순으로 정렬한 deterministic Python external projection section


callable별 prompt는 대상 callable과 allowed direct helper contract surface, 그리고 별도 Python external projection section만 포함한다. impl method prompt에는 binding이 없고 compiler-owned class/init/wrapper source를 수정하지 말라는 조건을 포함한다. projection section은 manifest configuration에서 derive하며 Canonical IR이나 generation implementation schema에 섞이지 않는다. helper implementation이나 transitive helper contract closure는 포함하지 않으며, 각 helper는 자신의 별도 binding·generation·verification 단위와 prompt를 가진다. 이 depth-one prompt input이 monolithic implementation 대신 callable별 계약으로 생성 지시를 분리한다.

### 17.2 에이전트 선택 및 호출

`cott generate`는 미구현 callable을 생성할 때 사용자가 `--agent`로 지정한 에이전트를 사용한다. cott는 모델 제공자 API를 직접 호출하거나 에이전트를 자동 선택하지 않는다.

MVP는 다음 두 가지 에이전트와 각 에이전트가 제공하는 CLI 인터페이스만 지원한다.

| `--agent` 값 | 호출 인터페이스 |
| ------------- | --------------- |
| `codex`       | `codex exec`    |
| `omp`         | `omp -p`        |

cott는 17.1의 입력을 하나의 callable별 구현 지시로 구성하여 선택된 인터페이스에 전달한다. implementation kind가 free function이면 바인딩된 symbol을 다시 구현하지 말고 project-local call에는 exact cott facade function import만 사용하라고 명시한다. kind가 impl method이면 supplied exact canonical function을 작성하고 class·init·wrapper·state declaration을 작성하지 말며 project-local method coordination에는 `self.<declared_method>(...)`만 사용하라고 명시한다. 어느 경우든 prompt는 same-file private helper와 literal `Final` constant가 canonical function의 private implementation detail이며 public behavior가 되면 Cott로 승격해야 함을 명시한다.

지원하지 않는 `--agent` 값은 에이전트를 호출하기 전에 오류로 거부한다.

#### 17.2.1 에이전트 실행 계약

선택 범위의 미구현 callable마다 fully qualified symbol 정렬 순서로 agent process 하나를 실행한다. 각 process의 유일한 implementation write target은 해당 free-function file 또는 impl-method helper file이며 어떤 run이라도 실패하면 전체 generate transaction을 폐기한다. `agent_runs`에는 callable별 record를 source order가 아니라 이 실행 순서로 남긴다.

각 에이전트 adapter는 실행 파일, prompt 전달 방식, 작업 디렉터리, 환경 변수, 종료 상태를 명시한다.

compiler release마다 adapter별 minimum supported CLI version과 exact argv template를 고정한다. v0.3은 Codex CLI `>=0.147.0`, OMP `>=17.2.12`를 허용한다. executable은 `PATH`에서 한 번 resolve하고 version probe부터 아래 containment에서 실행한다. version output이 해석 불가능하거나 minimum version보다 낮으면 본 실행 전에 실패한다.

v0.3의 exact main-process argv template는 다음과 같다. 각 항목은 shell 재해석 없이 별도 argv다. `<workspace>`·`<scratch>/omp.yaml`·`<seconds>`와 `<prompt>`만 run별 값으로 치환한다.

* Codex: `codex exec --strict-config --ephemeral --ignore-user-config --ignore-rules --skip-git-repo-check --sandbox workspace-write --color never --cd <workspace> -`; prompt bytes는 stdin으로 전달한다.
* OMP: `omp -p --cwd <workspace> --no-session --no-rules --no-skills --no-extensions --no-lsp --no-pty --no-title --tools read,grep,glob,edit,write --approval-mode yolo --max-time <seconds>s --config <scratch>/omp.yaml <prompt>`; prompt는 마지막 단일 argv다.

공통 environment name은 `HOME`, `PATH`, `PYTHONDONTWRITEBYTECODE`, `TMPDIR`이며 host에 존재할 때만 `SSL_CERT_FILE`, `SSL_CERT_DIR`, `HTTPS_PROXY`, `HTTP_PROXY`, `NO_PROXY`를 추가한다. Codex는 존재하는 `CODEX_API_KEY`, `CODEX_ACCESS_TOKEN`, `CODEX_HOME`만, OMP는 존재하는 `PI_CODING_AGENT_DIR`만 추가한다. 그 밖의 host environment는 전달하지 않는다.

* shell을 사용하지 않고 executable과 각 인자를 분리하여 실행한다.
* 실행 전에 executable의 canonical regular-file path, version과 content hash를 기록한다.
* 작업 디렉터리는 17.4의 격리된 staging workspace다.
* 실제 project root는 agent sandbox namespace에서 보이지 않는다. 대상 계약, 직접 참조 helper 계약, 필요한 binding·rule·기존 구현과 compiler-owned facade는 staging의 read-only copy로만 제공하고 현재 implementation file과 별도 scratch directory만 쓸 수 있다. Codex credential path와 OMP native-addon cache만 project 밖에서 read-only로 열며, OMP의 `config.yml`과 `agent.db`는 매 실행 scratch로 복사하고 원본 credential directory는 열지 않는다. 이 sandbox를 강제할 수 없는 platform에서는 agent generate를 거부한다.
* prompt는 adapter가 지원하는 stdin 또는 단일 argv 값으로 전달하며 shell 문자열로 조합하지 않는다. 운영체제 인자 크기 한도를 넘으면 실행 전에 오류로 거부한다.
* 환경 변수는 compiler version에 고정된 adapter별 name allowlist만 전달한다. secret value는 기록하지 않고 전달한 name만 기록한다.
* `PYTHONDONTWRITEBYTECODE=1`을 설정하고 `TMPDIR`, type checker·test cache와 agent 임시 상태를 scratch directory로 보낸다.
* `[generator].timeout_seconds`는 1–3600이며 default는 900이다. 모든 agent child는 compiler-owned process containment에 넣는다. parent가 정상 종료해도 남은 descendant를 전부 종료·reap하고 containment가 비었음을 확인한 뒤에만 candidate path를 staging workspace handle 기준 `O_NOFOLLOW`로 열어 regular file·`st_nlink == 1`인지 `fstat`으로 확인하고 읽는다. 그 밖의 file kind, 사용자 취소·timeout·비정상 종료나 descendant 정리 실패는 transaction을 폐기한다.
* containment에는 compiler version이 고정한 process·CPU·memory·open-file·writable-byte ceiling을 적용하고 candidate implementation file은 최대 1 MiB로 제한한다. 어떤 ceiling이라도 넘으면 agent 실패다.
* stdout·stderr는 끝까지 drain하며 전체 byte count·SHA-256와 truncation 여부를 계산하고 사용자에게 stream별 최대 1 MiB만 보여 준다. generation record에는 raw output을 넣지 않고 이 metadata, exit code, 실행 시간, adapter·executable path·version·content hash·prompt hash만 남긴다.

에이전트가 0이 아닌 상태로 종료되거나 timeout되면 staging과 scratch 변경을 폐기한다. stdout의 code block은 구현으로 채택하지 않으며 허용된 implementation file의 최종 bytes만 후보 입력이다. compiler는 그 후보의 끝 LF를 정확히 하나로 정규화한 뒤 검증·hash·publication하며 그 밖의 bytes는 바꾸지 않는다. 0으로 종료해도 target callable이 없거나 file이 바뀌지 않아 unresolved면 실패한다.
agent가 file을 썼지만 candidate static validation에 실패하면 compiler는 기존 candidate bytes와 누적된 exact validation diagnostic을 같은 callable prompt에 넣어 최대 두 번 추가 실행한다. 각 retry 전 isolated target만 지우고 workspace·scratch containment, write allowlist와 전체 timeout을 새 agent run에 동일하게 적용한다. agent 실행 자체의 실패·timeout에는 retry하지 않으며 세 번째 candidate도 invalid이면 transaction 전체를 폐기한다. `agent_runs`에는 최종 검증 성공 run만 기록한다.


### 17.3 에이전트가 변경할 수 없는 요소

에이전트는 다음 요소를 임의로 변경할 수 없다.

* callable 이름·매개변수명·매개변수 타입·반환 타입·오류 타입·선언된 효과
* 공개 구조체 field와 enum variant
* impl concrete 이름, trait 목록, ordered state field·default, init contract, invariant와 `modifies`
* compiler-owned class shell, slot, lock, init, facade wrapper, provenance와 generated test

impl method agent는 exact private `_cott_impl_<Concrete>_<method>` canonical top-level function 하나를 작성해야 하며, 같은 file의 permitted private helper와 literal `Final` constant 외 public declaration·class·mutable module global을 작성할 수 없다. 계약 변경이 필요하면 `.cott` 파일을 수정하지 않고 변경 필요성을 결과로 보고해야 한다.

### 17.4 격리 실행과 원자적 반영

CLI argument parsing 뒤 compiler는 먼저 project root를 canonical directory handle로 고정한다. clean checkout에서 `.cott`이 없으면 root handle 기준 `mkdirat`으로 mode `0755` directory를 만들고 root를 fsync하며, 이미 있으면 no-follow directory인지 확인한다. `.cott/lock`은 그 handle 기준 `O_NOFOLLOW | O_CREAT`로 열어 regular file·`st_nlink == 1`을 확인한 뒤 exclusive OS advisory lock을 획득하며, 다른 project input은 lock 전 읽지 않는다. lock 안에서 `transactions` directory도 같은 방식으로 생성·검사한다. 모든 project command는 종료까지 lock을 유지하고 read-only command도 같은 coherent snapshot을 읽는다. lock metadata는 PID와 execution nonce를 기록하며 process 사망 시 OS가 lock을 해제한다.

content input·transaction destination의 각 path component는 project root handle 기준 no-follow로 연다. symlink, `st_nlink != 1`인 regular file과 project root 밖으로 벗어나는 path는 hash 계산 전 거부한다. manifest가 지정한 interpreter·type checker와 agent executable만 canonical regular-file path로 symlink를 한 번 해소하는 예외다.

`.cott`, 모든 transaction destination과 staging payload가 같은 filesystem이 아니거나 그 filesystem이 same-directory atomic rename, exclusive advisory lock, regular file·directory의 durable `fsync`를 제공하지 않으면 multi-file apply를 시작하지 않는다.

lock 획득 직후 다른 입력을 읽기 전에 `.cott/transactions/`를 검사한다. transaction directory는 0개 또는 1개만 허용하며 둘 이상이면 application payload 및 기존 journal/state를 변경하지 않고 exit `6`으로 실패한다. 단, lock 획득을 위한 `.cott/lock` state 초기화는 예외다. journal의 `schema_version`이 현재 compiler와 정확히 다르거나 journal·pre-image가 unreadable·checksum-invalid이면 추측하거나 삭제하지 않고 exit `6`으로 실패한다.

1. transaction은 `schema_version`, nonce, 모든 destination의 file kind·mode·content pre-image, sibling temporary post-image, operation 목록·hash와 전체 journal checksum을 `.cott/transactions/<nonce>/`의 immutable journal에 저장한다.
2. backup file과 immutable journal을 fsync하고 transaction directory와 parent를 fsync한다. 상태는 journal과 분리한 marker이며 각 전이는 새 state와 journal checksum을 sibling temp에 쓰고 file fsync → same-directory atomic rename → transaction directory fsync 순서로 publish한다.
3. immutable journal과 pre-image 검증이 끝나면 `prepared`, 첫 project mutation 직전에 `applying` marker를 차례로 publish한다.
4. 각 regular-file post-image는 destination parent의 no-follow sibling temp에 final mode·bytes로 쓰고 file을 fsync한 뒤 hash를 재확인한다. `generation.json` 외 payload는 sibling rename 또는 삭제로 반영하고 매 operation 뒤 destination parent를 fsync한다.
5. `generation.json`을 포함하는 command는 같은 방식으로 만든 그 sibling temp를 모든 다른 payload 뒤 마지막으로 rename하고 parent를 fsync한다.
6. 적용 대상의 file·directory durability가 모두 확인된 뒤에만 `committed` marker를 publish한다.
7. `prepared`·`applying`, absent·unknown·checksum-invalid state marker는 immutable journal과 pre-image가 검증되는 경우 보수적으로 rollback하고, valid `committed` marker만 cleanup한다.

rollback은 idempotent해야 하며 recovery 자체가 중단되면 같은 journal로 다시 시작한다. 복구 결과의 file·directory fsync가 끝난 뒤에만 journal을 삭제하고 transaction parent를 fsync한다.

compiler payload의 regular file mode는 `0644`, directory mode는 `0755`로 고정하고 process umask와 무관하게 설정한다.

transaction 시작 시 계약, manifest, manifest가 참조하는 rule, lockfile, `<target.python.source>`, generated tree와 compiler-owned test tree의 파일 목록·content hash를 기록한다. 프로젝트 내부 binding과 기존 implementation도 포함한다. 그 뒤 임시 staging workspace와 별도 scratch directory를 만든다.

staging에는 대상 계약, allowed direct helper 계약, binding, rule, 기존 구현과 compiler 생성물의 사본을 제공하고 실제 project path는 agent에게 노출하지 않는다. 각 agent process의 workspace write allowlist는 현재 callable file 하나로 제한한다.

```text
<target.python.source>/_cott_impl/<module path>/<function>.py
<target.python.source>/_cott_impl/<module path>/<Concrete>/<method>.py
```

각 agent file에는 canonical function 하나와 same-file private helper 0개 이상, same private-name rule의 permitted literal `Final` immutable constant만 둘 수 있다. helper는 single-leading-underscore private name을 쓰고 facade·manifest binding·provenance symbol이 아니며 public behavior가 되면 별도 Cott declaration과 implementation file로 승격한다. 공개 cott helper의 implementation file, 필요한 `_cott_impl/**/__init__.py`, facade, type module, stub, IR, docs, generated tests와 provenance는 현재 agent가 쓸 수 없다. free-function binding file을 agent 생성 대상으로 함께 쓰거나 impl method binding을 선언하는 구성은 거부한다.

scratch는 workspace diff 대상이 아니며 실행 뒤 폐기한다. agent 실행 후 staging 전체 file list와 diff를 검사한다. `.cott`, manifest, binding, compiler 생성물, 비선택 구현 또는 allowlist 밖 변경은 실패다. agent가 workspace에 만든 cache·temporary file도 위반이다.

compiler-owned 관리 집합은 `<target.python.generated>`, `<target.python.stubs>`, `<artifact-root>/ir`, `<artifact-root>/docs`, `tests/generated`와 compiler-owned `<target.python.source>/_cott_impl/**/__init__.py`의 합집합이며, generation record는 `<artifact-root>/generation.json`이다. stale 삭제는 현재 command의 ownership 안에서만 수행한다. `emit ir`은 `<artifact-root>/ir`만, `emit python`과 `generate`는 전체 관리 집합을 소유하며 verify는 전체 집합을 재생성해 비교하되 반영하지 않는다.

성공적으로 project source에 승격된 agent callable file은 비결정적이지만 durable implementation source로 취급하며 cott가 자동 삭제하지 않는다. IR에서 더 이상 참조하지 않는 file은 `cott diff`의 `IMPLEMENTATION STALE`로 보고하되 public facade나 verify 대상에는 포함하지 않는다. 사용자가 명시적으로 삭제한다.

각 command의 staging 검사가 성공한 뒤 시작 project file list·hash와 해석된 tool executable·direct external dependency origin·distribution metadata의 identity·content hash를 다시 비교하고 달라졌으면 덮어쓰지 않는다. `emit ir`의 반영 대상은 IR scope와 `generation.json`, `emit python`·`generate`는 command 범위의 durable implementation, 전체 compiler 관리 집합·stale 삭제와 `generation.json`이다. `cott fmt`는 모든 선택 source의 formatted bytes를 먼저 staging하고 같은 journal로 한꺼번에 반영하며, 기존 `generation.json`이 있으면 실제 input·managed state를 다시 기록해 `current.verified = false`로 만들고 `last_verified`를 보존한 record를 마지막에 반영한다. record가 없으면 fmt가 새로 만들지 않는다. verify는 managed artifact를 반영하지 않고 성공 record만 같은 journal로 반영한다.

OS advisory lock은 cott process끼리만 조정한다. 이를 따르지 않는 editor·package installer 등 외부 writer는 command 실행 중 같은 project destination이나 해석된 dependency를 변경해서는 안 된다. 마지막 hash 재확인은 apply 전 drift를 탐지하고 배포 gate는 apply 뒤에도 hash를 다시 계산하지만, concurrent non-cott writer의 수정 보존이나 실행 중 Python reader의 snapshot isolation은 보장하지 않는다. 배포는 성공한 transaction 뒤 새 Python process로 시작해야 한다.

실패, timeout, 취소 또는 검증 오류에서는 이전 세대를 유지한다. 프로젝트 밖 dependency는 sandbox에서 읽기 전용으로 제공한다.

### 17.5 생성 결과 검증

아래 full pipeline은 `emit python`, `generate`와 full `verify`에 적용한다. `emit ir`은 Canonical IR 생성 뒤 final input 재확인과 17.4의 IR-scope apply로 이동하며 Python target을 만들지 않는다.

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

### 18.1 프로젝트 초기화

```bash
cott init <path>
cott init <path> --name <project-name> --no-sync
cott init <path> --format json
```

`<path>`는 필수며 absolute·relative path를 모두 허용한다. 기존 directory인 parent를 canonicalize한 뒤 그 안의 final component 하나를 target으로 사용한다. final component는 비어 있거나 `.`·`..`일 수 없고, target이 symlink를 포함해 이미 존재하면 내용과 무관하게 exit `2`다. 따라서 symlink가 포함된 parent path는 canonical parent로 정규화하되 새 target 자체의 symlink·alias collision은 허용하지 않는다. 기본 project name은 target basename을 변환하지 않고 그대로 사용하며, 이 값이 유효하지 않으면 `--name`이 필요하다. name은 `^[a-z](?:[a-z0-9]|-[a-z0-9])*$`를 만족하는 1–64자여야 하므로 trailing·consecutive hyphen을 거부하고 Python distribution name과 module name을 동시에 만족한다. `-`를 `_`로 바꾼 top-level module도 기존 reserved/collision 검사를 통과해야 한다. interactive prompt, `--force`, overwrite, dry-run은 없다.

`init`은 아직 project가 없어서 17.4의 project lock/journal을 쓰지 않는 유일한 명령이다. canonical parent directory handle 아래에 mode `0700` private sibling temporary scaffold를 만들고 target root의 mode `0600` `.cott-init` file에 closed `schema_version`·nonce ownership record를 저장한다. 모든 file을 fsync한 뒤 directory를 bottom-up fsync하고, Linux `renameat2(RENAME_NOREPLACE)` 또는 macOS `renameatx_np(RENAME_EXCL)`에 해당하는 같은-parent atomic no-replace rename으로만 publish한 다음 parent를 fsync한다. publish 전 실패는 init-owned temp를 no-follow로 제거하고 parent를 fsync한다. 경합 `EEXIST`는 이 cleanup까지 성공한 경우에만 exit `2`이며, 다른 scaffold·rename·fsync 실패나 cleanup 실패는 exit `6`이다. publish 뒤에는 uv 실행과 모든 probe를 먼저 완료한다. `.cott-init` unlink가 final commit transition이며, unlink 전 실패는 root file identity와 in-memory nonce가 marker record와 모두 일치하는 init-owned target만 no-follow로 제거하고 parent를 fsync한 뒤 원래 exit code를 반환한다. identity가 달라졌거나 cleanup이 실패하면 target을 보존하고 exit `6`을 반환한다. unlink를 시작한 뒤에는 target을 자동 삭제하지 않는다. unlink 또는 이어지는 target-root fsync가 실패하면 exact completed tree나 ownership-marked completed tree를 보존하고 exit `6`과 수동 확인 경로를 진단하며, 둘 다 성공해야 init이 성공한다. process crash로 남은 ownership-marked temp·target도 다음 init이 자동 삭제하거나 overwrite하지 않고 exit `2`와 수동 확인 경로를 진단한다. uv가 한 번이라도 시작된 뒤 실패하면 선택된 human 또는 JSON diagnostic에 global managed-Python·cache 변경이 남고 rollback되지 않을 수 있음을 반드시 포함한다.

scaffold는 `python/.python-version`에 `3.14`를 쓰고 `python/pyproject.toml`의 `requires-python`을 `>=3.14.6,<3.15`로 고정하며 BasedPyright `>=1.39.9`를 dev dependency로 둔다. v0.3은 CPython `>=3.14.6,<3.15`와 uv `0.12.3` 이상을 지원하며, init은 그 범위의 managed CPython patch를 설치·probe한다. `uv.lock`은 Python exact patch를 고정하지 않으며, 실제 설치된 full patch는 이후 generation provenance에 고정한다.

uv executable은 shell 없이 PATH에서 한 번만 canonical regular file로 resolve하고 version이 `0.12.3` 이상인지 검사한다. uv subprocess environment는 empty base에서 compiler-fixed sanitized `PATH`와 허용한 `HOME`·temporary-directory·platform TLS/certificate 변수만 복사하고 inherited `UV_*`, `VIRTUAL_ENV`, `CONDA_PREFIX`는 전부 제외한 뒤 `UV_PYTHON`·`UV_PROJECT_ENVIRONMENT`만 해당 단계에 명시하며 canonical uv를 `--no-config`로 실행한다. `<uv> --no-config python dir`의 canonical managed-install root를 기록한 뒤 다음 순서로 실행한다: `<uv> --no-config python install --upgrade 3.14`; `<uv> --no-config python find --managed-python --system 3.14`가 반환한 canonical path가 그 root 아래인지 확인하고 해당 interpreter를 `-I -c <compiler-fixed-identity-probe>`로 실행해 CPython `>=3.14.6,<3.15`를 검증; project cwd `python/`에서 lock, sync 순서를 수행한다.

`--no-sync`는 Python install·upgrade, lock 및 uv-managed Python probe까지 수행하고 sync와 root venv Python·BasedPyright probe만 생략한다. human 출력은 `/usr/bin/env -i HOME=<home> TMPDIR=<temporary-directory> PATH=<sanitized-path> UV_PYTHON=<canonical-managed-interpreter> UV_PROJECT_ENVIRONMENT=<canonical-target-absolute>/.venv <canonical-uv> --no-config sync --directory <canonical-target-absolute>/python --frozen --managed-python`의 placeholder를 init과 같은 compiler-owned environment allowlist의 실제 값 및 canonical path로 POSIX-shell-escape해 렌더링한다. JSON 출력은 같은 명령을 `severity: "note"`, `span: null` diagnostic의 `help` 원소로 제공한다.

모든 subprocess는 shell 없이 실행하고 stdout/stderr를 drain하되 output은 bounded하게 보관하며 compiler-fixed timeout과 cancel을 적용한다. uv missing/unsupported와 invalid args/path/name은 exit `2`; init의 uv dir·install/upgrade·find·lock·sync, managed/root venv interpreter·BasedPyright probe 실패, timeout 또는 cancel은 exit `5`다.

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

이 명령은 `<artifact-root>/ir` scope와 `<artifact-root>/generation.json`만 원자 갱신하고 다른 compiler-owned managed bytes는 그대로 둔다. `current`는 apply 뒤 실제 전체 managed file hash와 `current.verified = false`를 기록하며 `last_verified`를 보존한다.

### 18.5 Python 대상 생성

```bash
cott emit python
```

이 명령은 agent 없이 compiler-owned 산출물을 staging에서 만들고 원자 갱신한다. 미구현 free function과 impl method는 facade에서 생략하고 kind·canonical symbol을 `current.unresolved`에 기록한다. `current.verified = false`로 갱신하지만 `last_verified`와 durable agent implementation file은 보존한다. emitter 자체가 성공하면 exit 0이지만 배포 가능한 결과는 아니다.

### 18.6 구현 생성

```bash
cott generate --agent codex --target python
cott generate foo.bar.process_bar --agent omp --target python
cott generate foo.bar.Counter.increment --agent codex --target python
```

selection은 exact canonical free-function FQN 또는 impl-method FQN `<module>.<Concrete>.<method>`만 받으며 class FQN alone, trait FQN, glob과 alias는 거부한다. 선택 범위에 미구현 callable이 있으면 `--agent`가 필수다. 허용 값은 `codex`, `omp`다. 선택된 free function이 모두 binding되어 있으면 agent를 호출하지 않지만 impl method는 binding될 수 없어 unresolved이면 항상 agent candidate다. 특정 callable generate에서 agent write 대상은 그 callable의 durable source file뿐이며 apply는 선택 implementation과 전체 compiler-owned 관리 집합을 함께 갱신한다. verified baseline guard는 17.5의 정확한 규칙을 사용한다. 최초 검증 전에는 선택 범위 성공만으로 진행할 수 있다. 결과는 `current.verified = false`며 project 전체 미구현 상태를 별도 진단한다. 배포 gate는 항상 full `cott verify`다.

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
* deterministic init-case construction을 포함한 순수 free function/impl method 계약 테스트, init/invariant/modifies clause별 evidence와 미관찰 사례의 정확한 등급 강하
* unresolved callable과 compiler-owned stale module·symbol, stale durable implementation 진단
* generated copy의 verified-loader runtime signature, facade/type/source/runtime origin·content hash와 copy byte identity
* direct cott facade import의 exact module·public free-function identity와 금지된 module·alias·type·constant·star·`_cott_impl` import
* 모든 external import의 selected lock entry, installed distribution identity·version·metadata·origin·content hash와 archive-to-install 신뢰 등급
* configured mode의 public callable `requires`, concrete 반환 타입, allowed error variant와 `ensures`, always-on impl init/state checks
* recursive-placement `Opaque` tag/key admissibility와 reserved target path, staging allowlist, filesystem·effect sandbox와 transaction recovery, current/last_verified provenance

`cott verify`는 result cache를 사용하지 않고 현재 contract·manifest·lock·implementation input에서 expected IR·Python·stub·docs·test artifact를 staging에 다시 만든 뒤 실제 managed file 집합과 byte-for-byte 비교한다. input drift는 새 검증 대상으로 허용하지만 missing·extra·hand-edited managed file은 hard failure이며 `cott emit` 또는 `cott generate`로 먼저 갱신해야 한다. verify는 source와 managed file을 고치지 않고, 시작 snapshot이 실행 중 달라져도 실패한다. 모두 성공한 뒤 `generation.json`만 journal transaction으로 갱신해 같은 snapshot을 `current.verified = true`와 `last_verified`에 기록한다.

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

public declaration 제거·rename, sync/async kind, signature·generic·type shape·variant·field·default·constant·refinement·contract clause·effect의 변경은 conservative하게 breaking이다. 새 top-level type·function·constant만 기존 target symbol과 충돌하지 않을 때 additive다. doc만 바뀌면 `DOCUMENTATION`이다. diff는 semantic implication을 추측하지 않는다.

baseline/current `[project].version`은 restricted `x.y.z` API version이며 current가 baseline보다 작으면 diff error다. breaking change는 baseline major가 `0`이면 최소 minor, 그 밖에는 최소 major bump를 요구한다. additive change는 최소 minor bump를 요구하고 implementation/documentation-only change는 bump를 요구하지 않는다. insufficient bump는 `VERSION INCOMPATIBLE` change로 report에 추가되고 `--exit-code`는 7을 반환한다. report는 declaration removal에 “Remove uses …”, addition에 “Adopt …” migration advice를 함께 제공한다.

`cott diff`는 `generation_id` mismatch 자체를 change로 보지 않는다. 같은 target environment에서는 compiler·runtime·Python·type-checker identity와 managed artifact hash까지 비교한다. target identity가 다른 cross-machine 비교에서는 이 machine-local 항목을 변경 판정에서 제외하고 normalized contract·public symbol, durable implementation content와 normalized lock·dependency identity를 비교한다.

MVP는 generation result cache를 두지 않고 emit·generate 때마다 target을 결정적으로 다시 만든다. `generation_id`를 구성하는 contract·manifest·rule·target metadata·lock raw hash, compiler·runtime·Python·type-checker identity, implementation identity·source/runtime origin·content hash 중 하나라도 달라지면 새 세대다. `cott verify`도 항상 모든 검사를 실행한다.

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
| `2` | CLI 사용법, init의 uv missing/unsupported·invalid args/path/name, manifest 구성 또는 diff baseline 부재·읽기·schema 오류 |
| `3` | cott 문법, 이름, 타입 또는 계약 오류 |
| `4` | 구현 누락·불일치, provenance drift 또는 verify 실패 |
| `5` | agent 또는 init uv 실행·probe 실패, timeout 또는 취소 |
| `6` | init filesystem·cleanup·atomic no-replace rename, lock, 동시 수정, sandbox 또는 원자적 반영 실패 |
| `7` | `cott diff --exit-code`에서 breaking contract 발견 |
| `8` | `cott fmt --check` format mismatch |

`cott diff`는 기본적으로 차이를 출력하고 0을 반환하며 `--exit-code`에서만 breaking change를 7로 반환한다. `cott emit`의 미구현 진단과 `verified = false`는 emitter 자체가 성공했다면 0이지만 배포 성공을 뜻하지 않는다.

여러 문제가 동시에 있으면 argument·subcommand 및 init의 missing/unsupported uv·invalid args/path/name 오류 `2` → init filesystem·cleanup·atomic no-replace rename과 lock·journal recovery `6` → cleanup이 성공한 init target collision `2` → manifest 구성 `2` → diff baseline resolution `2` → cott semantic `3` → implementation·provenance `4` → agent 또는 init uv 실행·probe `5` → formatter 비멱등성 등 internal compiler error `1` → apply `6` → command-specific diff·format 상태 `7`·`8` 순서에서 처음 검출된 실패 하나를 반환한다. code를 합치거나 더 늦은 오류로 덮어쓰지 않는다.

---

## 19. 프로젝트 구조

### 19.1 `cott init` 직후 구조

`cott init <path> [--name <name>] [--no-sync]`는 존재하지 않는 새 target에 다음 최소 scaffold를 만든다. `<module>`은 project name에서 derive한 Python-safe module name이다.

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

`.cott/lock`, `.cott/transactions`와 `<artifact-root>/generation.json`은 machine-local state며 source control과 배포 package에 포함하지 않는다. release baseline으로 보관한 generation record는 `cott diff --baseline`에 명시할 수 있다.

manifest 예시:

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

[target.python.external_types]
"foo.data.HttpRequest" = "starlette.requests:Request"

[target.python.implementations]
"foo.data.load_payload" = "my_project.adapters.provider:load_payload"

[generator]
rules = "AGENTS.md"
timeout_seconds = 900
```

MVP manifest schema는 닫혀 있고 Python target 하나만 허용한다. `[effects]`, `[target.python.implementations]`, `[target.python.external_types]`의 동적 key 외 unknown table·field는 configuration error다. `[target.python.external_types]` key는 quoted fully qualified Cott external symbol이고 value는 `module:Qualname`이다; key는 선언된 external type에 정확히 하나씩 대응해야 하며 non-external·missing·stale key, malformed module/qualname과 prompt에 안전하지 않은 value는 configuration error다. 이 projection table은 target configuration일 뿐 Canonical IR이나 implementation selection에 들어가지 않는다.

`[project]`의 `name`·`version`·`source`와 `[target.python]`의 `source`·`generated`·`stubs`·`interpreter`·`type_checker`·`runtime_validation`은 필수다. `lockfile`은 아래 dependency 규칙의 조건부 필드이고 `[effects]`, `[target.python.implementations]`, `[target.python.external_types]`, `[generator]`는 선택이다. `[generator]`가 없으면 `timeout_seconds = 900`이고 project coding rule은 없으며, 있으면 `rules`는 선택적인 project-relative regular file이고 `timeout_seconds`는 선택적인 1–3600 정수다.

모든 manifest path는 project-relative normalized path여야 하며 absolute path와 `..`를 거부한다. content file·directory는 symlink일 수 없다. `[project].source`, `[target.python].source`, artifact root, `tests/generated`, `.cott` directory root는 서로 disjoint하며 중첩할 수 없다. artifact root는 필수 `[target.python].generated`의 parent directory로 derive하고 `generated`의 basename은 반드시 `python`이어야 한다. `[target.python].stubs`는 `<artifact-root>/stubs`여야 하며 IR·docs·record는 각각 `<artifact-root>/ir`, `<artifact-root>/docs`, `<artifact-root>/generation.json`으로 derive한다. executable path만 symlink를 해소해 canonical regular file로 실행한다.

`core.*`는 source tree가 아니라 compiler prelude다. `source`는 `_cott_impl`과 user adapter를 포함하는 durable implementation root이고 `generated`는 public cott module, `cott_runtime`과 verified local implementation copy를 포함하는 단일 runtime·package root다. source에는 cott 공개 path, `*_types` 또는 `cott_runtime`과 충돌하는 module을 둘 수 없다.

runtime과 BasedPyright search path는 generated root 뒤에 standard library와 locked distribution만 둔다. source root와 tool-only stubs는 runtime path에서 제외한다. Python build도 generated root의 runtime file만 포함한다.

interpreter와 type checker path는 project root 기준이며 regular executable로 resolve되어야 한다. target project metadata는 `<target.python.source>/pyproject.toml`로 고정하고 `requires-python`이 CPython 3.14와 호환되어야 한다.

`cott init`만 uv에 해당 supported uv release가 제공하는 최신 CPython 3.14 patch의 managed install·upgrade, `uv.lock` 생성, default dev group을 포함한 frozen sync를 위임한다. `uv.lock`은 Python exact patch를 고정하지 않으며, 실제 full patch는 이후 generation provenance에 고정한다. `--no-sync`는 sync와 그 결과에 의존하는 root venv Python·BasedPyright probe만 건너뛰며 Python install·upgrade, managed Python probe와 lock 생성은 수행한다. `cott init`의 명시적인 uv 위임을 제외한 compiler/verify command는 dependency를 설치하거나 다시 해석하지 않고 기존 lockfile·provenance 규칙을 따른다. init이 만든 lockfile은 production dependency가 비어 있어도 존재한다; manually authored project에서는 external dependency가 전혀 없을 때만 생략할 수 있다.

binding 또는 agent implementation이 standard library·generated module 밖의 distribution을 하나라도 import하면 lockfile이 필수다. 존재하는 lockfile은 항상 provenance와 `generation_id`에 포함한다. `generation.json`은 `current`와 `last_verified`, implementation owner·source/runtime origin·content hash와 compiler 관리 집합을 기록한다.

MVP가 해석하는 lock format은 supported schema version의 `uv.lock`뿐이다. `pyproject.toml`의 production dependency 선언과 lock의 root metadata가 frozen 상태로 일치해야 하며, 구현이 import하는 모든 distribution은 현재 platform에서 선택된 production dependency closure에 속해야 한다. external distribution은 installed metadata의 name·version·inventory가 그 selected non-editable registry dependency와 일치해야 한다. editable·path·VCS·unhashed source는 거부하고 selected lock hash는 기대 `lock_artifact_hash`, installed metadata·module bytes는 별도 관찰 hash로 기록한다. immutable archive나 검증 가능한 installer receipt가 없으면 둘의 provenance 연결은 신뢰 선언이며, `cott init`의 명시적인 uv 위임을 제외한 compiler/verify command는 dependency를 설치하거나 다시 해석하지 않는다.

agent implementation은 source file로 지속되고 compiler stale file만 자동 정리한다. 변경 command와 같은 project를 사용하는 Python process는 동시에 실행하지 않는다.

---

## 20. 진단 메시지

오류 메시지는 단순히 파싱 실패를 알리는 수준에 머물지 않는다.

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

---

## 21. 포맷터 규칙

cott는 idempotent한 공식 format 하나만 제공한다.

* UTF-8, LF newline, file 끝 newline 하나
* indentation 4 spaces, tab·trailing whitespace 금지
* token 사이 spacing과 operator 양쪽 한 space
* module 뒤 빈 줄 하나; contiguous `use` declaration 사이는 붙이고 그 block 뒤와 top-level declaration 사이는 빈 줄 하나; field·variant·같은 clause group은 빈 줄 없이 한 logical line에 하나, non-empty clause group 사이는 빈 줄 하나
* parameter·import-name·type-argument·payload·effects comma-list는 rendered line의 Unicode-scalar column 수가 100 이하이면 한 줄로 유지하고, 넘으면 결정적으로 item별 line로 나누며, 이 multiline list에는 grammar가 허용하는 경우에만 trailing comma를 붙임
* single-line list의 trailing comma와 grammar가 허용하지 않는 trailing comma는 제거
* contract expression은 Unicode-scalar column 수가 100 이하이면 한 줄로 유지하고, 넘으면 괄호를 추가한 뒤 낮은 precedence operator부터 결정적으로 나눔
* `doc`, `requires`, `ensures`, `error`, `effects` group order와 각 group 내부 source order 보존
* comment의 다음 syntax node attachment, literal spelling과 `doc` content 보존

legal breakpoint가 없는 string·qualified name은 Unicode-scalar column 수가 100을 넘을 수 있다. parse error가 있으면 file을 쓰지 않는다. `cott fmt --check`는 formatter output과 raw input bytes를 비교하고, 두 번 format한 결과가 한 번 결과와 다르면 compiler bug로 실패한다.

---

## 22. MVP 범위

### 22.1 v0.3에 포함

* v0.3 grammar, const generic, heterogeneous variadic `Tuple`, `Array`, `Buffer`와 aggregate constant
* immutable type/enum/resource, structural trait, associated type projection/assignment과 static default-facade dispatch
* explicit sync/async free function, async binding/provenance/facade/runner; async return exclusion
* unified match guard, rule composition, ordered error, resource transition, transitive Cott effect check
* Canonical IR v5, generation schema v2, runtime ABI2와 project API version identity
* Python facade/stub/runtime, static ABI check, boundary evidence, verified loader, deterministic contract test
* `current`/`last_verified` provenance and project-version-aware contract/implementation diff with migration advice

### 22.2 v0.3에서 제외

* `.cott` execution body, parameter default, generic overload
* trait inheritance, specialization, subtyping variance와 dynamic trait dispatch
* async impl method, async iterator, async generator 및 their cancellation/lifecycle semantics
* ownership, borrow checker, lifetime, arbitrary recursive user type, SMT proof
* Cott 밖 Python call graph/effect inference, project-local implementation direct import
* mutable Cott container state, arbitrary `old()`, automatic refactoring/adapter/exception conversion
* multi-target backend, full IDE plugin, multi-project Python environment, external struct/enum direct binding
* dependency resolver/package manager, live reader transaction snapshot isolation, installed wheel whole-origin verification

---

## 23. MVP 완료 기준

MVP는 다음 조건을 모두 자동 검증할 때 완료다.

1. 14장 예시를 clean checkout에서 parse, emit, generate, verify할 수 있다.
2. module path가 injective하고 reserved prelude·target path 충돌이 emit 전에 실패한다.
3. syntax, name, type와 contract 오류가 정확한 source span을 가진다.
4. 모든 declaration·type·contract clause와 pattern이 normative schema를 통과하는 typed IR node며 ambient name과 불법 expression을 거부한다.
5. conditional `error` priority와 error list의 allowed variant exhaustiveness를 source order에서 결정적으로 보존한다.
6. public constant와 impl class를 포함한 public symbol이 IR, type module, facade, stub과 diff에 동일하게 나타난다.
7. facade와 stub을 각각 `public_python_symbols(IR)`과 비교하고 declared `Any`·`Unknown`을 각각 `typing.Any`·`object`로 보존하며 누락 annotation과 혼동하지 않는 compiler-owned BasedPyright strict 검사를 통과한다.
8. project identity가 일치하는 `cott_runtime` 하나만 표준 union, container, numeric metadata와 contract exception identity를 소유한다.
9. statically concrete `F32` binary32 normalization을 모든 mode에서, integer range를 검사가 활성화된 ABI boundary에서 보존한다.
10. `Path`, `Unit`, `Never`, `Any`, `Unknown`, `Iterator`, `Generator`, `JsonValue`, `Opaque`, external type, struct, enum, newtype, heterogeneous tuple, Array와 Buffer ABI를 보존한다.
11. type/const generic invariance, associated projection/assignment, trait default facade selection과 복수 structural trait bound를 static verifier와 BasedPyright에서 유지한다.
12. newtype constructor는 모든 mode에서 carrier ABI와 refinement를 재귀 검사하고 raw Python container를 받지 않는다.
13. boundary mode는 public callable concrete nested value, `requires`, allowed error variant와 `ensures`를 검사한다.
14. compiler-owned impl init은 exact state assignment·init clauses·post-init invariant를, method wrapper는 identity state snapshot·`modifies`·normal `Ok`/`Err` invariant를 모든 mode에서 검사하고 per-instance `RLock`으로 serialize한다.
15. off·test-only mode는 16.4 표보다 강한 보증을 보고하지 않는다.
16. 자동 test input은 refinement·`requires`를 만족하며, impl method는 deterministic init case로 instantiate하고 생성 실패 clause를 `미관찰`로 보고한다.
17. pure free-function/impl-method test는 deny-by-default OS sandbox에서 facade wrapper를 통해서만 실행하고 effectful callable과 `Never` 반환 callable은 자동 실행하지 않는다.
18. free-function binding과 implementation import를 이번 staged type module·Canonical IR에 대해 import 없이 해석하고, project-local module access는 compiler-generated package/facade namespace로 제한하며 cross-contract call은 declared public function 또는 `self` method wrapper만 허용해 각 callable을 별도로 생성·검증한다.
19. impl class는 ordinary final slot shell이며 inheritance·subclassing·dynamic attribute·`__del__` 없이 trait method union을 exact coverage하고 every impl method가 canonical agent-only function/path 및 same-file private helper/`Final` policy로 해석됨을 검증한다.
20. 모든 implementation external import는 frozen production dependency closure의 selected lock hash, installed distribution identity·version·metadata·origin·content hash 없이는 실패하며 archive-to-install 연결의 신뢰 등급을 정직하게 보고한다.
21. local implementation은 generated runtime copy로 고정하고 verified loader가 그 exact bytes를 실행 전 검증한다.
22. implementation signature, numeric metadata, source/runtime origin, copy byte identity와 content drift를 탐지하고 impl provenance/unresolved record를 canonical callable symbol과 kind로 남긴다.
23. agent는 user-selected supported CLI만 shell 없이 callable별 process와 single-file write sandbox에서 실행하며 impl method manifest binding을 거부한다.
24. 선택 callable file 외 project·contract·manifest·binding·non-selected implementation 변경을 막는다.
25. 최초 partial generate와 verified-baseline partial generate 규칙을 구분하고 baseline declaration의 비선택 surface를 보존하되 새 declaration 추가를 허용하며 항상 `current.verified = false`로 남긴다.
26. unresolved free function 또는 impl method, incomplete public projection이 full verify를 실패시킨다.
27. successful full verify만 동일한 current snapshot을 `last_verified`로 승격한다.
28. `cott diff` 기본 baseline은 `last_verified`이며 contract, implementation과 stale implementation을 구분한다.
29. semantic·implementation input drift가 `generation_id`를 바꾸고 target을 다시 emit하며 verify는 전부 재실행된다.
30. stale compiler output은 삭제하지만 durable agent source는 자동 삭제하지 않는다.
31. crash injection을 journal state publish와 각 post-image fsync·rename·delete·commit, rollback restore·fsync·journal cleanup의 재중단 단계에 수행해 반복된 다음 lock acquisition마다 old 또는 new complete snapshot으로 복구한다.
32. CLI는 format mismatch를 포함해 18.9의 stable exit code를 반환한다.
33. 배포 gate는 full `cott verify`와 transaction 뒤 시작된 새 Python process만 허용한다.
34. formatter는 21장의 canonical format, parse-error no-write, 두 번 format의 byte-identical idempotence와 raw-byte `--check`를 검증한다.
35. JSON diagnostic은 20장의 closed schema, 안정 정렬, 단일 object·끝 newline과 human prose·색상 없는 출력을 검증한다.
36. `cott init`은 absent target만 허용하고 exact scaffold·template, supported uv release가 제공하는 최신 CPython 3.14 patch managed install·upgrade, lock과 기본 sync, `--no-sync`의 sync 및 root venv Python·BasedPyright probe 생략, atomic collision no-write, publish 전과 final marker commit 전 실패의 ownership-checked cleanup, 가능한 global uv side effect의 human·JSON diagnostic과 stable exit code를 자동 검증한다. init 전용 file·directory fsync, no-replace publish, parent fsync, marker unlink와 temp·target cleanup 각 단계에는 failure·crash injection을 수행한다. crash 뒤에는 absent target, ownership-marked incomplete/complete target 또는 exact markerless completed tree만 허용하며 existing target은 자동 overwrite하지 않는다.

---

## 24. 구현 언어 및 내부 구조

cott 컴파일러는 Rust로 구현한다.

MVP는 crate 경계를 미리 늘리지 않고 `cott` 단일 crate 안에 다음 module을 둔다. 독립 배포나 compile-time 필요가 생길 때만 분리한다.

```text
cli
manifest
syntax
parser
ast
hir
typeck
contract
ir
python::{emit, binding, loader, verify}
lsp
agent
sandbox
transaction
provenance
diagnostics
formatter
```

핵심 원칙:

* 파서는 복구 가능한 오류를 지원한다.
* 소스 위치 정보를 모든 단계에서 유지한다.
* AST와 HIR을 분리한다.
* emitter가 AST를 직접 참조하지 않는다.
* 모든 대상 언어의 계약 의미는 Canonical IR에서만 가져오고 target 연결 정보는 manifest에서 가져온다.
* 타입 검사기는 agent나 특정 Python 구현에 의존하지 않는다.
* generation record를 제외한 managed compiler 산출물은 IR, target 설정, compiler·runtime version, exact target Python identity·platform, lock과 implementation identity·source/runtime origin·content hash에 대해 결정적이다.
* implementation 본문, source origin과 agent 실행은 durable provenance로 기록하고 verification result는 cache하지 않는다.

`cott lsp`는 parser와 HIR을 재사용하는 editor-analysis surface만 제공한다. 완전한 IDE plugin, generation, publishing과 agent invocation은 이 command의 범위 밖이다.

---

## 25. 향후 확장

v0.2와 v0.3 항목은 이 문서의 구현 범위이며 roadmap이 아니다. 현재 남은 확장은 다음뿐이다.

* async impl method의 task-aware reentrant serialization, cancellation state transition과 invariant semantics
* async iterator/generator의 yield·send·completion·close lifecycle contract
* trait inheritance/specialization, variance와 dynamic dispatch
* recursive user type, SMT proof, additional target backend와 installed-wheel whole-origin verification

`async fn`의 implemented boundary는 sync facade compatibility layer가 없는 top-level free function이다. future async forms는 이 boundary를 넓히기 전에 cancellation과 lifecycle evidence를 정의해야 한다.

### v1.0 이후

* language/IR compatibility policy stabilization
* official additional backend와 package installation model
* IDE plugin


---

## 26. 핵심 설계 결정 요약

### 결정 1

cott는 실행 본문이 없는 선언형 계약 DSL이며 `.cott`와 typed Canonical IR이 의미 원본이다.

### 결정 2

MVP module graph는 비순환이고 source path mapping은 injective며 package 가능한 module은 최소 두 segment다. `core.*`, `cott_runtime`, `_cott_impl`과 `*_types` target path는 예약한다.

### 결정 3

MVP type system은 fixed-width scalar, const generic, heterogeneous tuple, Array/Buffer, nominal newtype/container, immutable struct/enum/resource, associated type를 가진 structural trait와 Cott-owned stateful impl을 제공한다.

### 결정 4

trait default facade dispatch, associated type, resource transition, transitive Cott effect check와 explicit async free function은 구현되었다. trait inheritance/subclassing, ownership, async impl method/generator와 static cleanup proof는 범위 밖이다.

### 결정 5

계약 표현식은 닫힌 순수 언어다. pattern과 clause는 typed IR이고 constant reference identity, error priority·exhaustiveness를 결정적으로 보존한다.

### 결정 6

Python ABI의 표준 identity는 project identity를 embed한 generated `cott_runtime` 하나가 소유한다. alias·trait, impl class, custom enum union·keyword-only frozen variant, struct·newtype, public constant와 resolved public callable의 공개 projection을 구분 없이 보존한다.

### 결정 7

`F32` binary32 normalization은 runtime mode와 무관하며 contract 산술의 매 operation에도 적용한다. integer range는 검사가 활성화된 concrete ABI boundary에서 확인하고 `off`에서는 trust declaration으로 남긴다.

### 결정 8

검증은 정적 증명, runtime 검사, test 관찰, 미관찰과 trust declaration을 구분해 실제보다 강하게 보고하지 않는다.

### 결정 9

자동 계약 테스트는 유효한 pure callable input과 deterministic impl init case를 staged facade를 통해 deny-by-default OS sandbox에서 실행한다. effectful callable과 `Never` 반환 callable은 MVP에서 자동 실행하지 않는다.

### 결정 10

Python free function은 manifest의 plain top-level binding이거나 함수별 `_cott_impl` source다. 각 implementation file은 exact canonical function 하나로 Cott의 최소 public/observable contract를 충족하며 private helper와 literal `Final` constant는 같은 hashed/provenanced file의 비공개 구현 detail이다. impl method는 agent-only canonical private function source이고 compiler가 ordinary slotted class·init·lock·public wrapper를 소유한다. local module은 canonical path의 generated runtime copy로 고정한다. 연결 정보는 Canonical IR가 아니라 target manifest와 provenance에 둔다.

### 결정 11

binding은 import 없이 staged type module에 대해 정적으로 해석한다. 모든 external implementation import에는 frozen production dependency closure의 selected lock hash와 observed installed distribution provenance가 필수며 archive-to-install 연결은 증거가 없으면 trust declaration이다.

### 결정 12

호출자는 cott path의 typed facade만 사용한다. facade는 embedded provenance로 local implementation의 generated copy를 검증하고 direct external dependency origin·hash를 preflight한 뒤 canonical name당 하나의 implementation module만 lazy load하며 load와 invocation을 같은 exception boundary로 감싼다.

### 결정 13

`off`, `boundary`, `test-only`는 facade bytes에 compile-time specialize되어 optional free-function/method ABI·contract 검증 범위만 바꾸며 provenance, F32 normalization, newtype invariant, impl init/state snapshot/invariant/modifies, per-instance serialization과 exception containment는 끄지 않는다.

### 결정 14

`cott generate`는 user-selected Codex CLI 또는 OMP CLI를 callable별 process로, shell 없이 single-file write sandbox staging에서 호출한다.

agent는 실제 project를 쓰지 않고 선택 free-function 또는 impl-method file만 변경한다. scratch와 cache는 workspace 밖으로 격리한다.

### 결정 16

compiler output은 현재 IR과 command-owned scope에서 계산해 stale file을 정리한다. 성공 승격된 agent implementation은 durable source라 자동 삭제하지 않고 stale 상태만 진단한다.

### 결정 17

변경 command는 project lock, 시작·종료 hash, immutable pre-image journal, durable post-image와 atomic state marker를 사용한다. crash 뒤 old 또는 new complete snapshot으로 복구한다.

### 결정 18

runtime reader snapshot isolation은 보장하지 않는다. 변경 중 같은 project process를 실행하지 않고 배포는 완료 뒤 새 process로 시작한다.

### 결정 19

`generation.json.current`는 latest applied state, `last_verified`는 latest full-verified baseline이다. fmt·emit·generate는 후자를 보존하고 full verify만 승격한다.

### 결정 20

partial generate는 verified baseline의 기존 비선택 declaration과 symbol을 보존하되 새 declaration 추가는 허용하고, 최초 baseline 전에는 selected callable scope만 생성할 수 있다. 어느 경우도 배포 상태가 아니다.

### 결정 21

MVP는 generation·verification result cache를 두지 않고 emit·generate와 full verify를 매번 실행한다.

### 결정 22

배포 gate는 unresolved가 없고 current hash가 일치하는 full `cott verify`다.

### 결정 23

BasedPyright 검증은 user config가 아니라 compiler-owned strict config를 사용하며 유일한 diagnostic override는 cott static verifier가 대체하는 `reportInvalidTypeVarUse`다.

### 결정 24

MVP compiler host와 runtime target은 같은 OS family·architecture의 `x86_64` 또는 `arm64` Linux/macOS CPython 3.14이며, generated artifact는 configured CPython full patch version에 고정되고 Python environment당 cott project 하나다.

### 결정 25

`generation.json`과 `generation_id`, exact tool·runtime identity와 managed artifact hash는 machine-local state다. cross-machine diff는 ID 자체가 아니라 normalized contract·public symbol, durable implementation content와 normalized lock·dependency identity를 비교한다.

### 결정 26

`cott init`은 absent target에 minimal scaffold를 만들고 uv에 supported Python minor의 최신 patch 설치·lock·sync만 위임한다. cott는 dependency resolver나 package manager가 아니다.
