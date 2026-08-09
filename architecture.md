# cott 기본 설계 문서

**문서 상태:** Draft v0.1
**프로젝트명:** cott
**파일 확장자:** `.cott`
**CLI 명령:** `cott`


## 0.1 v0.1 릴리스 호환성

이 문서의 v0.1 구현은 CPython `3.14.6`, BasedPyright `1.39.9`, uv `0.12.3`, Codex CLI `0.147.0`, OMP `17.2.12`만 지원한다. 이후 tool version은 이 표, adapter probe golden test와 compatibility test를 함께 변경한 release에서만 지원한다. 지원 범위를 semver range로 넓히지 않는다.

`emit python`과 `verify`는 agent를 호출하지 않는다. agent 호출은 `generate`에서만 조건부로 수행한다. 기존 project command의 `--project <dir>`은 subcommand 뒤 어느 위치에서나 한 번만 허용하며 기본은 현재 directory다. `init`은 target path를 받고 `--project`를 거부한다.
---

## 1. 개요

cott는 함수, 데이터 구조, 오류, 제약 조건을 정밀하게 선언하고, 이를 기반으로 AI 구현을 생성하거나 기존 구현을 안전하게 연결하는 **정적 타입 기반 계약 DSL**이다.

cott 자체는 범용 프로그래밍 언어가 아니다. 반복문, 분기문, 네트워크 호출, 파일 입출력 같은 실제 구현 기능을 제공하지 않는다.

cott의 역할은 다음 세 가지로 제한한다.

1. 프로그램의 구조와 타입을 선언한다.
2. 구현이 지켜야 할 계약을 선언한다.
3. 생성되거나 binding된 코드가 선언된 계약과 일치하는지 검증한다.

기본 대상 언어는 Python이다.

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

Python 구현은 에이전트가 생성하거나 기존 project function에 명시적으로 binding할 수 있다. external library는 project-local typed adapter로 연결한다. test code, 문서와 agent 구현 지시는 모두 cott 선언에서 파생된다.

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

### 3.3 `Any`와 `Unknown`을 기본적으로 금지한다

다음 타입은 기본 언어에 포함하지 않는다.

```text
Any
Unknown
Dynamic
Object
```

동적 데이터가 필요한 경우에도 명시적인 타입을 사용한다.

```cott
JsonValue
Opaque["external-library-object"]
```

`Opaque` 타입은 명시적인 경계에서만 허용하며, 내부 도메인 타입으로 전파할 수 없다.

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

MVP에서 다음 기능은 구현하지 않는다.

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
* 비동기 실행 의미
* 완전한 정리 증명
* cott 자체의 프로그램 합성 엔진

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

`Bool`·고정 폭 숫자·`Str`·`Bytes`·`Path`·`Unit`·`Never`, container constructor, `Option`, `Result`, `JsonValue`와 `Opaque`는 compiler prelude 이름으로 항상 scope에 있다. canonical identity는 `core.*`이며 project source가 `core.*` module이나 같은 prelude 이름을 선언할 수 없다. Python에서는 16.1의 `cott_runtime`이 유일한 runtime identity를 제공한다.

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
```

크기가 불분명한 `int`, `float` 타입은 제공하지 않는다. `Path`는 파일 시스템 경로 값이며 경로의 존재 여부처럼 외부 상태를 읽는 동작은 값의 속성이 아니라 `effects [file.read]`가 있는 함수로 표현한다.

`()`는 `Unit`의 유일한 source value literal이다. `Never`에는 value가 없다.

계약 표현식의 정수 산술은 overflow 없는 mathematical integer로 평가한다. 정수 type의 sign과 bit width는 값 생성과 runtime validation이 활성화된 public boundary에서 range로 검사하며 Python ABI compatibility에서도 별도 metadata로 비교한다.

numeric literal은 선언 type이나 typed operand에서 문맥 type을 얻어야 하며 문맥 없는 literal끼리의 연산은 오류다. unary sign까지 평가한 뒤 integer range를 검사한다.

`F32` 값과 문맥상 `F32`인 literal은 생성·statically concrete public boundary에서 IEEE 754 binary32로 반올림한 뒤 저장하고 구현에 전달한다. 이 ABI normalization은 `runtime_validation = "off"`에서도 유지한다. erased `TypeVar` 뒤의 숫자 관계는 정적으로만 검사한다. `F64`는 Python binary64 `float`를 그대로 사용한다.

`Str`은 Unicode scalar sequence이며 활성 runtime validation은 surrogate code point를 거부한다. `Str.len`은 scalar 개수, `Bytes.len`은 byte 개수, 컨테이너의 `.len`은 원소 또는 map 항목 개수이며 모든 `.len` expression의 cott type은 `U64`다. `off`에서 외부 `str`의 scalar 유효성은 trust declaration이다.

`JsonValue`와 `Opaque["tag"]`는 12.5의 명시적 경계 타입이며 일반 원시 타입의 암묵적 대체재가 아니다.

---

### 5.4 컨테이너 타입

```cott
List[T]
Set[T]
Map[K, V]
Tuple[T1, T2]
Option[T]
Result[T, E]
```

MVP의 `Tuple`은 정확히 두 원소만 가진다. 다른 arity는 const generic과 함께 이후 버전에서 도입한다.

예시:

```cott
struct Collection:
    entries: List[User]
    by_id: Map[UserId, User]
    description: Option[Str]
```

컨테이너는 불변이며 타입 인자도 invariant다.

Python MVP는 일반 `list`, `set`, `dict`를 공개 ABI로 사용하지 않는다. `cott_runtime`의 invariant 명목 타입 `CottList[T]`, `CottSet[T]`, `FrozenMap[K, V]`, `CottTuple2[T1, T2]`를 사용한다. 저장소는 각각 private `tuple`, `frozenset`, 복사한 `dict`의 `MappingProxyType`, 길이 2의 `tuple`이며 read-only sequence·set·mapping·pair 연산만 노출한다. 변환 생성자는 입력을 한 번 복사하고 이후 가변 원본을 노출하지 않으며 공개 경계는 일반 Python 컨테이너를 암묵 변환하지 않는다.

```text
List[Dog]는 List[Animal]의 하위 타입이 아니다.
```

공변성과 반공변성은 MVP 이후 별도 문법으로 도입한다.

`Set[T]`의 `T`와 `Map[K, V]`의 `K`는 compiler의 hash-stable 타입이어야 한다. 허용되는 기반 타입은 `Bool`, 정수, `Str`, `Bytes`, `Path`와 이들로만 구성된 newtype·payload 없는 enum·pair tuple이다. float, struct, container, `JsonValue`, `Opaque`, trait와 type parameter는 MVP key position에서 거부한다.

### 5.5 어휘와 선언 문법

source는 UTF-8이다. identifier는 ASCII `[A-Za-z_][A-Za-z0-9_]*`로 제한한다. module·function·field·parameter는 `snake_case`, type·trait·enum variant는 `UpperCamelCase`, constant는 `UPPER_SNAKE_CASE`다. `module`, `use`, `alias`, `newtype`, `where`, `struct`, `enum`, `trait`, `const`, `fn`, `self`, `doc`, `requires`, `ensures`, `when`, `effects`, `true`, `false`, `and`, `or`, `not`은 keyword다. `result`는 pattern 없는 `ensures` expression scope에서만, `error`는 function clause 시작에서만 예약되는 contextual keyword이므로 field와 payload에서는 사용할 수 있다. prelude type 이름도 user declaration으로 가릴 수 없다.

Python target validation은 CPython 3.14 hard keyword와 단독 `_`를 identifier로 거부하고 `_cott_` prefix 또는 `__`로 시작하거나 끝나는 user name도 예약한다. target projection 뒤 모든 이름에 같은 검사를 적용하므로 emitter가 identifier를 escape하거나 rename하지 않는다.

일반 문자열은 JSON escape를 사용하는 double-quoted literal이고 `doc`만 triple double quote를 사용한다. 정수는 10진수, float는 소수점 또는 exponent가 있는 10진수이며 빈 괄호 `()`는 `Unit` literal이다. 부호는 literal이 아니라 unary operator다. tab과 semicolon은 금지한다. parser는 일관된 space indentation을 받고 formatter는 4칸으로 정규화한다. `#`부터 newline까지는 comment다. blank 또는 comment-only physical line은 `NEWLINE`, `INDENT`, `DEDENT` token을 만들지 않는다.

다음 EBNF가 MVP의 선언 surface다. `INDENT`와 `DEDENT`는 indentation token이고 `{x}`는 0회 이상, `[x]`는 선택이다.

```text
file          = module_decl, { use_decl }, { declaration } ;
module_decl   = "module", qname, NEWLINE ;
use_decl      = "use", qname, [ ".{", name_list, "}" ], NEWLINE ;

declaration   = ( [ doc_block ], ( alias_decl | newtype_decl | struct_decl
                | enum_decl | trait_decl | const_decl ) ) | fn_decl ;
alias_decl    = "alias", type_name, "=", type, NEWLINE ;
newtype_decl  = "newtype", type_name, "(", type, ")", NEWLINE,
                [ INDENT, "where", expression, NEWLINE, DEDENT ] ;
struct_decl   = "struct", type_name, [ generic_params ], ":", NEWLINE,
                INDENT, field, { field }, DEDENT ;
enum_decl     = "enum", type_name, [ generic_params ], ":", NEWLINE,
                INDENT, variant, { variant }, DEDENT ;
trait_decl    = "trait", type_name, [ generic_params ], ":", NEWLINE,
                INDENT, trait_method, { trait_method }, DEDENT ;
const_decl    = "const", const_name, ":", type, "=", const_expr, NEWLINE ;
const_expr    = expression | qname, "(", const_expr, ")" ;

field         = field_name, ":", type, [ "=", const_expr ], NEWLINE ;
variant       = variant_name, [ "(", parameter_list, ")" ], NEWLINE ;
trait_method  = "fn", function_name, "(", "self",
                [ ",", parameter_list ], ")", "->", type, NEWLINE ;
fn_decl       = "fn", function_name, [ generic_params ],
                "(", [ parameter_list ], ")", "->", type,
                ( NEWLINE | ":", NEWLINE, INDENT, clause, { clause }, DEDENT ) ;
parameter_list = parameter, { ",", parameter }, [ "," ] ;
parameter     = parameter_name, ":", type ;

clause        = doc_block | "requires", expression, NEWLINE
              | "ensures", [ pattern, "=>" ], expression, NEWLINE
              | "error", qname, [ "when", expression ], NEWLINE
              | "effects", "[", [ qname, { ",", qname } ], "]", NEWLINE ;
doc_block     = "doc", triple_string, NEWLINE ;

generic_params = "[", generic_param, { ",", generic_param }, [ "," ], "]" ;
generic_param = type_name, [ ":", type, { "+", type } ] ;
type          = qname, [ "[", type_arg, { ",", type_arg }, [ "," ], "]" ] ;
type_arg      = type | string_literal ;
qname         = identifier, { ".", identifier } ;
name_list     = identifier, { ",", identifier }, [ "," ] ;
type_name     = identifier ; variant_name = identifier ;
function_name = identifier ; field_name = identifier ;
parameter_name = identifier ; binding_name = identifier ;
const_name    = identifier ;
```

