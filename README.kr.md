# cott

`cott`는 typed intent와 prompt를 작성하는 language-like 컴파일러다. 실행 본문이 없는 `.cott`
module은 공개 type, function, contract, effect, scenario, error를 선언한다. 그 선언이 작성된
intent이며, Python·Kotlin/JVM·Dart는 검증된 projection이지 두 번째 계약 원본이 아니다. runtime
code는 generated public facade를 사용하며 authored `.cott`를 live로 읽지 않는다.

Cott는 그 선언을 고정하고, scoped generation prompt를 렌더하며, intent fingerprint를 기록하고,
구현 conformance, artifact identity, 관찰된 evidence를 검사한다. intent를 완전히 형식화하지
않으며, 통과한 검사는 구현 전반의 정확성 증명이 아니다. 제품은 typed authoring과 evidence이며
속도 주장이 아니다.

`architecture.md`는 구현된 v1.0 언어 계약의 규범 문서다. Package `1.0.0`, Canonical IR schema `8`,
contract-test strategy schema `5`, diagnostics schema `1`은 유지한다.
Python은 generation schema `8`, domain `cott.generation.v8`, runtime ABI `7`을 사용한다.
Kotlin은 generation schema `2`, domain `cott.kotlin.generation.v2`, runtime ABI `1`을 사용한다.
Dart는 generation schema `2`, domain `cott.dart.generation.v2`, runtime ABI `2`를 사용한다.
각 target의 닫힌 identity는 독립적이며 reader와 runtime은 다른 backend나 이전 record를 거부한다.
생성된 Dart package를 Flutter가 직접 소비하며 Kotlin bridge는 필요 없다.

이 문서와 repository source가 다르면 source file과 closed schema validator가 authority다.
Contradictory compatibility path를 만들지 말고 문서를 implementation에 맞게 고친다.

구현된 v0.8 `.cott` source는 의미를 바꾸지 않고 source-compatible 상태로 유지된다. Serialized 및
generated artifact는 exact-identity이므로 schema·ABI·package mismatch 뒤에는 다시 생성한다.
일반 reader는 이전 record를 거부하며 compatibility reader나 generated alias는 제공하지 않는다.

## 계약과 evidence

Cott는 선언을 resolve·type-check하고 Canonical IR로 lower한 뒤 target을 projection하며, 실제로
얻은 evidence만 기록한다. 잘못된 syntax, name, type, constant, tag, manifest, artifact identity는
오류다. 유효한 runtime capability가 없다고 결과를 만들어 내지 않는다. 실행 관찰을 할 수 없으면
verification은 `unobserved`를 기록한다. 지원되지 않거나 proof budget이 소진된 bounded proof는
`unknown`이며 `unobserved`나 trust가 아니다.

Evidence는 다음 중 하나다.

| 상태 | 의미 |
| --- | --- |
| static proof | 실행하지 않는 결정적 declaration, signature, type 또는 target-shape 검사가 통과했다. |
| runtime check | 설정된 production boundary가 검사를 실행했다. |
| test observation | 허용된 유효 case가 실행되어 contract point를 관찰했다. |
| unobserved | 허용된 runtime 또는 test observation이 없었다. |
| unknown | Bounded static proof가 지원되지 않거나 proof budget이 소진되었다. |
| trust declaration | Cott가 일반적으로 증명하지 않은 채 선언을 받아들였다. |

Struct invariant는 canonical constructor 계약의 일부다. Scenario는 public facade와 닫힌
filesystem, HTTP, clock, failure fixture만 사용한다. Effectful fixture observation에는
compiler-owned Linux bubblewrap isolated-loopback sandbox가 필요하다. 격리가 없거나 사용할 수
없으면 unsandboxed 또는 external-network fallback이 아니라 `unobserved`다. Semantic coverage는
Canonical IR clause inventory와 runner evidence를 join하며, manifest coverage rule은 artifact
certification을 바꾸지 않고 선택한 clause만 gate할 수 있다.

