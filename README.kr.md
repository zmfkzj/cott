# cott

`cott`는 선언과 계약을 우선하는 DSL용 Rust 컴파일러다. 실행 본문이 없는 `.cott` module은
공개 type, function, contract, effect, scenario, error를 선언한다. Python은 그 선언의 검증된
projection이며 두 번째 계약 원본이 아니다.

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
오류다. 유효한 runtime capability가 없다고 결과를 만들어 내지 않는다. 관찰할 수 없으면
verification은 `unobserved`를 기록한다.

Evidence는 다음 중 하나다.

| 상태 | 의미 |
| --- | --- |
| static proof | 실행하지 않는 결정적 declaration, signature, type 또는 target-shape 검사가 통과했다. |
| runtime check | 설정된 production boundary가 검사를 실행했다. |
| test observation | 허용된 유효 case가 실행되어 contract point를 관찰했다. |
| unobserved | 허용된 runtime 또는 test observation이 없었다. |
| trust declaration | Cott가 일반적으로 증명하지 않은 채 선언을 받아들였다. |

Struct invariant는 canonical constructor 계약의 일부다. Scenario는 public facade와 닫힌
filesystem, HTTP, clock, failure fixture만 사용한다. Effectful fixture observation에는
compiler-owned Linux bubblewrap isolated-loopback sandbox가 필요하다. 격리가 없거나 사용할 수
없으면 unsandboxed 또는 external-network fallback이 아니라 `unobserved`다. Semantic coverage는
Canonical IR clause inventory와 runner evidence를 join하며, manifest coverage rule은 artifact
certification을 바꾸지 않고 선택한 clause만 gate할 수 있다.

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

`emit python`은 agent를 호출하지 않는다. compiler-owned output을 갱신하고 unresolved callable을
기록한다. `generate`는 eligible unresolved callable에 대해서만 선택한 agent를 호출하며, selected
binding과 accepted durable implementation은 재사용한다. `verify`는 source contract를 편집하지
않고 managed target을 다시 만들고 evidence와 provenance를 certify한다.

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