여러 줄 parameter·generic 목록의 trailing comma는 허용하고 formatter가 붙인다. function parameter default와 overload는 문법에 없다. `self`의 무타입 표기는 trait method의 첫 parameter에서만 허용한다. string type argument는 `Opaque["tag"]`에만 허용한다.

`()`·`[]`·`{}` 안에서는 newline과 indentation token을 무시한다. clause expression은 한 logical line이어야 하며 여러 줄로 나누려면 괄호 안에 작성한다.

function block에는 `doc` 최대 하나, `requires`·`ensures`·`error` 각 0개 이상, `effects` 최대 하나가 이 순서로 온다. top-level `doc`은 바로 다음 type 또는 constant declaration에 붙으며 orphan·중복 doc은 오류다.

expression precedence는 낮은 순서로 `or`, `and`, unary `not`, comparison, `+ -`, `* / %`, unary `+ -`, field/`.len`, primary다. comparison은 `== != < <= > >=`이며 연쇄 비교를 허용한다. primary는 scalar literal, `Unit` literal `()`, 현재 scope의 name·constant·enum singleton과 괄호식이다. 임의 call, index, collection literal과 attribute method call은 계약 표현식에 없다.

arithmetic operand는 같은 numeric type이어야 한다. `/`는 float에만, `%`는 integer에만 허용하고 unary `-`는 unsigned type에 허용하지 않는다. integer contract 중간값은 declared width를 넘을 수 있는 mathematical integer며 remainder는 `0 <= r < abs(divisor)`인 Euclidean remainder다. emitter는 `%`를 Python operator가 아니라 `cott_runtime._cott_euclidean_mod`로 낮춘다. zero divisor는 compile-time constant에서 semantic error, runtime clause에서 `CottContractViolation`이다. `F32` 중간 결과는 매 연산 후 binary32, `F64`는 binary64로 평가한다. compiler constant evaluator와 runtime clause·refinement evaluator는 같은 규칙을 쓰며, emitter는 `F32`의 `+ - * /` 결과를 매번 `cott_runtime` binary32 rounding helper로 낮춘 뒤 비교한다.

```text
pattern = "_" | binding_name
        | qname, [ "(", [ pattern, { ",", pattern } ], ")" ] ;
```

binding은 `snake_case`, variant의 마지막 segment는 `UpperCamelCase`이므로 모호하지 않다. pattern의 payload arity와 타입은 반환 타입에 대해 검사한다.

---

## 6. 사용자 정의 타입

user type declaration은 같은 module의 forward reference를 사용할 수 있지만 alias·newtype·struct·enum·trait dependency graph 전체가 acyclic이어야 한다. container로 감싼 self-reference도 MVP에서는 거부하고 emitter는 resolved DAG를 topological order로 생성한다.

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

newtype carrier는 `Never`, trait와 `Opaque`를 제외한 cott immutable value type이어야 하며 alias를 먼저 해소한다.

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

trait는 Python 객체가 구조적으로 제공해야 하는 method signature 집합이다.

```cott
trait Repository[Entity, Id]:
    fn find(self, id: Id) -> Result[Option[Entity], RepositoryError]
    fn save(self, entity: Entity) -> Result[Unit, RepositoryError]
```

MVP trait는 비어 있을 수 없고 method signature만 가진다. method에는 generic parameter, default, body, `doc`, contract와 `effects`를 붙일 수 없다. `self`는 첫 parameter이며 generated Python `Protocol`에서는 instance parameter로 변환한다.

trait는 generic bound와 function parameter type에 사용할 수 있다.

```cott
fn load_user(
    repository: Repository[User, UserId],
    id: UserId,
) -> Result[Option[User], RepositoryError]
```

Python emitter는 `@runtime_checkable` `typing.Protocol`을 생성한다. BasedPyright와 cott static verifier가 method name, parameter kind·type와 return type을 구조적으로 비교한다. boundary checker는 parameterized Protocol에 `isinstance`를 호출하지 않고 `inspect.getattr_static`으로 origin Protocol의 required member presence만 확인해 descriptor를 실행하지 않는다. annotation과 generic 관계는 정적 보증으로 보고한다.

cott generic parameter는 trait에서도 invariant다. PEP 544 checker가 method position이나 occurrence count만 보고 다른 variance 또는 불필요한 `TypeVar`를 요구할 수 있으므로 compiler-owned BasedPyright invocation은 `reportInvalidTypeVarUse`를 run-wide로 끈다. cott static verifier가 exact file set의 모든 TypeVar declaration·bound·occurrence와 invariance를 대신 검사하며 source의 diagnostic suppression과 다른 checker suppression은 거부한다.

trait method는 top-level cott function이 아니므로 facade, binding, agent generation과 contract test 대상이 아니다. `struct implements Trait`, nominal marker, default implementation, runtime dispatch와 class inheritance는 MVP에서 제공하지 않는다.

---

## 8. 제네릭

### 8.1 기본 제네릭

```cott
struct Page[T]:
    items: List[T]
    total: U64

fn first[T](items: List[T]) -> Option[T]
```

### 8.2 Trait bound

```cott
fn save_all[T: Serializable](
    values: List[T],
) -> Result[Unit, SaveError]
```

복수 제약:

```cott
fn compare[T: Comparable + Serializable](
    left: T,
    right: T,
) -> Ordering
```

Python emitter는 복수 제약을 각 trait `Protocol`을 모두 상속하는 합성 `Protocol`로 만들고 `TypeVar(bound=CompositeProtocol)`로 사용한다. `TypeVar`의 선택형 constraints로 약화하지 않는다. bound trait끼리 같은 method 이름이 있으면 parameter·return signature가 구조적으로 동일해야 하며 다르면 HIR error다.

### 8.3 제네릭 규칙

MVP에서는 다음 규칙을 적용한다.

* 제네릭 타입은 기본적으로 invariant다.
* 생성된 Python 컨테이너와 사용자 제네릭도 invariant `TypeVar`를 사용한다.
* generic type reference의 type argument는 exact arity로 명시한다.
* generic function 호출의 type variable은 target static checker가 argument에서 추론하며 cott MVP에는 call expression이나 explicit call-site type argument 문법이 없다.
* bound는 중복 없는 trait type만 허용하고 미해결 type variable과 암묵적인 `Any` 대체는 오류다.
* 재귀적인 무한 타입은 거부한다.

Python runtime은 지워진 `TypeVar`를 복원하거나 호출별로 통합하지 않는다. `List[InputPayload]`처럼 facade 시그니처에 구체화된 중첩 타입은 런타임 검사할 수 있지만 `first[T]`의 입력과 반환 사이 관계는 BasedPyright와 cott 정적 verifier의 보증이며 런타임 검사로 보고하지 않는다.

---

## 9. 함수 선언

cott의 함수는 실행 본문을 가지지 않는다.

함수 블록에는 다음 요소만 들어갈 수 있다.

* `doc`
* `requires`
* `ensures`
* `error`
* `effects`

기본 예시:

```cott
fn repeat(data: Bytes, count: U64) -> Result[Bytes, RepeatError]:
    doc """
    입력 데이터를 지정한 횟수만큼 반복한다.
    """

    requires count > 0

    ensures Result.Ok(output) => output.len == data.len * count
```

함수 오버로딩은 MVP에서 금지한다.

함수 parameter default는 금지한다. 호출 option은 default field가 있는 struct로 묶는다.

MVP cott function parameter는 모두 Python positional-or-keyword parameter로 emit한다. positional-only와 keyword-only function parameter 문법은 이후 버전 범위다.

같은 모듈 안에서는 함수 이름이 유일해야 한다.

---

## 10. 계약

### 10.1 계약 표현식

refinement, `requires`, `ensures`, 조건부 `error`는 하나의 정규화된 순수 표현식 언어를 사용한다.

허용 대상:

* 숫자, 문자열, boolean과 `Unit` literal `()`
* 함수 인자와 cott 상수
* `ensures`에서만 사용할 수 있는 반환값 전체인 `result`
* refinement에서만 사용할 수 있는 기반 타입 값 `self`
* cott 값의 필드 접근과 `Str`, `Bytes`, 컨테이너의 `.len`
* 산술, 연쇄 비교, 동등성, `and`, `or`, `not`

`ensures` 문법은 `ensures [pattern =>] expression`이다. `=>`는 expression operator가 아니다. pattern은 enum variant, 재귀 payload pattern, 이름 binding과 wildcard `_`로 구성한다. variant는 반환 type에 속해야 하고 payload arity가 정확해야 하며 binding은 pattern 안에서 한 번만 선언한다. binding은 function argument나 visible constant를 가릴 수 없고 `result`와 `self`도 사용할 수 없다.

금지 대상:

* 선언되지 않은 ambient 이름
* 파일, 네트워크, 데이터베이스, 시계와 난수 접근
* 객체 메서드 호출과 임의 Python 함수 호출
* 상태 변경과 비결정적 표현식

표현식의 모든 이름과 타입은 HIR에서 해석한다. 숫자 literal은 문맥 type을 따르고 연쇄 비교는 각 operand를 한 번 평가하는 short-circuit `and`로 정규화한다. 계약 표현식에서 arithmetic·ordering·equality operand의 동일성은 alias를 해소하고 newtype을 carrier type으로 정규화한 뒤 판단한다. arithmetic과 ordering operand는 같은 numeric type이어야 한다. equality operand는 같은 resolved non-trait cott value type이어야 하며 type parameter, trait 또는 `Opaque`를 transitive하게 포함할 수 없다. boolean operator는 short-circuit하며 모든 refinement, `requires`, `ensures`와 `when`의 최종 type은 `Bool`이어야 한다. MVP contract language에는 function call이 없다.

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

pattern이 없으면 expression scope는 function argument, constant와 반환값 전체를 가리키는 `result`다. pattern이 있으면 일치하는 반환에서만 expression을 검사하고 scope는 function argument, constant와 그 pattern binding이며 `result`는 사용할 수 없다. 반환 type 검사 후 source order의 모든 applicable `ensures`를 검사한다. MVP에는 호출 전 가변 상태 snapshot인 `old()`를 제공하지 않는다.

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

`error Variant when condition`은 조건이 참인 생성 사례에서 해당 variant를 반환해야 하는 검사 가능한 의무다. 둘 이상의 조건이 참이면 source order에서 첫 번째 조건부 절만 의무가 되고 뒤 절은 면제된다. 조건 없는 `error Variant`는 허용된 환경 실패를 선언할 뿐 항상 일치하는 조건으로 취급하지 않는다.

`Result` 함수에 `error` 절이 하나라도 있으면 그 목록은 허용된 오류 variant의 exhaustive set이다. 런타임 검사가 활성화된 facade는 모든 `Err` 반환이 이 집합에 속하는지 검사한다. `off`에서는 이 항목을 신뢰 선언으로 낮춘다. `error` 절이 전혀 없으면 반환 오류 타입만 보장하고 모든 variant의 발생 조건을 신뢰 선언으로 보고한다.