`doc`는 실행되지 않는 metadata이며 conformance를 판정하지 않는다. `doc`만 바뀐 contract diff는
`DOCUMENTATION`이며, 그 label이 regeneration 신호가 아니다. `doc`, 적용된 rule과 그 base, 계약 상수, 참조된 type, incoming
scenario, retained generator rule 식별자 변경은 해당 callable의 intent fingerprint를 갱신하고 agent regeneration을 큐에 넣을 수
있다. 관찰된 clause가 요구사항 완전성을 증명하지 않는다. `verified`는 해당 snapshot의 artifact,
type, runtime, proof, runner evidence 인증이다. 모든 semantic clause가 관찰되었거나 coverage
policy가 통과했음을 뜻하지 않는다. coverage gate는 선택한 rule이 있을 때만 동작하고, 선택한
rule이 없으면 gate가 없다. 외부 effect와 일부 boundary는 trust declaration이다. proof와 sampling은
bounded다. 지원되지 않거나 proof budget이 소진된 bounded proof는 `unknown`이다. 실행 관찰을 할
수 없으면 capability에 따라 `unobserved` 또는 trust다. 어느 쪽도 성공으로 위장하지 않는다.

같은 작업의 유효한 baseline은 typed Python과 독립 테스트다. 안정적인 public facade와
provenance/evidence 경계가 필요할 때 Cott 비용을 감수한다. 일차 비교는 같은 AI model이
Cott를 통해 생성하는 경우와 Python을 직접 생성하는 경우다. 사람 작성·검토 비용은 그
비교가 아니며 합성하지 않는다.

`benchmarks/contract_value.py`는 이미 생성된 artifact의 mutation·runtime 비용 실험이다.
generation 또는 productivity 증거가 아니다. 실제 AI generation 비교는
`benchmarks/ai_generation.py`다. 두 arm은 같은 artifact-pipeline 작업과 숨겨진 독립
3130-case corpus를 대상으로, 깨끗한 구현과 고정 model/config에서 시작한다. trial마다
Cott `generate` workflow 하나(native per-callable retry 포함)와 direct generation
invocation 하나를 실행하며 jobs는 최대 3이다. generation wall time과 verify/acceptance는
분리한다. Cott native provenance는 duration과 stream digest만 제공하고 token usage는
없으며 추론하지 않는다. 이 비교는 한 작업의 3 pair다. direct는 trial당 invocation 하나,
Cott는 native per-callable retry다. 두 arm은 같은 model과 toolset을 쓴다.

기록된 trial 숫자는 그 run에 저장된 compiler hash에 묶인 역사적 artifact다. 현재 prompt renderer의
성능 주장이 아니다.

독립 pipeline acceptance corpus는 `cott verify`의 일부가 아니며 canonical evidence source나
compiler certification이 아니다. 공유 case는
`examples/complex/artifact-pipeline/check_semantics.py`에 있다. 전제: 아래 예제 workflow로
project environment를 uv sync하고, 설치된 인증된 OMP와 실제 target environment가 있어야
한다. 그다음 실행한다.

```bash
examples/complex/artifact-pipeline/.venv/bin/python examples/complex/artifact-pipeline/check_semantics.py
examples/complex/artifact-pipeline/.venv/bin/python benchmarks/contract_value.py --cott cott --repeat 3 --output benchmarks/contract-value-results.json
examples/complex/artifact-pipeline/.venv/bin/python benchmarks/ai_generation.py --cott target/debug/cott --repeat 3 --jobs 3 --output benchmarks/ai-generation-results.json
```

## 예제 workflow

모든 예제는 독립 project다. Python project에는 저장소 root에서 아래 순서를 사용하고
`<project>`를 아래 index의 Python 경로로 바꾼다.

설치된 package와 command는 `cott --version`(또는 `cott -V`) 및 `cott --help`로 확인한다.

```bash
project=examples/<project>
UV_PROJECT_ENVIRONMENT="$project/.venv" uv sync --project "$project/python"
cott check --project "$project"
cott fmt --check --project "$project"
cott emit python --project "$project"
cott generate --agent claude --target python --project "$project"
cott verify --project "$project"
```

### Kotlin/JVM module workflow

Manifest는 `[target.python]`, `[target.kotlin]`, `[target.dart]` 중 정확히 하나만 선택한다.
Kotlin table은 닫혀 있다. `source`, `generated`, `runtime_validation`은 필수이고
`compiler = "kotlinc"`, `java = "java"`, `jvm_target = 17`은 해당 default다. JVM 17만
허용한다. `classpath`는 runtime JAR, `compile_only`는 Android SDK `android.jar` 같은
compile-time JAR 목록이다. 두 목록 모두 hash된 compiler input이지만 배포에는 `classpath`만
포함한다. Binding과 external projection은 target별 table을 사용한다.

