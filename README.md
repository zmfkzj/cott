# cott

`cott` is a Rust compiler for a declaration- and contract-first DSL. A bodyless `.cott`
module declares public types, functions, contracts, effects, scenarios, and errors; Python is a
verified projection of that declaration, not a second contract source.

`architecture.md` is the normative implemented v0.8 contract. The closed compatibility identity is
package `0.8.0`, Canonical IR schema `8`, generation schema/domain
`7` (`cott.generation.v7`), Python runtime ABI `7`, and contract-test strategy schema `5`.
Readers and loaders reject incompatible generation records, strategies, and runtime identities.

## Contract and evidence

Cott resolves and type-checks declarations, lowers Canonical IR, projects a target, and records only
the evidence it actually obtains. Invalid syntax, names, types, constants, tags, manifests, and
artifact identities are errors. A missing valid runtime capability does not invent a result:
verification records `unobserved` where observation is unavailable.

Evidence is one of:

| Status | Meaning |
| --- | --- |
| static proof | A deterministic non-executing declaration, signature, type, or target-shape check passed. |
| runtime check | A configured production boundary executed the check. |
| test observation | A permitted valid case executed and observed the contract point. |
| unobserved | No permitted runtime or test observation was available. |
| trust declaration | The declaration is accepted without general proof by Cott. |

Struct invariants are part of the canonical constructor contract. Scenarios use only public facades
and closed filesystem, HTTP, clock, and failure fixtures. Effectful fixture observations require the
compiler-owned Linux bubblewrap isolated-loopback sandbox; missing or unusable isolation is
unobserved, never an unsandboxed or external-network fallback. Semantic coverage joins the Canonical
IR clause inventory to runner evidence; manifest coverage rules may gate selected clauses without
changing artifact certification.

## Example workflow

Every example is an independent project. Use this one sequence from the repository root; replace
`<project>` with an index path below.

```bash
project=examples/<project>
UV_PROJECT_ENVIRONMENT="$project/.venv" uv sync --project "$project/python"
cott check --project "$project"
cott fmt --check --project "$project"
cott emit python --project "$project"
cott generate --agent omp --target python --project "$project"
cott verify --project "$project"
```

`emit python` never invokes an agent. It updates compiler-owned output and records unresolved
callables. `generate` invokes the selected agent only for eligible unresolved callables; selected
bindings and accepted durable implementations are reused. `verify` rebuilds the managed target and
certifies evidence and provenance without editing source contracts.

`generated/` and any agent-owned `python/_cott_impl/` files committed in an example are actual
compiler results. They are not an authoring shortcut. `.venv/`, `.cott/`, and `__pycache__/` are
transient. Public code imports generated Cott facades only; neither `_cott_impl` nor
`cott_bindings` is a public import path.

## Reduced example index

The maintained inventory has 20 projects: six grammar lessons, three simple lessons, one complex
curriculum project, the separate `process-bar` full-generation fixture, seven focused features, one
modular project, and one FastAPI integration.

### Grammar — 6

| Project | Distinct contract |
| --- | --- |
| `grammar/checked-add` | The sole focused manifest-binding lesson: `checked_add(I32, I32) -> I64`. |
| `grammar/assignment-rule` | Rule inheritance, override, deletion, and error selection for an access code. |
| `grammar/cta-row` | Nominal transit-row decoding and ordered validation errors. |
| `grammar/fractional-range-values` | Refined floating step and bounded finite range contract. |
| `grammar/portfolio-cost` | Ordered portfolio validation and finite aggregate valuation. |
| `grammar/stock-record` | A validated stock-record facade composed with `value_record`. |

`checked-add` is intentionally a binding example. Its manifest maps
`curriculum.checked_add.checked_add` to the project-local compatible implementation; the mapping
selects an implementation and never defines the Cott contract.

### Simple — 3

| Project | Distinct contract |
| --- | --- |
| `simple/alphabetical-file-groups` | Ordered filename grouping through the public `classify_filename` facade. |
| `simple/calculator` | Closed arithmetic operation enum with division-by-zero error. |
| `simple/decimal-binary` | Tagged decimal/binary conversion with canonical binary and overflow rules. |

### Complex curriculum — 1

| Project | Distinct contract |
| --- | --- |
| `complex/artifact-pipeline` | Pure deterministic topological ordering and artifact-plan composition. |

### Full-generation fixture — 1

`complex/process-bar` is not a second curriculum category. It is the focused full-agent-generation
fixture for `foo.bar`: `process_bar` composes `validate_payload`, `process_payload_bytes`, and
`build_output` through public facades. Its committed generation record and `_cott_impl` tree are the
actual accepted compiler output.

### Focused features — 7

| Project | Distinct contract |
| --- | --- |
| `features/declarations-generics` | Aliases, constants, refinements, variance, const generics, `Array`, `Buffer`, and cross-module declarations. |
| `features/contracts-evidence` | Struct invariants, refined labels, rule refinement, and clause-level evidence/coverage policy. |
| `features/boundary-protocols` | External projection, `Opaque`, `Any`/`Unknown`, iterator/generator, and async protocol boundaries. |
| `features/trait-protocol` | Structural traits, associated types, specialization, `Dyn`, `Factory`, resource transitions, and async impl methods. |
| `features/json-transform` | Recursive JSON-facing declarations and typed JSON transformation. |
| `features/effects-selection` | Filesystem, HTTP, database, clock, random, and process effects with closed fixture scenarios. An unavailable isolated loopback leaves fixture evidence unobserved; it never uses host networking. |
| `features/workflow-scenario` | Finite lifecycle scenarios: async spawn/await/cancel, stale-result exclusion, and coalesced save. |

### Composition and integration — 2

| Project | Distinct contract |
| --- | --- |
| `modular/order-management` | `store.order` and `store.catalog` compose through generated module facades. |
| `integrations/fastapi-hello` | FastAPI projection: external `HttpRequest` maps to `starlette.requests:Request`; the generated `read_root` facade is registered by the small app adapter. |

## Editor analysis

Run the parameterless language server from a Cott project:

```bash
cott lsp
```

It serves stdio JSON-RPC diagnostics, completion, hover, and definition with UTF-16 positions and
full document sync. It analyzes open documents only; it does not emit, publish, or invoke an agent.