`error`는 `Result[T, E]` function에만 올 수 있고 variant는 `E`에 속해야 한다. conditional `when`은 argument와 constant만 참조하는 `Bool` expression이다. 같은 variant의 여러 conditional clause는 허용하지만 완전히 중복된 clause와 같은 variant의 unconditional clause 중복은 오류다.

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

MVP에서 `effects`는 Canonical IR metadata이자 trust declaration이다. cott function에는 실행 body가 없고 Python implementation의 hidden call graph를 분석하지 않으므로 일반 effect propagation을 증명하지 않는다. contract language 자체에는 call이 없다. implementation-level propagation은 v0.3에서 도입한다.

---

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

값이 존재하지 않는 상황은 `Option`으로 표현한다. `Nothing`은 Python 예약어 `None`과 충돌하지 않는 표준 빈 variant다.

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

`Opaque["tag"]` tag는 `[a-z][a-z0-9._-]{0,63}`이어야 한다. 이 type은 manifest-bound function의 direct parameter 또는 return success value가 `Opaque`, `Option[Opaque]`, `Result[Opaque, E]`인 경우에만 허용한다. error payload, alias, newtype, 다른 container 원소, struct·enum field와 trait의 transitive occurrence는 HIR 오류다. 이 boundary classification은 IR에 보존한다.

Python ABI는 invariant `cott_runtime.Opaque[Literal["tag"]]` frozen wrapper 하나로 고정하고 instance의 literal tag도 runtime에 저장한다. 두 wrapper는 tag가 같고 wrapped object가 `is`로 같을 때만 동등하며 wrapped object의 equality를 호출하지 않고 hash도 제공하지 않는다. `unwrap() -> object`를 제공하며 adapter는 concrete external type으로 명시적으로 `cast`한다. `Any`·`Unknown`과 agent-generated function의 `Opaque`는 허용하지 않는다.

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