```toml
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
"example.counter.increment" = "cott_bindings.counter.increment"

[target.kotlin.external_types]
"example.counter.PlatformValue" = "android.os.Bundle"
```

전체 Kotlin-only lifecycle은 같은 Cott source language와 Canonical IR을 사용한다.

```bash
cott init path/to/module --target kotlin
cott check --project path/to/module
cott fmt --check --project path/to/module
cott emit kotlin --project path/to/module
cott prompt example.module.callable --project path/to/module
cott generate example.module.callable --agent claude --target kotlin --project path/to/module
cott verify --project path/to/module
cott diff --project path/to/module
cott deploy --project path/to/module --output dist/example-module
```

`init --target kotlin`은 Cott Kotlin module만 만들며 Android application을 만들지 않는다.
`check`와 `fmt`는 Kotlin을 compile하지 않는다. `emit kotlin`은 agent나 compiler를 호출하지
않고 compiler-owned Kotlin source와 unverified record를 쓰며 unresolved callable facade는
생략한다. `prompt`는 provider나 compiler를 호출하지 않고 `implementation.kt` 지시를 출력한다.
`generate --target kotlin`은 eligible durable implementation source만 쓰고 항상 unverified
snapshot을 publish한다. 오직 명시적인 `verify`만 complete module을 compile하고 sandboxed
bounded contract runner를 실행해 `library/cott-module.jar`를 쓰며
`.snapshots[.current].verified = true`와 `current == last_verified`를 인증한다. source, manifest,
implementation, tool 또는 managed byte drift는 fail closed한다.

Kotlin/JVM은 ordinary type parameter를 erase한다. 따라서 Cott는 associated type을 추가 bounded
Kotlin type parameter로 projection하고 concrete impl assignment를 override 전에 해석하며,
reflection이나 phantom associated-type wrapper를 사용하지 않는다. Free const generic에는
명시적인 `_cott_const_*: CottConst` value-witness parameter를 넣어 정확한 unsigned
mathematical value를 보존한다. Ordinary type과 abstract associated-generic 관계는 static
guarantee다. Runtime validation은 임의의 erased `T`를 reify할 수 없고 bounded runner는
지원하지 않는 abstract associated runtime candidate를 observation으로 꾸미지 않고
unobserved/unknown으로 기록한다.

Manifest binding은 `target.kotlin.source` 아래의 source-owned 파일이며 accepted agent source는
`<target.kotlin.source>/cott_impl/<module>/<callable>.kt`에 있다. Package, canonical top-level
function, exact signature, path, content hash, intent fingerprint와 owner를 감사한다. 미구현
callable과 소유권이 확인된 intent-stale agent source는 unresolved로 남긴다. 기록에 없는 파일,
이동한 파일, 변조된 agent 파일은 오류로 거부하며 예전 record에서 trust를 갱신하지 않는다.
Public consumer는 generated Cott module package만 import하며 `cott_bindings`나 `cott_impl`을 import하지
않는다.

### Dart module과 Flutter workflow

Dart SDK는 `>=3.13.3,<4.0.0`이고 `project.name`은 lowercase snake_case Dart package name이다.
Cott는 module을 소유하며 Flutter는 widget, plugin, application resource와 platform build를
소유한다. `cott init --target dart`는 Dart Cott module만 만들며 Flutter app을 scaffold하지 않는다.

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

