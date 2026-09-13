# cott

`cott`는 typed intent와 prompt를 작성하는 language-like 컴파일러다. 실행 본문이 없는 `.cott`
module은 공개 type, function, contract, effect, scenario, error를 선언한다. 그 선언이 작성된
intent이며, Python은 검증된 projection이지 두 번째 계약 원본이 아니다. runtime은 generated
facade를 load하며 authored `.cott`를 live로 읽지 않는다.

Cott는 그 선언을 고정하고, scoped generation prompt를 렌더하며, intent fingerprint를 기록하고,
구현 conformance, artifact identity, 관찰된 evidence를 검사한다. intent를 완전히 형식화하지
않으며, 통과한 검사는 구현 전반의 정확성 증명이 아니다. 제품은 typed authoring과 evidence이며
속도 주장이 아니다.

`architecture.md`는 구현된 v1.0 언어 계약의 규범 문서다. 닫힌 호환성 identity는 package `1.0.0`,
Canonical IR schema `8`, generation schema/domain `7` (`cott.generation.v7`), Python runtime ABI
`7`, contract-test strategy schema `5`, diagnostics schema `1`이다. reader와 loader는 호환되지 않는
generation record, strategy, runtime identity를 거부한다.

구현된 v0.8 `.cott` source는 의미를 바꾸지 않고 source-compatible 상태로 유지된다. Serialized 및
generated artifact는 exact-identity다. package mismatch 뒤에는 다시 생성해야 하며, Cott는 legacy
reader를 제공하지 않는다.

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

모든 예제는 독립 project다. 저장소 root에서 아래 한 순서를 사용하고, `<project>`를 아래 index의
경로로 바꾼다.

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

프롬프트는 해당 함수의 프로젝트와 fully qualified name으로 확인한다. 예를 들면:

```bash
cott prompt curriculum.artifact_pipeline.plan_pipeline --project examples/complex/artifact-pipeline
cott prompt curriculum.artifact_pipeline.plan_pipeline --project examples/complex/artifact-pipeline --format json
```

`cott prompt <fully.qualified.callable> [--project DIR] [--format json]`는 초기 generation prompt를
검사한다. provider, Python, type checker를 호출하지 않고 journal을 publish하거나 recover하지 않는다.
human mode는 prompt bytes를 쓰고 JSON은
`{symbol,intent_hash,prompt_hash,generation_required,context,prompt}`다. `prompt`는 그 초기 bytes와
같고 `prompt_hash`는 초기 prompt만 hash한다. retry는 실제 validation feedback을 뒤에 붙인다.
prompt의 write path는 relative `implementation.py`다. inspection은 project lock과 lock metadata를
허용하며 pending journal은 recovery 없이 거부한다. `context`는 scoped transitive declaration
집합이다. explicit identifier 참조, `constant_ref`, `cott.applied_rule`과 그 base, 관련 incoming scenario, 전역 rule prose와 선택 callable의
`cott-domain` 줄만 포함한다. prompt 섹션은 authority, current intent, formal declarations, project
rules, reference implementations, output rules, optional feedback다. rule과 reference prose는
source를 override하지 않으며 충돌은 NLP로 증명하지 않고 표면에 남긴다.

`emit python`은 agent를 호출하지 않는다. compiler-owned output을 갱신하고 unresolved callable을
기록하며 그 callable은 public facade에서 생략한다. `emit ir`은 IR scope와 `generation.json`만 갱신하고
non-IR managed hash는 기존 신뢰 값을 유지하므로 IR-only emission은 무관한 디스크 편집을 신뢰한 것으로 처리하지 않는다. authentic `AgentRun` provenance가 있는 pending
unresolved agent source는 emit과 checkpoint를 반복해도 `generate`가 재생성할 때까지 소유권을
유지한다. manifest-owned binding은 intent regeneration에서 제외한다. 기록된 path·content hash와
다른 tampered agent file은 거부한다. `generate`는 eligible unresolved callable에 대해서만 선택한
agent를 호출하며, selected binding과 accepted durable implementation은 intent fingerprint가 바뀌지
않으면 재사용한다. 한 generate 호출에서 미리보기로 제시한 초기 prompt snapshot은 고정되며, 이후 수락한 wave candidate는 validation에만 쓰인다. `verify`는 source contract를 편집하지 않고 managed target을 다시 만들고
evidence와 provenance를 certify한다. pending unresolved를 거부하며 현재 facade에 없는 옛 managed
implementation을 export하지 않는다. `current`는 마지막 emit epoch이고 `last_verified`는 인증된
역사 baseline이다. 이미 배포된 snapshot은 `emit` 또는 `generate` 전까지 옛 계약을 유지한다.
runtime은 authored `.cott`를 live로 읽지 않는다. `tools.cott_intent`가 없는 same-v7 record는 기록된
`contract_surface`에서 fingerprint를 derive한다. 부재를 fresh로 보지 않으며 manifest나 rule input
증거가 없으면 보수적으로 invalidate한다.

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

각 예제에 commit된 `generated/`와 agent-owned `python/_cott_impl/` 파일은 실제 compiler
result다. authoring shortcut이 아니다. `.venv/`, `.cott/`, `__pycache__/`는 transient다. Public
code는 generated Cott facade만 import한다. `_cott_impl`과 `cott_bindings`는 public import path가
아니다.

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

## 축소된 예제 index

유지되는 inventory는 26개 project다. grammar lesson 6개, simple lesson 3개, complex curriculum
project 1개, 별도 `process-bar` full-generation fixture, focused feature 7개, modular project 1개,
FastAPI integration 1개, real-world generation-first project 6개로 구성된다.

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

### Composition과 integration — 2

| Project | 고유 계약 |
| --- | --- |
| `modular/order-management` | `store.order`와 `store.catalog`이 generated module facade를 통해 합성된다. |
| `integrations/fastapi-hello` | FastAPI projection: external `HttpRequest`는 `starlette.requests:Request`로 mapping되며, 작은 app adapter가 generated `read_root` facade를 등록한다. |

## Editor analysis

Cott project에서 인자 없이 language server를 실행한다.

```bash
cott lsp
```

UTF-16 position과 full document sync로 stdio JSON-RPC diagnostic, completion, hover, definition을
제공한다. Open document만 분석하며 emit, publish, agent invocation은 수행하지 않는다.