MVP constant expression은 scalar literal, imported constant 또는 같은 module에서 앞서 선언된 constant, arithmetic·boolean operator, enum singleton과 newtype constructor로 제한한다. struct field default도 같은 scope를 사용하며 다른 field를 참조하지 않는다. compiler가 타입 검사·평가·숫자 정규화·refinement 검사를 마친 canonical value를 IR에 저장하므로 module DAG와 source order상 value dependency도 acyclic하다.

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
NewtypeDecl
RequiresClause
EnsuresClause
```

### 15.3 HIR

HIR은 이름이 해석되고 타입 표현이 정규화된 내부 구조다.

예를 들어 다음 두 타입 표현은 HIR에서 같은 심볼을 가리킨다.

```cott
InputPayload
system.data.InputPayload
```

### 15.4 Canonical IR

Canonical IR은 에이전트나 특정 언어 문법에 종속되지 않는 정규 표현이다. 다음 JSON은 필드 형태를 보여 주는 비규범 표시 fragment이며 schema-conformant instance가 아니다. `clause_id`, 완전한 span과 resolved type 등 반복 field는 지면상 생략했고, `equal`과 `integer`는 설명용 shorthand다. exact schema tag를 이 예시에서 추정하지 않으며 normative schema와 target은 이 shorthand를 소비하지 않는다.

실제 IR file의 top-level object는 `schema_version`, fully qualified `module`, project-relative `source`, sorted `imports`와 `declarations`를 필수로 가진다. declaration은 공통 `kind`·fully qualified `name`·`public`·`doc`·`span`을, function은 generic parameter·parameter·return type·contract·effect를 추가로 가진다.

type node kind는 `primitive`, `named`, `type_parameter`, `list`, `set`, `map`, `tuple2`, `option`, `result`, `opaque`로 닫혀 있다. alias는 IR type에서 제거하고 `named`는 fully qualified declaration과 generic argument를 가진다. expression node는 resolved cott `type`을 필수로 가지며 parameter·field·constant·variant reference는 canonical symbol identity를 저장한다. pattern도 resolved variant·payload type과 binding identity를 가진다.

declaration kind와 추가 field는 닫혀 있다: `alias(target)`, `newtype(carrier, refinement)`, `struct(generic_parameters, fields)`, `enum(generic_parameters, variants)`, `trait(generic_parameters, methods)`, `const(type, value)`, `function(generic_parameters, parameters, return_type, contracts, effects)`. generic parameter는 scoped canonical identity와 ordered bound, field·parameter는 name·resolved type·default 또는 `null`·span, variant는 canonical identity와 ordered payload field, trait method는 body 없는 function signature를 가진다. optional doc·refinement·default도 없으면 생략하지 않고 `null`로 쓴다.

expression kind는 typed literal, parameter·binding·`self`·constant·enum singleton reference, field, len, unary, binary와 comparison chain으로 닫혀 있고 모든 source node는 span을 가진다. schema version마다 compiler와 함께 배포하는 `canonical-ir.schema.json`이 normative하며 compiler는 emit 직전과 IR load 직후 schema를 검증한다. 아래 축약 JSON은 normative schema를 대체하지 않는다.

integer canonical value는 sign을 포함한 base-10 string, `F32`·`F64`는 width와 IEEE bit-pattern lowercase hex, `Bool`·`Str`은 JSON scalar, `Bytes`는 lowercase hex, `Unit`은 typed null로 저장한다. platform-dependent `Path`, `Never`와 `Opaque`에는 compile-time value가 없다. enum·newtype·container·`JsonValue`는 type node와 child value로 재귀 표현한다. list·tuple·field는 declaration order, set element와 map entry는 typed canonical key JSON bytes order다. numeric literal도 contextual type과 normalized value를 가지므로 target이 type을 재추론하지 않는다.

declaration, field, parameter와 contract clause array는 source order를 보존한다. 의미가 set인 effect와 import는 fully qualified name으로 정렬한다. source span은 raw UTF-8의 0-based start·exclusive-end byte offset과 1-based line·Unicode-scalar column을 함께 가진다. 예시의 span과 resolved type은 지면상 축약했다. schema에 없는 field는 거부한다.

IR JSON은 sorted key, insignificant whitespace 없음, final newline 하나로 canonicalize하고 schema version을 `generation_id`에 포함한다.

v0.1의 normative schema는 repository의 `schemas/canonical-ir.schema.json`, `schemas/generation.schema.json`, `schemas/diagnostics.schema.json`, `schemas/contract-test.schema.json`이다. 모두 JSON Schema Draft 2020-12, version `1`이며 compiler binary가 `include_str!`로 embed한다. IR·generation·diagnostic·contract strategy writer와 reader는 해당 schema를 동시에 검증한다.

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
`tests/generated/<module path>/<function>.json`은 compiler가 실행하는 deterministic managed contract-test strategy다. 닫힌 object는 `{"schema_version":1,"symbol":<FQN>,"seed":"sha256:<hex>","candidate_limit":64,"container_length_limit":3,"json_depth_limit":4,"classification":"pure"|"effectful"|"never","clause_ids":[<source-order IDs>]}`이며 generated Python source가 해석하지 않는다.

`cott_runtime`은 numeric alias `I8`…`U64`·`F32`·`F64`, generic alias `Option`·`Result`, `Ok`·`Err`·`Some`·`Nothing`, `Unit`·`UNIT`, `Opaque`, nominal container, numeric metadata, `JsonValue` union·variant와 `CottContractViolation`의 유일한 runtime identity 원본이다. 각 `<module>_types.py`는 그 cott module의 user type·constant만 정의한다. standard ABI type은 `cott_runtime`에서 직접 import하며 module별로 re-export하지 않는다. compiler-owned support package는 Canonical IR 밖 관리 file로 허용한다.

MVP는 Python environment 하나에 generated cott project 하나만 설치한다. `cott_runtime`과 각 facade는 normalized `[project].name` identity를 함께 embed하고 서로 다르면 import를 거부한다. 다른 distribution이 이미 `cott_runtime`을 소유한 environment도 verify에서 거부해 package file collision을 조용히 허용하지 않는다.

generated module의 support import와 helper는 reserved `_cott_` prefix를 사용하고 `__all__`에 넣지 않는다. 따라서 class body에서도 name mangling 없이 참조하고 user symbol을 rename하지 않은 채 runtime name 충돌을 피한다.

`generated/python`은 public cott module, `cott_runtime`과 verified local implementation copy를 함께 담는 단일 runtime·package root다. 완전히 타입이 지정된 `bar.py` facade가 공개 계약 표면이며 각 public package는 `py.typed`를 포함한다.

`facade_exports(IR, resolved)`는 `public_python_symbols(IR)`의 모든 비함수 symbol과 이번 세대에 구현이 해석된 공개 함수 symbol의 합집합이다. facade의 `__all__`은 이 집합과 정확히 같다. `verified = true`인 세대에서는 unresolved가 없어 `facade_exports`가 전체 `public_python_symbols`와 같아야 한다. 미구현 함수는 `generation.json.current.unresolved`에 기록한다. `cott_runtime`을 제외한 모든 compiler-owned package `__init__.py`는 비어 있고 re-export하지 않는다.

`bar_types.py`는 구현과 adapter가 공유하는 지원 대상 typing boundary지만 공개 함수의 대체 import 경로는 아니다. `generated/stubs`의 `.pyi`는 도구 산출물이며 runtime import path에 넣지 않는다.

resolved local binding과 agent implementation module은 source bytes를 canonical Python module path 아래에 그대로 복사한다. compiler가 만든 empty parent `__init__.py` 외에는 같은 package의 다른 source를 복사하지 않는다. external distribution module은 복사하지 않는다. source file은 durable 원본, generated copy는 compiler-owned runtime artifact이며 두 hash가 다르면 verify가 실패한다.

`generation.json`은 두 snapshot을 가진다.

* `current`: 마지막 성공 apply의 입력·구현·관리 파일 hash, unresolved 집합과 `verified` 상태
* `last_verified`: 마지막 full verify의 정규화 계약 snapshot, Python 공개 표면과 관리 파일 hash 또는 최초 검증 전 `null`

record의 필수 field를 보여 주는 다음 JSON은 객체·배열 entry 일부를 지면상 생략한 비규범 fragment이며, 그 자체로 schema-conformant record가 아니다. 실제 `contract_surface`와 `public_python_symbols`는 아래 규칙대로 축약 없이 저장한다.

```json
{
  "schema_version": 1,
  "current": {
    "generation_id": "sha256:...",
    "verified": false,
    "inputs": {"AGENTS.md": "sha256:...", "cott.toml": "sha256:...", "python/pyproject.toml": "sha256:...", "python/uv.lock": "sha256:...", "src/foo/bar.cott": "sha256:..."},
    "tools": {
      "compiler": {"version": "0.1.0", "executable": "/canonical/cott", "content_hash": "sha256:..."},
      "runtime": {"version": "0.1.0"},
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

project-owned path는 project-relative POSIX path이고 dependency import origin만 distribution-relative POSIX path다. hash는 raw file bytes의 SHA-256 lowercase hex다. map key와 set-derived array를 정렬한 UTF-8 JSON으로 쓰며 file 끝 newline 하나만 둔다. `generation.json` 자체는 self-reference를 피하려고 `managed_files`에서 제외한다. `generation_id`는 domain tag, top-level `schema_version`과 current에서 `generation_id`·`verified`·`verification`·`agent_runs`를 뺀 canonical object의 hash다. `last_verified`는 pointer가 아니라 verified current snapshot의 deep copy다.

`agent_runs`는 현재 agent implementation content hash와 일치하는 함수별 마지막 successful run만 담는다. 이후 emit·verify에서도 hash가 같으면 보존하고 agent 재생성 시 교체하며 user edit로 hash가 달라지면 제거한다. 실패·폐기된 run과 무제한 history는 generation record에 누적하지 않는다.

canonical executable path와 binary hash를 포함하므로 `generation_id`는 같은 machine·tool installation의 generation instance identity이지 cross-machine reproducible build ID가 아니다. portable 비교는 Canonical IR, `contract_surface`, `public_python_symbols`, durable implementation content hash와 normalized lock·dependency identity를 사용한다. exact tool·runtime identity와 machine-specific constant를 embed한 managed artifact hash는 같은 target environment 안에서만 비교한다. `generation.json`은 machine-local state이고 wheel에 포함하지 않는다.

`dependencies`는 허용된 external import마다 normalized distribution name·version, 현재 platform에서 lock이 선택한 `lock_artifact_hash`, 관찰한 installed metadata content hash와 distribution-relative module origin·content hash를 기록한다. lock artifact hash는 기대값이고 immutable archive나 검증 가능한 installer receipt가 없는 MVP 설치 환경에서 installed bytes가 그 archive에서 왔음을 증명하지 않는다. 이 연결은 명시적 신뢰 선언이며 loader는 verify가 관찰해 고정한 installed bytes를 검사한다. generated module과 standard library는 제외하며 후자는 exact CPython provenance로 고정한다. project-local import는 16.5.1에 따라 허용하지 않는다.

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
| `List[T]` | invariant `cott_runtime.CottList[T]` |
| `Set[T]` | invariant `cott_runtime.CottSet[T]` |
| `Map[K, V]` | invariant `cott_runtime.FrozenMap[K, V]` |
| `Tuple[T1, T2]` | invariant `cott_runtime.CottTuple2[T1, T2]` |
| `Option[T]` | `Some[T] \| Nothing`; `Some(value=...)`, `Nothing()` |
| `Result[T, E]` | `Ok[T] \| Err[E]`; `Ok(value=...)`, `Err(error=...)` |
| 사용자 `enum E` | 모든 `E_<Variant>` frozen class의 `TypeAlias` union `E` |
| `struct` | `@dataclass(frozen=True, slots=True, kw_only=True)` |
| `trait` | structural `typing.Protocol` |
| 복수 trait bound | 모든 bound를 상속한 합성 `Protocol` |
| `newtype` | 조건을 검사하는 명목 wrapper class |
| `alias` | type alias |
| `const` | `<module>_types.py`의 `Final[ABI type]` |
| `JsonValue` | `cott_runtime`의 고정 recursive tagged union |
| `Opaque["tag"]` | invariant `cott_runtime.Opaque[Literal["tag"]]` |

`JsonValue`의 Python variant는 `JsonNull`, `JsonBoolean`, `JsonInteger`, `JsonFloat`, `JsonString`, `JsonArray`, `JsonObject`로 고정하며 union alias 이름은 `JsonValue`다. `Unit()`은 singleton `UNIT`을 반환하고 모든 `Nothing()` 값은 같은 zero-payload variant끼리 동등하다.

모든 newtype 생성자는 alias를 해소한 carrier ABI를 모든 mode에서 검사하고 statically concrete `F32` path를 exact `float`에서 binary32로 normalize한다. function input·output의 statically concrete `F32`도 모든 mode에서 같은 처리를 한다. 그 밖의 function scalar runtime check가 활성화되면 exact `bool`·`int`·`float`·`str`·`bytes`, integer range와 `Str`의 surrogate 부재를 검사해 `bool`을 integer로, integer를 float로 받지 않는다. newtype carrier의 `Str` scalar 유효성은 생성자가 모든 mode에서 검사한다. `Path` runtime 값은 지원 platform의 exact `pathlib.PosixPath`여야 하며 user subclass는 거부한다.

표준 union variant는 `Ok(value=...)`, `Err(error=...)`, `Some(value=...)`, `Nothing()`으로 고정한다. 사용자 enum의 모든 variant도 keyword-only frozen class다. cott의 `BarError.InvalidPayload`와 `BarError.ServiceUnavailable`은 Python의 `BarError_InvalidPayload(reason=...)`, `BarError_ServiceUnavailable()`가 되고 `BarError`는 이 class들의 union alias다.

`Unit`, `Opaque`, nominal container, standard·`JsonValue`·사용자 enum variant, struct와 newtype의 concrete class는 모두 `@typing.final`이고 runtime validator도 exact class identity를 요구한다. trait `Protocol`만 member-presence 구조 검사를 사용한다.

alias 이름, trait `Protocol`, enum union alias와 underscore-delimited variant class, struct, newtype, public constant와 구현이 해석된 공개 함수는 facade가 re-export하는 IR-derived public Python symbol이다. compiler-synthesized `TypeVar`와 복수 bound 합성 `Protocol`은 private `_cott_` support name이며 export하지 않는다. payload·struct field의 선언 순서와 이름은 ABI다. `Result[Unit, E]`의 성공값은 `Ok(value=UNIT)`다. target symbol projection에서 이름 충돌이 나면 emit 전에 실패한다.

BasedPyright는 `Annotated[int, ...]`의 width 차이만으로 type을 구분하지 못하므로 cott static binding verifier가 implementation signature의 sign·width·precision metadata까지 비교한다. 일반 Python caller의 width 구분은 정적 증명으로 보고하지 않으며 활성 boundary의 value range 검사, `off`의 trust declaration으로 남는다. facade는 statically concrete `F32` path를 모든 mode에서 normalize하고 그 밖의 numeric range와 값은 구성된 validation mode를 따른다. `typing.NewType`은 runtime identity가 없으므로 사용하지 않는다.

`CottList`는 tuple-backed `Sequence`, `CottSet`은 frozenset-backed `Set`, `FrozenMap`은 private `MappingProxyType` 기반 read-only `Mapping`, `CottTuple2`는 길이 2의 heterogeneous `Sequence`다. public keyword-only constructor는 각각 `CottList(*, values: Iterable[T])`, `CottSet(*, values: Iterable[T])`, `FrozenMap(*, values: Mapping[K, V])`, `CottTuple2(*, first: T1, second: T2)`다. 이미 같은 nominal container인 입력은 private immutable backing을 재사용하고 그 밖의 입력은 새 private backing으로 한 번 materialize한다. public boundary는 raw Python container를 암묵 변환하지 않는다.

`CottTuple2`는 read-only `.first`·`.second`와 `Literal[0]`·`Literal[1]` `__getitem__` overload를 제공한다. 모든 nominal container의 equality는 같은 cott runtime class와 contents에 대해서만 성립하며 native Python container와는 같지 않다.

cott key admissibility는 5.4의 static classifier가 결정한다. `CottTuple2.__hash__`는 Python tuple처럼 두 runtime 원소에 위임하므로 unhashable 원소면 `TypeError`가 나지만 compiler는 두 component type이 모두 hash-stable인 instantiation만 key position에 허용한다. payload 없는 enum과 허용된 carrier의 newtype은 hashable하다. `CottList`, `CottSet`, `FrozenMap`, struct, payload enum, 표준 union·`JsonValue` variant, `Unit`과 `Opaque`는 `__hash__ = None`이다.

---

### 16.3 타입 검사

Python 구현은 compiler가 scratch에 만든 전용 BasedPyright config와 explicit `--project`로 검사한다. config는 exact file set, CPython version·platform, generated root와 tool-only stub root를 고정하고 다른 `extraPaths`를 두지 않는다. user `pyproject.toml`의 BasedPyright 설정은 verification에 사용하지 않는다.

```json
{"typeCheckingMode": "strict", "reportInvalidTypeVarUse": "none"}
```

manifest의 interpreter와 type checker executable은 shell 없이 canonical regular-file path로 실행하고 full version·content hash를 provenance에 기록한다. 설정된 interpreter가 정확히 CPython `3.14.6`이 아니거나 BasedPyright version이 정확히 `1.39.9`가 아니면 Python target 검증을 시작하지 않는다. compiler-owned config의 유일한 완화는 7장의 `reportInvalidTypeVarUse`이며 cott static verifier가 대신 검사한다. source의 `type: ignore`·`pyright:` suppression과 checker command/config injection은 거부한다.

interpreter identity probe, BasedPyright version probe·검사 process와 그 runtime child는 compiler-owned containment 안에서 실행한다. 실제 project path는 보이지 않고 staging input, standard library와 locked distribution은 read-only이며 cache·temporary output만 scratch에 쓸 수 있다. network·device와 environment secret을 차단하고 compiler-version-fixed wall timeout, process·memory·open-file ceiling과 stdout·stderr 한도를 적용하며 종료 뒤 descendant를 모두 reap한다. 이 filesystem·process 격리를 강제할 수 없으면 검증을 시작하지 않는다.

다음 항목은 오류로 취급한다.

* 누락된 타입
* `Any`
* `Unknown`
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
| statically concrete function `F32` exact type·ABI normalization | 항상 | 항상 | 항상 |
| newtype 생성자의 carrier 명목·scalar·중첩 ABI, `F32` normalization과 refinement | 항상 | 항상 | 항상 |
| 미선언 `Exception` → `CottContractViolation` | 항상 | 항상 | 항상 |
| `Never` 정상 반환과 `SystemExit` 재전파 조건 | 항상 | 항상 | 항상 |
| 그 밖의 function 경계 구체화 타입·숫자 범위 | 신뢰 선언 | 런타임 검사 | test context에서 검사 |
| `requires`, 허용 error variant, `ensures` | 신뢰 선언 | 런타임 검사 | test context에서 검사 |
| 지워진 `TypeVar` 관계 | 정적 검사 | 정적 검사 | 정적 검사 |

wrapper order는 고정한다: statically concrete argument `F32` ABI normalization → 활성 mode의 concrete input type·numeric range·refinement, 모든 `requires`와 첫 true conditional `error` 기록 → implementation call → return `F32` ABI normalization → 활성 mode의 concrete return type·numeric range, allowed `Err` set·기록된 conditional error 의무와 모든 applicable `ensures`. 실패하면 해당 type 또는 clause span을 가진 `CottContractViolation`이다.

facade의 always-on ABI pass는 expected type에서 statically concrete `F32` path만 recursive traversal한다. 값이 반올림되면 같은 immutable cott carrier를 다시 만들며 raw Python container를 convert하지 않는다. 이 path의 shape mismatch는 `off`에서도 ABI violation이고 erased `TypeVar` 내부는 static-only다. 이와 별도로 newtype 생성자는 6.2의 carrier ABI와 refinement를 항상 재귀 검사한다.

validator는 alias를 해소하고 cott_runtime nominal class, struct·enum field, container element와 newtype refinement를 재귀 검사한다. trait는 7장의 member-presence 수준, erased TypeVar는 static-only다. `Never` 값은 항상 실패하고 `Opaque`는 wrapper identity와 literal tag를 확인한다.

`test-only` context는 cott 계약 테스트 실행기만 활성화하며 일반 환경 변수로 켤 수 없다. MVP는 구현 내부 호출 지점을 계측하지 않는다.

`runtime_validation` 값은 emit 시 facade·wrapper bytes에 compile-time specialize되어 managed file hash에 포함된다. 설치된 runtime은 `cott.toml`, `generation.json`이나 environment에서 mode를 다시 읽지 않는다. `test-only`의 optional check는 계약 test runner가 만든 test context에서만 활성화되고 일반 호출에서는 `off`와 같으며, 그 context는 public API나 환경 변수로 만들 수 없다.

#### 16.4.1 검증 보증 등급

`cott verify`는 모든 계약 항목을 같은 수준으로 검증했다고 표현하지 않는다.

| 등급 | 의미 | MVP 예시 |
| --- | --- | --- |
| 정적 증명 | 실행 없이 결정적으로 검사 | 공개 symbol, signature, concrete type 구조, 숫자 metadata, trait·generic 관계, 계약 표현식 타입 |
| 런타임 검사 | 실제 production mode의 실행 경계에서 검사 | 구체화된 중첩 값, `requires`, refinement, 허용 error variant, `ensures` |
| 테스트 관찰 | deterministic하게 생성한 유효 사례에서 확인 | 순수 함수의 조건부 `error`와 `ensures` |
| 미관찰 | 유효한 사례를 만들지 못해 실행 증거 없음 | 만족 가능한 입력을 생성하지 못한 절 |
| 신뢰 선언 | MVP가 일반적으로 증명할 수 없음 | 숨은 부작용, off mode 검사, effectful 함수의 실행 조건, archive-to-install dependency provenance |

자동 test input은 모든 refinement와 `requires`를 만족해야 한다. generator는 IR hash를 seed로 경계값 우선 64개 candidate를 만들고 container 길이 0–3, enum variant와 recursive `JsonValue` 깊이 4로 제한한다. `requires`를 통과한 case만 실행하며 위반 candidate는 폐기한다. 미구체화 function `TypeVar`·trait·`Opaque` 입력이나 유효 case를 만들지 못한 절은 `미관찰`이다.

자동 계약 테스트는 `effects`가 없고 반환 type이 `Never`가 아닌 함수만 함수별 별도 CPython process의 deny-by-default OS sandbox에서 실행한다. `Never` 함수는 자동 호출하지 않고 clause별 `미관찰` reason을 기록한다. sandbox를 구현 코드 import 전에 적용하고 read는 staging generated root·exact interpreter standard library·locked distribution과 dynamic-loader runtime으로 제한한다. filesystem write는 폐기할 process-private scratch만 허용하고 network, device, subprocess와 environment secret은 차단한다. `PYTHONDONTWRITEBYTECODE=1`, fixed `PYTHONHASHSEED`와 scratch `TMPDIR`을 사용하며 stdout·stderr는 pipe로 수집한다. process tree wall timeout은 30초, stream별 보존 한도는 1 MiB다. timeout·비정상 종료·한도 초과는 verify 실패이며 sandbox를 강제할 수 없는 platform에서도 실패한다. effectful 함수는 자동 실행하지 않고 `신뢰 선언`으로 보고한다.

contract test runner는 candidate마다 staged facade symbol을 loader·wrapper 경로로 호출한 뒤 같은 typed IR evaluator로 `requires`, 반환 type, conditional `error`와 `ensures`를 독립 판정한다. `test-only` project에서는 runner만 test context를 활성화하고, 다른 configured production mode도 바꾸지 않는다. 따라서 `off`도 실제 facade를 통과해 실행된 pure case의 테스트 관찰 evidence를 얻지만 설치된 facade의 optional production check가 활성화되었다고 보고하지 않는다. facade를 통과하지 않은 실행은 테스트 관찰로 기록하지 않는다.

verification report는 contract symbol과 source-order clause ID마다 `{symbol, clause_id, span, evidence: [{grade, mode, valid_cases, reason}]}`를 기록한다. runtime capability, static result와 실제 test 실행은 별도 evidence entry이고 단일 최고 등급으로 합치지 않는다. 0 case를 테스트 관찰로 승격하지 않는다.

`CottContractViolation`은 `Exception`의 하위 타입이며 `cott_runtime`에서 import한다. `symbol`, `phase`, clause `span`, expected·actual summary와 original `Exception` cause를 보존한다. verified loader의 identity·origin·hash preflight 실패도 target 호출 전에 `phase = "provenance"`인 이 exception으로 발생한다. facade의 동일한 exception boundary는 lazy load·symbol lookup과 implementation invocation 전체를 감싼다. loader가 이미 만든 `CottContractViolation`을 포함한 기존 contract violation은 재포장하지 않고, module compile·execute·import·symbol lookup의 `Exception`은 cause를 보존한 `phase = "implementation-load"` 위반으로, implementation이 새로 발생시킨 `Exception`은 invocation 위반으로 변환한다. `SystemExit`은 load 또는 invocation 중 반환 type이 `Never`이고 `process.exit`가 선언된 경우만 재전파하며 그 외에는 contract violation이다. 다른 `BaseException`은 포획하지 않는다. `Never` implementation이 정상 반환하면 위반이다. 어떤 exception도 cott `Result` error로 자동 변환하지 않는다.

진단과 JSON 검증 결과에는 구성된 mode에서 각 계약 항목이 실제로 얻은 보증 등급을 포함한다.

---

### 16.5 기존 구현 바인딩

라이브러리를 구현 내부에서만 사용한다면 cott에 등록하지 않는다. Python 구현에서 일반적으로 import하고 package와 version은 `pyproject.toml` 및 기존 lockfile로 관리한다.

기존 Python 함수가 cott 함수를 직접 구현할 때만 대상별 binding을 선언한다.

```toml
[target.python.implementations]
"foo.data.load_payload" = "my_project.adapters.provider:load_payload"
```

키는 cott 함수의 완전한 이름이고 값은 Python `module:function_name`이다.

#### 16.5.1 바인딩 해석과 시그니처 호환성

manifest에 binding key가 있으면 해석 실패는 hard error다. 잘못된 binding을 미구현 함수나 agent 생성으로 대체하지 않는다.

manifest binding key는 현재 IR의 public function을 정확히 가리켜야 하며 stale·duplicate key는 configuration error다.

`cott check`, `cott emit`, `cott generate`, `cott verify`는 Python source와 stub을 import 없이 정적으로 해석한다. 타입 판정은 이번 transaction에서 staging에 생성한 `*_types.py`를 기준으로 한다.

MVP target은 regular `.py`에 선언된 decorator 없는 top-level synchronous function과 simple function name으로 제한한다. target의 coroutine, generator, overload, variadic parameter와 descriptor, extension·zip·custom loader는 거부한다. helper와 아래 허용된 module initialization은 implementation bytes의 일부지만 선언된 effect를 증명한다고 보지 않는다.

module top-level node는 optional docstring, `from __future__ import annotations`, absolute import, invariant `TypeVar` 선언, literal로 초기화한 `Final[bool | int | float | str | bytes]`와 undecorated synchronous function definition만 허용한다. class·type alias 정의는 거부한다. 모든 helper signature도 concrete하게 typed되어야 하며 function body의 nested import·`global`·`nonlocal`과 그 밖의 executable top-level statement는 거부한다.

target과 helper에서 optional docstring을 제외한 body가 `pass` 또는 `...`뿐인 placeholder와 `NotImplementedError`를 직접 발생시키는 코드는 정적 해석 단계에서 거부한다. 이 규칙은 `.pyi` stub의 ellipsis에는 적용하지 않는다.

static verifier는 module 전체 AST의 import를 수집한다. generated `cott_runtime`·`*_types`, CPython standard library와 lockfile에 고정된 external distribution만 허용한다. star import, relative import, 다른 project-local module, `importlib`·`__import__` 등 dynamic import, `eval`·`exec`·`compile`, `builtins`·`__builtins__` reflection과 `__file__`·`__path__`·`__spec__`·`__loader__`·`__package__` 의존은 거부한다. local helper는 같은 file에 두고 복잡한 library API는 최소 typed adapter로 감싼다.

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

cott 함수 매개변수에는 기본값이 없다. 기본값이 필요한 API는 options struct field로 표현한다. 추가 선택 인자를 받거나 `Any`·`Unknown`이 유입되는 함수는 직접 binding하지 않는다. 선언된 `effects`는 16.4.1의 신뢰 선언이다.

binding된 함수는 agent 생성 대상에서 제외한다. 나머지 각 함수는 별도 파일에 구현한다.

```text
foo.bar.process_bar
→ <target.python.source>/_cott_impl/foo/bar/process_bar.py
→ _cott_impl.foo.bar.process_bar:process_bar
```

function implementation resolution priority는 manifest binding → 위 exact agent file → unresolved다. compatible agent file이 이미 있으면 재사용하고 agent를 호출하지 않는다. selected generate에서 agent file이 없거나 signature가 현재 contract와 불일치하면 regeneration candidate로 staged overwrite할 수 있다. binding 불일치는 항상 hard error며 agent로 대체하지 않는다.

compiler가 필요한 `_cott_impl/**/__init__.py`를 side-effect 없는 빈 파일로 생성한다. agent는 선택 함수 파일만 쓰고 helper도 그 파일 안에 둔다.

binding target은 공개 facade와 달라야 한다. 외부 API가 계약과 다르면 사용자가 typed adapter를 작성한다. cott는 인자·예외 변환을 추측하지 않는다.

MVP binding target은 `target.python.source` 아래 module로 제한하고 project 밖 function을 직접 binding하지 않는다. external library API는 project-local typed adapter가 import하며 16.1의 dependency provenance 규칙을 적용한다.

MVP binding 대상은 함수로 제한한다. 외부 struct와 enum은 cott 타입으로 변환하고 외부 객체가 계약 경계를 통과해야 하면 12.5의 `Opaque` 규칙을 따른다.

---

### 16.6 공개 facade와 구현 경계

호출자는 구현 위치와 관계없이 항상 cott module 경로를 사용한다.

```python
from foo.bar import process_bar
```

cott는 `generated/python/foo/bar.py`에 fully typed wrapper를 생성한다. `bar_types.py`가 module 고유 type identity의 원본이고 standard ABI identity는 `cott_runtime`에 있다. implementation과 adapter는 custom type을 type module에서, standard type을 `cott_runtime`에서 import하며 facade를 import하지 않는다.

각 wrapper에는 project identity·expected `cott_runtime` ABI version, compile-time specialized `runtime_validation`, implementation의 canonical module·symbol, `generated/python` relative `runtime_origin`·content hash, exact CPython full version·cache tag·OS family·architecture와 16.1의 external dependency record를 immutable constant로 embed한다. full `sysconfig` platform string은 generation provenance에만 둔다. durable `source_origin`은 `generation.json`에만 남고 verify가 generated copy와 byte identity를 확인한다. installed package에 project-side record가 없어도 검사는 동작한다.

`cott_runtime` verified loader는 먼저 facade와 runtime의 project identity·ABI version 및 embedded CPython full version·cache tag·OS family·architecture가 현재 runtime과 같은지 확인하며 OS point version은 비교하지 않는다. CPython patch version mismatch도 거부하며 16장의 재생성·재검증이 필요하다. 그 뒤 ordinary import보다 먼저 자신의 package 위치에서 generated root를 정하고 embedded `runtime_origin`을 no-follow로 열어 exact bytes의 hash를 검사한다. 성공하면 canonical module name으로 단 하나의 module object를 만들고 실행 전에 `sys.modules`에 등록한 뒤 검증한 bytes 자체를 compile·execute한다. 실패하면 등록을 되돌린다.

이미 같은 canonical name이 `sys.modules`에 있으면 cott loader registry가 동일 object·origin·hash를 앞서 검증한 경우에만 재사용하고, 일반 import로 먼저 실행된 module은 거부한다. process-global registry와 load transition은 canonical name별 reentrant lock으로 보호해 concurrent caller가 같은 module object 또는 같은 실패를 관찰하게 한다. 구현 module 직접 import는 지원 API가 아니다. custom loader, relative import 또는 실행이 필요한 parent `__init__.py`는 MVP에서 거부한다. compiler-owned empty parent package만 만들며 검증된 symbol을 cache한다.

loader는 target 실행 전에 recorded direct external module의 distribution identity·version·regular module-relative origin·content hash를 import 없이 확인하고, 이미 load된 module의 `__file__` origin이 다르면 실패한다. 이 preflight는 preloaded module이 과거에 같은 bytes로 실행됐거나 distribution의 transitive file·standard library 전체가 변조되지 않았음을 증명하지 않는다. external execution은 lockfile packaging과 exact CPython installation에 대한 신뢰 선언으로 보고한다.

`runtime_validation`은 16.4 표의 항목만 제어하며 provenance loader를 끄거나 직접 implementation re-export로 바꾸지 않는다. 구현 위치와 mode가 달라도 facade callable의 signature와 module identity는 같다.

`target.python.source`는 compiler input과 durable implementation root일 뿐 runtime import path가 아니다. 이 root에는 cott public module, compiler-owned `*_types` 또는 `cott_runtime`을 정의할 수 없다. runtime·BasedPyright는 generated root 뒤에 standard library와 locked distribution만 사용하고 stub root는 runtime path에서 제외한다. Python build는 모든 local runtime file을 generated root에서만 포함한다. 설치된 wheel 전체의 독립 검증은 v1.0 범위지만 embedded provenance check는 MVP package에서도 필수다.

구현이 해석된 함수만 facade와 `__all__`에 포함한다. 미구현 함수에는 placeholder를 만들지 않고 `current.unresolved`에 기록한다. `cott verify`는 unresolved가 하나라도 있거나 verified facade projection이 전체 IR과 다르면 실패한다.

---

## 17. 에이전트 코드 생성 흐름

### 17.1 생성 입력

선택된 에이전트에게 전달되는 정보는 다음과 같다.

1. Canonical IR
2. 원본 `doc`
3. 사전 조건
4. 사후 조건
5. 오류 조건
6. 부작용
7. 생성 대상 언어 규칙
8. 프로젝트 코딩 규칙
9. 관련 타입 선언
10. 기존 구현 파일
11. 구현 바인딩과 바인딩된 심볼 목록
12. 읽기 전용인 프로젝트 내부 바인딩 파일

### 17.2 에이전트 선택 및 호출

`cott generate`는 미구현 함수를 생성할 때 사용자가 `--agent`로 지정한 에이전트를 사용한다. cott는 모델 제공자 API를 직접 호출하거나 에이전트를 자동 선택하지 않는다.

MVP는 다음 두 가지 에이전트와 각 에이전트가 제공하는 CLI 인터페이스만 지원한다.

| `--agent` 값 | 호출 인터페이스 |
| ------------- | --------------- |
| `codex`       | `codex exec`    |
| `omp`         | `omp -p`        |

cott는 17.1의 입력을 하나의 구현 지시로 구성하여 선택된 인터페이스에 전달한다. 구현 지시에는 최소한 다음 내용을 명시한다.

> 이 계약에 따라 대상 언어 코드를 구현하라. `.cott` 파일과 읽기 전용 바인딩 파일은 수정하지 말고, 바인딩된 심볼을 다시 구현하지 마라.

지원하지 않는 `--agent` 값은 에이전트를 호출하기 전에 오류로 거부한다.

#### 17.2.1 에이전트 실행 계약

선택 범위의 미구현 함수마다 fully qualified symbol 정렬 순서로 agent process 하나를 실행한다. 각 process의 유일한 implementation write target은 해당 함수 file이며 어떤 run이라도 실패하면 전체 generate transaction을 폐기한다. `agent_runs`에는 함수별 record를 source order가 아니라 이 실행 순서로 남긴다.

각 에이전트 adapter는 실행 파일, prompt 전달 방식, 작업 디렉터리, 환경 변수, 종료 상태를 명시한다.

compiler release마다 adapter별 exact supported CLI version과 exact argv template를 고정한다. v0.1은 Codex CLI `0.147.0`, OMP `17.2.12`만 허용한다. executable은 `PATH`에서 한 번 resolve하고 version probe부터 아래와 같은 containment에서 실행한다. version output이 정확히 일치하지 않거나 해석 불가능하면 본 실행 전에 실패한다.

v0.1의 exact main-process argv template는 다음과 같다. 각 항목은 shell 재해석 없이 별도 argv다. `<workspace>`·`<scratch>/omp.yaml`·`<seconds>`와 `<prompt>`만 run별 값으로 치환한다.

* Codex: `codex exec --strict-config --ephemeral --ignore-user-config --ignore-rules --skip-git-repo-check --sandbox workspace-write --color never --cd <workspace> -`; prompt bytes는 stdin으로 전달한다.
* OMP: `omp -p --cwd <workspace> --no-session --no-rules --no-skills --no-extensions --no-lsp --no-pty --no-title --tools read,grep,glob,edit,write --approval-mode yolo --max-time <seconds>s --config <scratch>/omp.yaml <prompt>`; prompt는 마지막 단일 argv다.

공통 environment name은 `HOME`, `PATH`, `PYTHONDONTWRITEBYTECODE`, `TMPDIR`이며 host에 존재할 때만 `SSL_CERT_FILE`, `SSL_CERT_DIR`, `HTTPS_PROXY`, `HTTP_PROXY`, `NO_PROXY`를 추가한다. Codex는 존재하는 `CODEX_API_KEY`, `CODEX_ACCESS_TOKEN`, `CODEX_HOME`만, OMP는 존재하는 `PI_CODING_AGENT_DIR`만 추가한다. 그 밖의 host environment는 전달하지 않는다.

* shell을 사용하지 않고 executable과 각 인자를 분리하여 실행한다.
* 실행 전에 executable의 canonical regular-file path, version과 content hash를 기록한다.
* 작업 디렉터리는 17.4의 격리된 staging workspace다.
* 실제 project root는 agent sandbox namespace에서 보이지 않는다. 필요한 계약·binding·rule·기존 구현은 staging의 read-only copy로만 제공하고 현재 implementation file과 별도 scratch directory만 쓸 수 있다. adapter executable·runtime library와 adapter별 credential path만 project 밖에서 read-only로 열며, 이 sandbox를 강제할 수 없는 platform에서는 agent generate를 거부한다.
* prompt는 adapter가 지원하는 stdin 또는 단일 argv 값으로 전달하며 shell 문자열로 조합하지 않는다. 운영체제 인자 크기 한도를 넘으면 실행 전에 오류로 거부한다.
* 환경 변수는 compiler version에 고정된 adapter별 name allowlist만 전달한다. secret value는 기록하지 않고 전달한 name만 기록한다.
* `PYTHONDONTWRITEBYTECODE=1`을 설정하고 `TMPDIR`, type checker·test cache와 agent 임시 상태를 scratch directory로 보낸다.
* `[generator].timeout_seconds`는 1–3600이며 default는 900이다. 모든 agent child는 compiler-owned process containment에 넣는다. parent가 정상 종료해도 남은 descendant를 전부 종료·reap하고 containment가 비었음을 확인한 뒤에만 candidate path를 staging workspace handle 기준 `O_NOFOLLOW`로 열어 regular file·`st_nlink == 1`인지 `fstat`으로 확인하고 읽는다. 그 밖의 file kind, 사용자 취소·timeout·비정상 종료나 descendant 정리 실패는 transaction을 폐기한다.
* containment에는 compiler version이 고정한 process·CPU·memory·open-file·writable-byte ceiling을 적용하고 candidate implementation file은 최대 1 MiB로 제한한다. 어떤 ceiling이라도 넘으면 agent 실패다.
* stdout·stderr는 끝까지 drain하며 전체 byte count·SHA-256와 truncation 여부를 계산하고 사용자에게 stream별 최대 1 MiB만 보여 준다. generation record에는 raw output을 넣지 않고 이 metadata, exit code, 실행 시간, adapter·executable path·version·content hash·prompt hash만 남긴다.

에이전트가 0이 아닌 상태로 종료되거나 timeout되면 staging과 scratch 변경을 폐기한다. stdout의 code block은 구현으로 채택하지 않으며 허용된 implementation file의 최종 bytes만 후보 입력이다. 0으로 종료해도 target symbol이 없거나 file이 바뀌지 않아 unresolved면 실패한다.

### 17.3 에이전트가 변경할 수 없는 요소

에이전트는 다음 요소를 임의로 변경할 수 없다.

* 함수명
* 매개변수명
* 매개변수 타입
* 반환 타입
* 오류 타입
* 공개 구조체 필드
* enum variant
* 선언된 효과

계약 변경이 필요하면 `.cott` 파일을 수정하지 않고 변경 필요성을 결과로 보고해야 한다.

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

staging에는 계약, binding, rule, 기존 구현과 compiler 생성물의 사본을 제공하고 실제 project path는 agent에게 노출하지 않는다. 각 agent process의 workspace write allowlist는 현재 함수 file 하나로 제한한다.

```text
<target.python.source>/_cott_impl/<module path>/<function>.py
```

helper는 같은 함수 파일 안에 둔다. 필요한 `_cott_impl/**/__init__.py`, facade, type module, stub, IR, docs, generated tests와 provenance는 compiler만 쓴다. 같은 파일을 binding과 agent 생성 대상으로 함께 쓰는 구성은 거부한다.

scratch는 workspace diff 대상이 아니며 실행 뒤 폐기한다. agent 실행 후 staging 전체 file list와 diff를 검사한다. `.cott`, manifest, binding, compiler 생성물, 비선택 구현 또는 allowlist 밖 변경은 실패다. agent가 workspace에 만든 cache·temporary file도 위반이다.

compiler-owned 관리 집합은 `<target.python.generated>`, `<target.python.stubs>`, `<artifact-root>/ir`, `<artifact-root>/docs`, `tests/generated`와 compiler-owned `<target.python.source>/_cott_impl/**/__init__.py`의 합집합이며, generation record는 `<artifact-root>/generation.json`이다. stale 삭제는 현재 command의 ownership 안에서만 수행한다. `emit ir`은 `<artifact-root>/ir`만, `emit python`과 `generate`는 전체 관리 집합을 소유하며 verify는 전체 집합을 재생성해 비교하되 반영하지 않는다.

성공적으로 project source에 승격된 agent 함수 파일은 비결정적이지만 durable implementation source로 취급하며 cott가 자동 삭제하지 않는다. IR에서 더 이상 참조하지 않는 파일은 `cott diff`의 `IMPLEMENTATION STALE`로 보고하되 public facade나 verify 대상에는 포함하지 않는다. 사용자가 명시적으로 삭제한다.

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
이번 세대 type module을 기준으로 binding 정적 해석
  ↓
선택된 미구현 함수가 있으면 지정 agent 호출
  ↓
workspace allowlist 및 비선택 구현 불변 검사
  ↓
agent 이후 구현 symbol·source origin·content hash와 external import record 재계산
  ↓
local implementation을 canonical module path의 generated runtime copy로 복사
  ↓
embedded runtime provenance를 가진 facade와 staging `current` snapshot 생성
  ↓
public Python symbol projection과 compiler 관리 집합 검사
  ↓
BasedPyright, verified loader, mode별 wrapper와 생성된 순수 계약 테스트
  ↓
실제 project file list·입력 hash와 tool·direct dependency provenance 재확인
  ↓
emit·generate는 durable journal로 generation.json을 마지막에 포함해 반영; verify는 expected managed bytes 일치 확인 후 generation.json만 반영
  ↓
project lock 해제
```

staging facade는 embedded identity·runtime origin·hash를 generated copy에서 검사하며 `current.verified` bit를 요구하지 않는다. full verify 성공 시 `current`와 `last_verified`를 같은 snapshot으로 기록하고, emit·generate는 `last_verified`를 보존한다.

full verify에는 agent 선택 범위가 없고 agent를 호출하지 않는다. staging에서 재생성한 managed set과 actual project set이 정확히 같아야 하며 검증 record 외 차이는 폐기한다.

binding을 해석하지 못하거나 그 external import에 필요한 lock entry가 없으면 agent 호출 전에 실패한다. agent 결과의 external import는 호출 직후 같은 규칙으로 검사한다. clean checkout에서도 이번 세대 type module을 먼저 만들므로 이전 generated file에 의존하지 않는다.

특정 함수 generate에서 agent가 바꿀 수 있는 durable source는 선택된 함수별 implementation file뿐이지만 compiler-owned 관리 집합은 항상 전부 재생성·반영한다. `last_verified`가 있으면 그 baseline에 존재한 비선택 declaration의 canonical `contract_surface` record는 byte-identical해야 하고 비선택 public symbol은 현재 `public_python_symbols`에도 남아야 한다. 새 declaration 추가는 허용한다. 최초 검증 전 `last_verified = null`이면 이 guard 없이 선택 범위를 생성하고 `current.verified = false`로 기록한다.

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

scaffold는 `python/.python-version`에 `3.14`를 쓰고 `python/pyproject.toml`의 `requires-python`을 `>=3.14,<3.15`로 고정하며 BasedPyright `1.39.9`를 dev dependency로 pin한다. v0.1은 CPython `3.14.6`과 uv `0.12.3`만 지원하며, init은 정확히 그 managed CPython patch를 설치·probe한다. `uv.lock`은 Python exact patch를 고정하지 않으며, 실제 설치된 full patch는 이후 generation provenance에 고정한다.

uv executable은 shell 없이 PATH에서 한 번만 canonical regular file로 resolve하고 version `0.12.3`인지 검사한다. uv subprocess environment는 empty base에서 compiler-fixed sanitized `PATH`와 허용한 `HOME`·temporary-directory·platform TLS/certificate 변수만 복사하고 inherited `UV_*`, `VIRTUAL_ENV`, `CONDA_PREFIX`는 전부 제외한 뒤 `UV_PYTHON`·`UV_PROJECT_ENVIRONMENT`만 해당 단계에 명시하며 canonical uv를 `--no-config`로 실행한다. `<uv> --no-config python dir`의 canonical managed-install root를 기록한 뒤 다음 순서로 실행한다: `<uv> --no-config python install --upgrade 3.14`; `<uv> --no-config python find --managed-python --system 3.14`가 반환한 canonical path가 그 root 아래인지 확인하고 해당 interpreter를 `-I -c <compiler-fixed-identity-probe>`로 실행해 CPython `3.14.6`을 검증; project cwd `python/`에서 lock, sync 순서를 수행한다.

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

이 명령은 agent 없이 compiler-owned 산출물을 staging에서 만들고 원자 갱신한다. 미구현 함수는 facade에서 생략하고 `current.unresolved`에 기록한다. `current.verified = false`로 갱신하지만 `last_verified`와 durable agent implementation file은 보존한다. emitter 자체가 성공하면 exit 0이지만 배포 가능한 결과는 아니다.

### 18.6 구현 생성

```bash
cott generate --agent codex --target python
cott generate foo.bar.process_bar --agent omp --target python
```

선택 범위에 미구현 함수가 있으면 `--agent`가 필수다. 허용 값은 `codex`, `omp`다. 모든 선택 함수가 binding되어 있으면 agent를 호출하지 않는다.
특정 함수 generate에서 agent write 대상은 그 함수별 file뿐이며 apply는 선택 implementation과 전체 compiler-owned 관리 집합을 함께 갱신한다. verified baseline guard는 17.5의 정확한 규칙을 사용한다. 최초 검증 전에는 선택 범위 성공만으로 진행할 수 있다. 결과는 `current.verified = false`며 project 전체 미구현 상태를 별도 진단한다. 배포 gate는 항상 full `cott verify`다.

### 18.7 구현 검증

```bash
cott verify
```

검증 범위:

* 공개 function signature와 `public_python_symbols(IR)` projection
* custom enum union·variant class, public const와 module type 구조
* 숫자 ABI metadata, 명목 container invariance와 structural trait bound
* facade와 tool-only stub의 독립적인 Canonical IR 일치
* BasedPyright strict 결과
* deterministic하게 생성된 순수 함수 계약 테스트
* 미관찰 사례의 정확한 등급 강하
* unresolved 구현과 compiler-owned stale module·symbol
* stale durable implementation 진단
* binding·agent source의 정적 signature와 generated copy의 verified-loader runtime signature
* facade, type module, source/runtime implementation origin·content hash와 copy byte identity
* 모든 external import의 selected lock entry, installed distribution identity·version·metadata·origin·content hash와 archive-to-install 신뢰 등급
* configured mode의 `requires`, concrete 반환 타입, 허용 error variant와 `ensures`
* `Opaque` HIR boundary와 reserved target path
* staging allowlist, filesystem·effect sandbox와 transaction recovery
* 현재 hash, `current`와 `last_verified` provenance

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

public declaration 제거·rename, signature·generic·type shape·variant·field·default·constant·refinement·contract clause·effect의 변경은 conservative하게 breaking이다. 새 top-level type·function·constant만 기존 target symbol과 충돌하지 않을 때 non-breaking이다. doc만 바뀌면 `DOCUMENTATION`으로 보고한다. MVP는 logical implication으로 조건 완화 여부를 추측하지 않는다.

`cott diff`는 `generation_id` mismatch 자체를 change로 보지 않는다. 같은 target environment에서는 compiler·runtime·Python·type-checker identity와 managed artifact hash까지 비교한다. target identity가 다른 cross-machine 비교에서는 이 machine-local 항목을 변경 판정에서 제외하고 normalized contract·public symbol, durable implementation content와 normalized lock·dependency identity를 비교한다.

MVP는 generation result cache를 두지 않고 emit·generate 때마다 target을 결정적으로 다시 만든다. `generation_id`를 구성하는 contract·manifest·rule·target metadata·lock raw hash, compiler·runtime·Python·type-checker identity, implementation identity·source/runtime origin·content hash 중 하나라도 달라지면 새 세대다. `cott verify`도 항상 모든 검사를 실행한다.

### 18.9 Exit code

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

[target.python.implementations]
"foo.data.load_payload" = "my_project.adapters.provider:load_payload"

[generator]
rules = "AGENTS.md"
timeout_seconds = 900
```

MVP manifest schema는 닫혀 있고 Python target 하나만 허용한다. `[effects]`와 `[target.python.implementations]`의 동적 key 외 unknown table·field는 configuration error다.

`[project]`의 `name`·`version`·`source`와 `[target.python]`의 `source`·`generated`·`stubs`·`interpreter`·`type_checker`·`runtime_validation`은 필수다. `lockfile`은 아래 dependency 규칙의 조건부 필드이고 `[effects]`, `[target.python.implementations]`, `[generator]`는 선택이다. `[generator]`가 없으면 `timeout_seconds = 900`이고 project coding rule은 없으며, 있으면 `rules`는 선택적인 project-relative regular file이고 `timeout_seconds`는 선택적인 1–3600 정수다.

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

### 22.1 MVP에 포함

* `.cott` parsing, injective module mapping, prelude와 `use`
* 고정 폭 숫자, `Path`, `Unit`, `Never`, `JsonValue`, `Opaque["tag"]`
* `alias`, refinement를 항상 검사하는 `newtype`
* immutable `struct`, payload enum과 method-signature structural `trait`
* invariant generic, 복수 structural trait bound와 `Tuple[T1, T2]`
* `Option`, `Result`와 고정 Python runtime identity
* 본문·기본 매개변수 없는 function declaration
* 닫힌 순수 계약 표현식, typed pattern, ordered `error`, `effects`
* 이름·타입·상수 해석과 source span을 가진 Canonical IR
* `cott_runtime`, Python facade, type module, tool-only `.pyi`, docs와 IR 생성
* `public_python_symbols(IR)` 및 BasedPyright strict 검증
* refinement·`requires`를 만족하는 pure function 계약 테스트
* effectful 함수 자동 실행 제외와 정확한 trust 등급
* `off`, `boundary`, `test-only` mode와 항목별 보증 등급
* compiler source에서 정적으로 해석하고 generated runtime copy로 고정하는 project-local plain top-level Python binding
* single-identity verified loader와 embedded implementation provenance
* user-selected Codex CLI 또는 OMP CLI를 통한 함수별 구현 생성
* compiler stale file 자동 삭제와 stale durable implementation 진단
* `current`·`last_verified` snapshot과 contract/implementation diff
* formatter, stable CLI exit code와 JSON diagnostics
* `cott init <path> [--name <name>] [--no-sync]` minimal scaffold와 exact template
* uv에 위임한 CPython 3.14 최신 patch managed install, lock 생성과 기본 frozen sync

### 22.2 MVP에서 제외

* `.cott` 실행 본문과 parameter default
* trait implementation, nominal conformance, default method와 runtime dispatch
* ownership, borrow checker와 lifetime
* const generic, variadic tuple과 연관 타입
* recursive user type
* trait specialization과 subtyping variance
* 비동기 Python binding과 비동기 type system
* SMT 기반 정적 계약 증명
* 일반 Python call graph의 effect 전파 검사
* implementation 사이 project-local import와 cott facade chaining
* mutable 호출 전 snapshot과 `old()`
* 자동 refactoring, adapter와 exception conversion 생성
* 다중 target language와 완전한 IDE plugin
* 한 Python environment에 여러 generated cott distribution 설치
* external struct·enum 직접 binding
* extension·zip·dynamic Python implementation binding
* `cott init`의 제한된 uv 위임을 제외한 cott 내장 dependency resolver·package manager와 일반 dependency 설치
* live Python reader의 transaction snapshot isolation
* 설치된 wheel 전체의 독립적인 origin 검증

---

## 23. MVP 완료 기준

MVP는 다음 조건을 모두 자동 검증할 때 완료다.

1. 14장 예시를 clean checkout에서 parse, emit, generate, verify할 수 있다.
2. module path가 injective하고 reserved prelude·target path 충돌이 emit 전에 실패한다.
3. syntax, name, type와 contract 오류가 정확한 source span을 가진다.
4. 모든 declaration·type·contract clause와 pattern이 normative schema를 통과하는 typed IR node며 ambient name과 불법 expression을 거부한다.
5. conditional `error` priority와 error list의 allowed variant exhaustiveness를 source order에서 결정적으로 보존한다.
6. public constant가 IR, type module, facade, stub과 diff에 동일하게 나타난다.
7. facade와 stub을 각각 `public_python_symbols(IR)`과 비교하고 모든 generated·implementation code가 `Any`·`Unknown` 없는 compiler-owned BasedPyright strict 검사를 통과한다.
8. project identity가 일치하는 `cott_runtime` 하나만 표준 union, container, numeric metadata와 contract exception identity를 소유한다.
9. statically concrete `F32` binary32 normalization을 모든 mode에서, integer range를 검사가 활성화된 ABI boundary에서 보존한다.
10. `Path`, `Unit`, `Never`, `JsonValue`, `Opaque`, struct, enum, newtype와 pair tuple ABI를 보존한다.
11. generic invariance와 복수 structural trait bound를 static verifier와 BasedPyright에서 유지한다.
12. newtype constructor는 모든 mode에서 carrier ABI와 refinement를 재귀 검사하고 raw Python container를 받지 않는다.
13. boundary mode는 concrete nested value, `requires`, allowed error variant와 `ensures`를 검사한다.
14. off·test-only mode는 16.4 표보다 강한 보증을 보고하지 않는다.
15. 자동 test input은 refinement·`requires`를 만족하고 생성 실패 절을 `미관찰`로 보고한다.
16. pure test는 deny-by-default OS sandbox에서만 실행하고 effectful function과 `Never` 반환 function은 자동 실행하지 않는다.
17. cott binding을 이번 staged type module에 대해 import 없이 해석하고 unsupported Python shape를 거부한다.
18. 모든 implementation external import는 frozen production dependency closure의 selected lock hash, installed distribution identity·version·metadata·origin·content hash 없이는 실패하며 archive-to-install 연결의 신뢰 등급을 정직하게 보고한다.
19. local implementation은 generated runtime copy로 고정하고 verified loader가 그 exact bytes를 실행 전 검증한다.
20. implementation signature, numeric metadata, source/runtime origin, copy byte identity와 content drift를 탐지한다.
21. agent는 user-selected supported CLI만 shell 없이 함수별 process와 단일-file write sandbox에서 실행한다.
22. 선택 function file 외 project·contract·manifest·binding·non-selected implementation 변경을 막는다.
23. 최초 partial generate와 verified-baseline partial generate 규칙을 구분하고 baseline declaration의 비선택 surface를 보존하되 새 declaration 추가를 허용하며 항상 `current.verified = false`로 남긴다.
24. unresolved function이나 incomplete public projection이 full verify를 실패시킨다.
25. successful full verify만 동일한 current snapshot을 `last_verified`로 승격한다.
26. `cott diff` 기본 baseline은 `last_verified`이며 contract, implementation과 stale implementation을 구분한다.
27. semantic·implementation input drift가 `generation_id`를 바꾸고 target을 다시 emit하며 verify는 전부 재실행된다.
28. stale compiler output은 삭제하지만 durable agent source는 자동 삭제하지 않는다.
29. crash injection을 journal state publish와 각 post-image fsync·rename·delete·commit, rollback restore·fsync·journal cleanup의 재중단 단계에 수행해 반복된 다음 lock acquisition마다 old 또는 new complete snapshot으로 복구한다.
30. CLI는 format mismatch를 포함해 18.9의 stable exit code를 반환한다.
31. 배포 gate는 full `cott verify`와 transaction 뒤 시작된 새 Python process만 허용한다.
32. formatter는 21장의 canonical format, parse-error no-write, 두 번 format의 byte-identical idempotence와 raw-byte `--check`를 검증한다.
33. JSON diagnostic은 20장의 closed schema, 안정 정렬, 단일 object·끝 newline과 human prose·색상 없는 출력을 검증한다.
34. `cott init`은 absent target만 허용하고 exact scaffold·template, supported uv release가 제공하는 최신 CPython 3.14 patch managed install·upgrade, lock과 기본 sync, `--no-sync`의 sync 및 root venv Python·BasedPyright probe 생략, atomic collision no-write, publish 전과 final marker commit 전 실패의 ownership-checked cleanup, 가능한 global uv side effect의 human·JSON diagnostic과 stable exit code를 자동 검증한다. init 전용 file·directory fsync, no-replace publish, parent fsync, marker unlink와 temp·target cleanup 각 단계에는 failure·crash injection을 수행한다. crash 뒤에는 absent target, ownership-marked incomplete/complete target 또는 exact markerless completed tree만 허용하며 existing target은 자동 overwrite하지 않는다.

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

초기부터 IDE를 완성하려 하지 않는다.

우선 CLI, formatter, 정확한 오류 메시지를 완성한 뒤 Tree-sitter 또는 LSP를 추가한다.

---

## 25. 향후 확장

### v0.2

* const generic과 variadic tuple
* 배열 길이와 고정 크기 buffer 타입
* 일반 pattern matching 계약
* 명시적 trait implementation과 default method
* Python implementation 자동 비교
* LSP 기초 지원

예시:

```cott
struct FixedBuffer[
    T,
    const N: U32,
]
```

### v0.3

* associated type
* effect 전파 검사
* 비동기 함수 계약
* resource 상태 타입
* 버전 호환성 검사
* 자동 migration 제안

### v1.0

* 안정된 언어 문법
* 안정된 IR schema
* Python 공식 backend
* 패키지 시스템과 설치된 wheel 전체의 독립적인 origin 검증
* IDE 플러그인

---

## 26. 핵심 설계 결정 요약

### 결정 1

cott는 실행 본문이 없는 선언형 계약 DSL이며 `.cott`와 typed Canonical IR이 의미 원본이다.

### 결정 2

MVP module graph는 비순환이고 source path mapping은 injective며 package 가능한 module은 최소 두 segment다. `core.*`, `cott_runtime`, `_cott_impl`과 `*_types` target path는 예약한다.

### 결정 3

MVP type system은 고정 폭 scalar, 명목 newtype·container, immutable struct, payload enum, invariant generic과 method-signature structural trait를 제공한다.

### 결정 4

trait implementation·default method·runtime dispatch, ownership, async와 정적 정리 증명은 MVP 밖이다.

### 결정 5

계약 표현식은 닫힌 순수 언어다. pattern과 clause는 typed IR이고 constant reference identity, error priority·exhaustiveness를 결정적으로 보존한다.

### 결정 6

Python ABI의 표준 identity는 project identity를 embed한 generated `cott_runtime` 하나가 소유한다. alias·trait, custom enum union·keyword-only frozen variant, struct·newtype, public constant와 resolved function의 공개 projection을 구분 없이 보존한다.

### 결정 7

`F32` binary32 normalization은 runtime mode와 무관하며 contract 산술의 매 operation에도 적용한다. integer range는 검사가 활성화된 concrete ABI boundary에서 확인하고 `off`에서는 trust declaration으로 남긴다.

### 결정 8

검증은 정적 증명, runtime 검사, test 관찰, 미관찰과 trust declaration을 구분해 실제보다 강하게 보고하지 않는다.

### 결정 9

자동 계약 테스트는 유효한 pure input을 staged facade를 통해 deny-by-default OS sandbox에서 실행한다. effectful function과 `Never` 반환 function은 MVP에서 자동 실행하지 않는다.

### 결정 10

Python function은 manifest의 plain top-level binding이거나 함수별 `_cott_impl` source다. local module은 canonical path의 generated runtime copy로 고정한다. 연결 정보는 Canonical IR가 아니라 target manifest와 provenance에 둔다.

### 결정 11

binding은 import 없이 staged type module에 대해 정적으로 해석한다. 모든 external implementation import에는 frozen production dependency closure의 selected lock hash와 observed installed distribution provenance가 필수며 archive-to-install 연결은 증거가 없으면 trust declaration이다.

### 결정 12

호출자는 cott path의 typed facade만 사용한다. facade는 embedded provenance로 local implementation의 generated copy를 검증하고 direct external dependency origin·hash를 preflight한 뒤 canonical name당 하나의 implementation module만 lazy load하며 load와 invocation을 같은 exception boundary로 감싼다.

### 결정 13

`off`, `boundary`, `test-only`는 facade bytes에 compile-time specialize되어 wrapper 검증 범위만 바꾸며 provenance, F32 normalization, newtype invariant와 exception containment는 끄지 않는다.

### 결정 14

`cott generate`는 user-selected Codex CLI 또는 OMP CLI를 함수별 process로, shell 없이 single-file write sandbox staging에서 호출한다.

agent는 실제 project를 쓰지 않고 선택 function file만 변경한다. scratch와 cache는 workspace 밖으로 격리한다.

### 결정 16

compiler output은 현재 IR과 command-owned scope에서 계산해 stale file을 정리한다. 성공 승격된 agent implementation은 durable source라 자동 삭제하지 않고 stale 상태만 진단한다.

### 결정 17

변경 command는 project lock, 시작·종료 hash, immutable pre-image journal, durable post-image와 atomic state marker를 사용한다. crash 뒤 old 또는 new complete snapshot으로 복구한다.

### 결정 18

runtime reader snapshot isolation은 보장하지 않는다. 변경 중 같은 project process를 실행하지 않고 배포는 완료 뒤 새 process로 시작한다.

### 결정 19

`generation.json.current`는 latest applied state, `last_verified`는 latest full-verified baseline이다. fmt·emit·generate는 후자를 보존하고 full verify만 승격한다.

### 결정 20

partial generate는 verified baseline의 기존 비선택 declaration과 symbol을 보존하되 새 declaration 추가는 허용하고, 최초 baseline 전에는 selected scope만 생성할 수 있다. 어느 경우도 배포 상태가 아니다.

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