[target.dart.implementations]
"example.counter.increment" = "cott_bindings/counter/increment.dart:_increment"
```

```bash
cott init path/to/module --target dart --name example_module
# init은 빈 module을 만든다. 먼저 src/example_module/main.cott에 callable을 선언한다.
# 예: fn main() -> Unit
cott check --project path/to/module
cott emit dart --project path/to/module
cott prompt example_module.main.main --project path/to/module
cott generate --agent omp --target dart --project path/to/module
cott verify --project path/to/module
cott diff --project path/to/module
cott deploy --project path/to/module --output dist/example_module
```

`emit dart`와 `generate --target dart`는 항상 unverified snapshot을 publish한다. 오직 `verify`가
실제 Dart analyzer, kernel compiler와 인증된 bounded runner를 실행하고
`current == last_verified`를 인증한다. 작성된 private implementation은 compiler-owned Dart
part가 된다. Public caller는 implementation file 대신
`package:<name>/modules/<module path>.dart`를 import한다. Stateful method와 private state는
같은 owner-private library에 두어 guard 내부를 공개하지 않는다.

Runtime은 I64/U64를 `BigInt`로 보존하고 fixed-width 범위, F32 rounding, Unicode, immutable
value와 protocol lifecycle을 검사한다. Dart type만으로 구별할 수 없는 Cott generic 관계는
명시적인 `CottType<T>` witness와 checked view로 검사하며 Dart covariance를 그대로 신뢰하지
않는다. Const generic은 `CottConst` witness를 쓴다. Cancellation은 cooperative이고 guard
ownership은 명시적이다. 임의의 `Future`를 강제로 중단했다고 주장하지 않는다.

Dart ABI `2`는 비어 있지 않고 generic parameter가 없으며 모든 variant가 payloadless인 enum
선언 전체를 native Dart enum으로 투영한다. Cott author syntax는 바꾸지 않는다. Caller와 구현은
괄호 없이 정확한 Cott member spelling인 `Kind.Local`을 쓴다. `Kind.values`, `value.name`,
`value.index`와 exhaustive constant-pattern switch를 그대로 사용할 수 있다.

```dart
String label(Kind kind) => switch (kind) {
  Kind.Local => 'local',
  Kind.Remote => 'remote',
};
```

해당 enum의 이전 variant class는 alias 없이 제거한다. Payload나 generic parameter가 하나라도
있으면 선언 전체가 sealed arbitrary-value ADT로 남고 payloadless variant도 generated class
constructor를 쓴다. `Option`과 `Result`는 계속 generic ADT다.
Member 이름이 enum type 이름과 같을 때만 `Kind.Kind`를 `Kind.Kind$`로 escape하며 여전히 native
enum이다. Canonical identity는 그대로이고 native `.name`에는 `$`가 반영된다.

Verify host에는 Linux bubblewrap과 Landlock ABI `>=3`이 필요하다. Dart VM thread 생성 전에
filesystem policy를 적용해 process memory 접근을 거부하면서 VM의 `/proc/self/maps`와
허용된 scratch I/O는 유지한다. Runner event는 stdin으로만 받은 일회성 key로 HMAC-SHA256
인증하며 candidate stdout으로 snapshot을 인증할 수 없다.

외부 의존성이 있으면 `target.dart.pubspec`과 `target.dart.lockfile`을 함께 지정한다.
예: implementation source와 분리된 `dart_package/pubspec.yaml`, `dart_package/pubspec.lock`.
Name/version은 Cott project와 같아야 한다. Verify는 offline으로 정확한 production closure를
사용하고 override나 새 solver 선택을 허용하지 않는다. Hosted package는 원본 archive도
`$PUB_CACHE/hosted-archives/<registry-cache-key>/<name>-<version>.tar.gz`에 필요하다.
Registry의 `archive_url`에서 명시적으로 준비한 archive의 SHA-256을 lock과 대조하고,
그 내용과 extracted cache bytes를 비교한다. 수정 가능한 pub cache와 hash sidecar만으로는
인증하지 않는다. Archive가 없으면 필요한 경로를 진단하며 verify가 몰래 다운로드하지 않는다.

실행 가능한 Flutter consumer는 `examples/integrations/flutter-counter`다.

```bash
cd examples/integrations/flutter-counter
COTT_BIN=/absolute/path/to/cott FLUTTER_BIN=/absolute/path/to/flutter dart tool/setup.dart
cd flutter
flutter analyze --no-pub
flutter build web --release --no-pub --no-web-resources-cdn
flutter build apk --debug --no-pub
```

Setup은 module을 emit·verify한 뒤 `flutter/cott_module`에 deploy하고 Flutter의 `pub get`을
실행한다. 기존 deployment는 덮어쓰지 않는다. App은 path dependency를 통해
`package:flutter_counter/modules/example/counter.dart`만 import한다. Dart 배포에는 `lib/`,
compiler-owned `pubspec.yaml`, 원본 `generation.json`, `dependencies.json`과 검증된 runtime
vendor package가 들어간다. Kernel 검증 산출물, 계약, authoring copy, SDK, runner support와 cache는
제외하며 Flutter가 이 portable source를 선택한 platform용으로 compile한다.
Flutter `3.47.4`와 bundled Dart `3.13.3`의 analyzer, release web build, debug Android APK build가
통과했다. Browser에서 `0 → 1 → 0` 및 `0..100` 양쪽 경계를 확인했고 Cott module의 여섯 clause
모두 observed로 기록되었다. APK build 성공을 device 실행 증거로 간주하지 않는다.

### Prompt 검사와 snapshot lifecycle

프롬프트는 해당 함수의 프로젝트와 fully qualified name으로 확인한다. 예를 들면:

```bash
cott prompt curriculum.artifact_pipeline.plan_pipeline --project examples/complex/artifact-pipeline
cott prompt curriculum.artifact_pipeline.plan_pipeline --project examples/complex/artifact-pipeline --format json
```

`cott prompt <fully.qualified.callable> [--project DIR] [--format json]`는 정확한 초기 generation
prompt를 검사한다. provider 또는 target compiler/checker를 호출하지 않고 journal을 publish하거나
recover하지 않는다. human mode는 prompt bytes를 쓰고 JSON은
`{symbol,intent_hash,prompt_hash,generation_required,context,prompt}`다. `prompt`는 그 초기
bytes와 같고 `prompt_hash`는 초기 prompt만 hash한다. retry는 실제 validation feedback을 뒤에
붙인다. 요청 write path는 Python의 `implementation.py`, Kotlin의 `implementation.kt`, Dart의 `implementation.dart`다.
inspection은 project lock과 lock metadata를 허용하며 pending journal은 recovery 없이 거부한다.
`context`는 scoped transitive declaration 집합이다. explicit identifier 참조, `constant_ref`,
`cott.applied_rule`과 그 base, 관련 incoming scenario, 전역 rule prose와 선택 callable의
`cott-domain` 줄만 포함한다. prompt 섹션은 authority, current intent, formal declarations,
project rules, reference implementations, target output rules, optional feedback다. rule과
reference prose는 source를 override하지 않으며 충돌은 NLP로 증명하지 않고 표면에 남긴다.

Target emission은 agent를 호출하지 않는다. Compiler-owned output을 갱신하고 unresolved
callable을 기록하며 해당 callable facade는 생략한다. `emit ir`은 IR scope와
`generation.json`만 갱신하고 non-IR managed hash는 기존 신뢰 값을 유지하므로 IR-only
emission은 무관한 디스크 편집을 신뢰한 것으로 처리하지 않는다. Authentic `AgentRun`
provenance가 있는 pending unresolved agent source는 emit과 checkpoint를 반복해도
`generate`가 재생성할 때까지 소유권을 유지한다. Manifest-owned binding은 intent
regeneration에서 제외한다. 기록된 path·content hash와 다른 tampered agent file은 거부한다.
`generate`는 eligible unresolved callable에 대해서만 선택한 agent를 호출하며 selected binding과
accepted durable implementation은 intent fingerprint가 바뀌지 않으면 재사용한다. 한 generate
호출의 초기 prompt snapshot은 고정되고 이후 수락한 wave candidate는 validation에만 쓰인다.
Emit과 generate는 항상 current snapshot을 unverified로 둔다. 오직 `verify`만 source contract를
편집하지 않고 managed target을 다시 만들고 evidence를 certify한다. Pending unresolved를
거부하며 현재 facade에 없는 옛 managed implementation을 export하지 않는다. `current`는 마지막
emit epoch의 참조이고 `last_verified`는 인증된 역사 baseline의 참조 또는 `null`이다. Verified
current는 `last_verified`와 같은 참조여야 한다. 이미 배포된 snapshot은 `emit` 또는 `generate`
전까지 옛 계약을 유지하고 runtime은 authored `.cott`를 live로 읽지 않는다. 유효한 Python record에
`tools.cott_intent`가 없으면 기록된 contract surface에서 fingerprint를 derive한다. 부재를 fresh로
보지 않으며 manifest나 rule evidence가 없으면 보수적으로 invalidate한다. 이전 schema reader는 아니다.

닫힌 `generation.json` envelope의 key는 정확히 `schema_version`, `current`, `last_verified`,
`snapshots`다. 두 참조는 snapshot content digest이고 `snapshots`는 digest에서 full snapshot
object로 가는 map이다. 참조 가능한 blob만 정확히 1~2개 저장하며 같은 참조는 한 번만 저장한다.
검증 flag는 `jq '.snapshots[.current].verified' generation.json`으로 읽는다. `current`를 object로
읽지 않으며 unused·dangling·tampered blob은 거부한다.

Snapshot content identity는 전체 verification evidence·`AgentRun`·`verified` flag를 포함한다.
기존 volatile field를 제외한 normalized generation identity를 명시적인 target-domain wrapper로
묶는 `generation_id`와 별개다. 둘 다 `cott.snapshot.v1` 뒤 NUL, tagged·length-delimited value와
float의 f64 IEEE bits에 SHA-256을 적용하는 structural JSON digest를 쓴다. Raw JSON text의
hash가 아니다. Envelope와 정확한 identity 규칙은 architecture §16.1을 따른다.

Record는 self-contained이므로 diff baseline 보관이나 relocation·deploy에 외부 snapshot cache나
sidecar가 필요 없다. Regenerated output에는 새 runtime loader와 self-contained deployment
record가 필요하다. 일회성 repository cutover만 compiler-linked transaction conversion으로 source와
`AgentRun` evidence를 보존하고 verification을 해제한 뒤 실제 emit·verify를 수행한다. 공개 migration
command나 일반 old-record reader가 아니다. 이전 certification은 새 schema·ABI로 승계되지 않으며
source hash를 손으로 바꿔 변경된 agent code를 인증해서는 안 된다.

`generate --agent`는 `codex`, `claude`, `omp` 세 direct adapter를 받는다. `claude`는 official
native Claude Code `>=2.1.89`를 직접 호출하며, OMP가 Claude model을 선택한 실행은 여전히
`omp`이고 `claude`가 아니다. generation 전에 direct Claude의 native-entrypoint check는 npm
`cli.js` entrypoint와 Node shebang을 거부하고 exact credential-free, network-disabled probe
`claude --version`을 실행한다. probe는 timeout 없이 status `0`으로 끝나야 하며 stdout 전체는
정확히 하나인 strict SemVer token `>=2.1.89`여야 한다. generation은 별개로 exact UTF-8 prompt를
stdin으로 받고 `Read`와 `Write`만 사용하며 successful JSON result만 수락한다. existing
`ANTHROPIC_API_KEY`와 provider network egress를 가질 수 있는 것은 generation뿐이며
network-capable Claude tool은 노출하지 않는다. normative argv, environment, native-entrypoint,
result contract는 architecture §17.2.1에 있다.

각 예제에 commit된 `generated/`와 agent-owned `python/_cott_impl/` 또는
`<target.kotlin.source>/cott_impl/` 파일은 실제 compiler result다. Authoring shortcut이 아니다.
`.venv/`, `.cott/`, `.gradle/`, `build/`, `__pycache__/`는 transient다. Public code는 generated Cott
facade만 import하며 `_cott_impl`, `cott_bindings`, `cott_impl`은 public import path가 아니다.

## 실행용 배포 패키지

`cott deploy [--output <dir>] [--project <dir>] [--format json]`는 검증된 현재 snapshot을
새 디렉터리에 패키징한다. 기본 출력은 `<project>/dist/<이름>-<버전>/`이며, 상대 `--output`은
명령을 실행한 작업 디렉터리 기준이다. 기존 출력은 덮어쓰지 않고 원본과 생성물도 수정하지 않는다.

```bash
cott deploy --project examples/grammar/checked-add --output dist/checked-add
cd dist/checked-add
uv venv
uv pip install --require-hashes -r requirements.txt
PYTHONPATH=python .venv/bin/python -c 'from curriculum.checked_add import checked_add; print(checked_add(1, 2))'
```

패키지는 공개 facade·타입·`cott_runtime`·선택된 구현 복사본·작성한 Python 어댑터가 있는
`python/`, 원본 bytes 그대로인 `generation.json`, 정확한 target patch를 담은 `.python-version`,
hash로 고정된 production `requirements.txt`만 포함한다. Cott 실행 파일, `.cott` 원본,
`cott.toml`, `generated/` 디렉터리, IR, 스텁, 테스트, 작성용 private 구현 복사본,
개발 디렉터리, 가상환경과 캐시는 제외한다. 실행에 필요한 생성 Python 코드는 삭제하지 않고
옮긴다. 기존 무결성 검사를 위해 `cott_runtime`과 `generation.json`은 유지한다.
Python 이외의 애플리케이션 리소스는 추측해서 복사하지 않는다.

현재 snapshot이 verified이고 미구현 항목이 없으며 선택한 coverage policy를 통과해야 한다.
입력과 managed file의 실제 bytes가 기록과 달라도 거부한다. 생성이나 재검증은 호출하지 않는다.
의존성이 있으면 uv `>=0.12.3`으로 frozen lock을 offline export하며 개발/default dependency
group은 제외한다. 의존성이 없으면 패키징 시 uv도 필요 없다. 배포 환경에는 기록된 것과 같은
CPython patch·OS·architecture 및 third-party 의존성을 별도로 준비한다. Cott는 필요 없다.

Kotlin 배포에는 `cott-module.jar`, 원본 bytes 그대로인 `generation.json`,
`dependencies.json`, `runtime-libs/`가 들어간다. Compiler distribution의 정확한
`kotlinx-coroutines-core-jvm.jar` version `1.8.0`과 verified `classpath` JAR는 runtime
library다. Kotlin stdlib는 Kotlin 또는 Android Gradle plugin이 제공하는 required·hash-recorded
dependency이므로 중복 bundle하지 않고, `compile_only` JAR도 절대 배포하지 않는다.

Android counter는 이 deployed module을 사용하는 일반 Gradle consumer다.

```bash
project=examples/integrations/android-counter
cott check --project "$project"
cott fmt --check --project "$project"
cott emit kotlin --project "$project"
cott verify --project "$project"
cott deploy --project "$project" --output dist/android-counter-module

COTT_BIN="$PWD/target/debug/cott" \
  "$project/android/gradlew" --project-dir "$project/android" --no-daemon :app:assembleDebug
```

예제 wrapper는 official Gradle `9.1.0` distribution과 SHA-256
`a17ddd85a26b6a7f5ddb71ff8b05fc5104c0202c6e64782429790c933686c806`을 pin한다. Standard
Android project는 Android Gradle plugin `9.0.1`(bundled Kotlin `2.2.10`), compile/target SDK
`36`, min SDK `26`, JVM 17을 사용한다. 개발 중에는 `COTT_BIN`으로 repository 안 compiler를
선택하고 installed `cott`에는 생략할 수 있다. Gradle task는 deployed module JAR와 runtime
dependency JAR만 사용한다. Application code는 public `example.counter.increment`와
`example.counter.decrement`만 import한다. 별도의 native JVM consumer는 published module을
대상으로 compile·run되어 `increment(0) == 1`, `decrement(100) == 99`, invalid
`increment(100)` 거부를 관찰했고 verification은 여섯 clause 모두를 observed로 기록했으며
unknown/unobserved clause는 없었다. 또한 pinned Gradle build로 debug APK를 assemble한 뒤
AOSP API 36 software emulator에 설치했고 UI에서 bounded counter의 `0 → 1 → 0` 전이를
관찰했다. 이는 emulator evidence이며 physical-device 성공 주장은 아니다.

Cott가 소유하는 범위는 Cott module의 compilation, verification, deployment뿐이다. 일반
Android/Gradle이 UI source, `AndroidManifest.xml`, resource, dependency graph, DEX, APK/AAB
assembly, signing, installation과 device lifecycle을 소유한다. Cott는 Android app을 scaffold하지
않고 Python을 device에서 실행하지 않는다.

## 축소된 예제 index

작성된 inventory는 Python project 26개, Kotlin project 20개, Dart/Flutter project 1개다.
Python set은 grammar 6개, simple 3개, complex curriculum 1개, 별도 `process-bar` fixture,
feature 7개, modular 1개, FastAPI integration 1개, real-world 6개다. `examples/kotlin/`의
19개 Kotlin lesson/fixture와 `integrations/android-counter`가 Kotlin set을 구성하며,
`integrations/flutter-counter`가 Dart module과 standard Flutter consumer다.

### Grammar — 6

| Project | 고유 계약 |
| --- | --- |
| `grammar/checked-add` | 유일한 focused manifest-binding lesson: `checked_add(I32, I32) -> I64`. |
| `grammar/assignment-rule` | Access code의 rule inheritance, override, deletion, error selection. |
| `grammar/cta-row` | Nominal transit row decoding과 순서가 있는 validation error. |
| `grammar/fractional-range-values` | Refined floating step과 bounded finite range 계약. |
| `grammar/portfolio-cost` | 순서가 있는 portfolio validation과 finite aggregate valuation. |
| `grammar/stock-record` | `value_record`와 합성되는 validated stock-record facade. |

`checked-add`는 의도적으로 binding example이다. Manifest는
`curriculum.checked_add.checked_add`를 project-local compatible implementation에 mapping한다.
Mapping은 implementation을 선택할 뿐 Cott contract를 정의하지 않는다.

### Simple — 3

| Project | 고유 계약 |
| --- | --- |
| `simple/alphabetical-file-groups` | Public `classify_filename` facade를 통한 순서 보존 filename grouping. |
| `simple/calculator` | Division-by-zero error를 가진 닫힌 arithmetic operation enum. |
| `simple/decimal-binary` | Canonical binary와 overflow 규칙을 가진 tagged decimal/binary conversion. |

### Complex curriculum — 1

| Project | 고유 계약 |
| --- | --- |
| `complex/artifact-pipeline` | 순수하고 결정적인 topological ordering 및 artifact-plan composition. |

### Full-generation fixture — 1

`complex/process-bar`는 두 번째 curriculum category가 아니다. `foo.bar`의 focused
full-agent-generation fixture다. `process_bar`는 public facade를 통해 `validate_payload`,
`process_payload_bytes`, `build_output`을 합성한다. Commit된 generation record와 `_cott_impl` tree는
실제 accepted compiler output이다.

### Real — 6

| Project | 고유 계약 |
| --- | --- |
| `real/yt-dlp` | Playlist selection, archive-aware download planning, output template, JSON rendering, bounded media transfer. |
| `real/harlequin` | SQLite statement execution, schema catalog search, 결정적인 query 및 catalog rendering. |
| `real/pgcli` | Connection precedence, SQL completion, query rendering, backslash command, database execution. |
| `real/posting` | YAML HTTP-request collection, variable resolution, curl export, persistence, bounded network request. |
| `real/toolong` | Bounded log paging, JSONL rendering, merging, searching, appended-file read. |
| `real/frogmouth` | Markdown document navigation, loading, state persistence, sidebar application behavior. |

### Focused features — 7

| Project | 고유 계약 |
| --- | --- |
| `features/declarations-generics` | Alias, constant, refinement, variance, const generic, `Array`, `Buffer`, cross-module declaration. |
| `features/contracts-evidence` | Struct invariant, refined label, rule refinement, clause-level evidence/coverage policy. |
| `features/boundary-protocols` | External projection, `Opaque`, `Any`/`Unknown`, iterator/generator, async protocol boundary. |
| `features/trait-protocol` | Structural trait, associated type, specialization, `Dyn`, `Factory`, resource transition, async impl method. |
| `features/json-transform` | Recursive JSON-facing declaration과 typed JSON transformation. |
| `features/effects-selection` | 닫힌 fixture scenario를 가진 filesystem, HTTP, database, clock, random, process effect. Isolated loopback을 사용할 수 없으면 fixture evidence는 `unobserved`이고 host network를 사용하지 않는다. |
| `features/workflow-scenario` | Finite lifecycle scenario: async spawn/await/cancel, stale-result exclusion, coalesced save. |

### Python composition과 integration — 2

| Project | 고유 계약 |
| --- | --- |
| `modular/order-management` | `store.order`와 `store.catalog`이 generated module facade를 통해 합성된다. |
| `integrations/fastapi-hello` | FastAPI projection: external `HttpRequest`는 `starlette.requests:Request`로 mapping되며, 작은 app adapter가 generated `read_root` facade를 등록한다. |

### Kotlin/Android integration — 1

| Project | 고유 계약 |
| --- | --- |
| `integrations/android-counter` | Kotlin/JVM 17 Cott counter module을 JAR로 배포하고 standard Gradle-owned Android application이 public `example.counter` import로 소비한다. |

## Editor analysis

Cott project에서 인자 없이 language server를 실행한다.

```bash
cott lsp
```

UTF-16 position과 full document sync로 stdio JSON-RPC diagnostic, completion, hover, definition을
제공한다. Open document만 분석하며 emit, publish, agent invocation은 수행하지 않는다.
