# Repository Guidelines

## Project Overview

`cott` is a Rust 2024 compiler for a static, declaration- and contract-first DSL. A bodyless
`.cott` module is the public contract source. Python bindings or accepted agent implementations are
checked projections; generated Python facades are the only public import path.

`architecture.md` is the authoritative implemented v0.8 contract: package `0.8.0`, Canonical IR
schema `8`, generation schema/domain `7` (`cott.generation.v7`), runtime ABI `7`, and
contract-test strategy schema `5`. Keep this closed compatibility contract: incompatible records,
runtimes, and strategies fail closed. Do not add a legacy reader, partial profile, unsandboxed
fixture fallback, or second source of truth.

## Architecture & Data Flow

```text
cott check / fmt / emit / generate / verify / diff
  → closed manifest + symlink-safe source discovery
  → lossless CST → AST → complete HIR → canonical IR
  → binding or scoped agent implementation validation
  → deterministic Python, stub, test, and provenance plan
  → journaled publish, exact verification, or semantic diff
```

- `src/manifest.rs` and `src/project.rs` own the closed manifest, paths, and source discovery.
- `src/syntax.rs`, `src/lexer.rs`, `src/parser.rs`, `src/ast.rs`, `src/hir.rs`, and `src/formatter.rs`
  implement the source pipeline; `src/ir.rs` renders and validates canonical JSON.
- `src/binding.rs` resolves manifest and durable agent implementations with byte identity.
- `src/python_emit.rs`, `src/python_runtime.rs`, `src/python_verify.rs`, and
  `src/contract_test.rs` own the Python ABI and verification pipeline.
- `src/agent.rs`, `src/sandbox.rs`, `src/transaction.rs`, and `src/cli.rs` own external execution,
  containment, crash-safe publication, command grammar, and exit codes.
- Generated artifact paths are compiler-owned. Do not hand-edit `generated/`; change the contract or
  the selected implementation source, then use the command that owns the managed output.

## Key Directories

| Path | Purpose |
| --- | --- |
| `src/` | Rust compiler, semantic model, emitter, and CLI |
| `tests/` | Rust integration tests; use public APIs or the built `cott` binary |
| `examples/grammar/` | Six declaration and ABI lessons, including `checked-add` binding |
| `examples/simple/` | Three compact composition lessons |
| `examples/complex/artifact-pipeline/` | The one pure complex curriculum project |
| `examples/complex/process-bar/` | Focused full-agent-generation fixture, outside curriculum counts |
| `examples/features/` | Seven focused v0.8 feature projects |
| `examples/modular/order-management/` | Multi-module facade composition |
| `examples/integrations/fastapi-hello/` | FastAPI external-type projection |
| `examples/**/src/**/*.cott` | Authoritative example contracts |
| `examples/**/python/cott_bindings/**/*.py` | Selected project-local binding sources where a manifest maps them |
| `examples/**/python/_cott_impl/**/*.py` | Durable accepted agent implementation sources where present |
| `architecture.md` | Normative implemented v0.8 contract |

The maintained inventory is 20 independent projects: grammar 6, simple 3, complex curriculum 1,
`process-bar` fixture 1, features 7, modular 1, and FastAPI integration 1. Every project has
`cott.toml` and `src/`; its managed/output and implementation layout follows its own manifest and
generation record. Committed `generated/` and agent-owned `_cott_impl` content are compiler results.
Never treat `.venv/`, `.cott/`, or `__pycache__/` as managed project content.

## Development Commands

```bash
cargo fmt --check
cargo test
cargo run -- --help
cargo run -- check --project examples/grammar/checked-add
cargo run -- emit ir --project examples/grammar/checked-add
```

The implemented command forms are:

```text
cott init <path> [--name <name>] [--no-sync] [--format json]
cott check [<source.cott>] [--project <dir>] [--format json]
cott fmt [--check] [--project <dir>] [--format json]
cott emit ir|python [--project <dir>] [--format json]
cott generate [<fully.qualified.function>] --agent codex|omp --target python [--project <dir>] [--format json]
cott verify [--project <dir>] [--format json]
cott diff [--baseline <generation.json>] [--exit-code] [--project <dir>] [--format json]
cott lsp
```

`emit` and `generate` publish through the project transaction and leave `current.verified = false`.
`emit python` never invokes an agent. `generate` invokes the selected agent only for eligible
unresolved callables. `verify` rebuilds and checks the complete target without a cache, then updates
provenance and applies any selected semantic-coverage gate.

## Code Conventions & Common Patterns

### Rust

- Format with `cargo fmt`; remain dependency-light and reuse stdlib before adding crates.
- Prefer deterministic structures (`BTreeMap`/`BTreeSet`) for externally visible ordering and
  artifact plans. Preserve source/module/declaration order where the semantic model owns it.
- Return structured, path-attached diagnostics instead of panicking for user input.
- Treat filesystem paths and output trees as trust boundaries: reject symlinks, unsafe relative paths,
  and partial publication. Keep output staging/publishing in `src/cli.rs`.
- Keep public data types simple (`Clone`, `Debug`, `Eq`, `PartialEq`) when tests need observable values.

### Cott v0.8

- A source file has one module whose name injectively matches its source-relative path.
- Supported types include fixed-width numeric types, `Path`, `Unit`, `Never`, `Any`, `Unknown`,
  `JsonValue`, constrained `Opaque`, nominal/generic types, `Array`, `Buffer`, and closed standard
  containers and protocols.
- Supported declarations include aliases, refined newtypes, immutable structs with ordered
  invariants and constant defaults, payload enums, structural traits, typed constants, resources,
  finite scenarios, and public function signatures.
- Functions support parameters, generics/bounds, `requires`, `ensures`, conditional `error`, and
  closed `effects`. Contract expressions are typed in HIR and generated wrappers apply the configured
  validation mode without weakening provenance or implementation-state checks.
- Scenario fixtures are closed and facade-only. Effectful HTTP observation is available only through
  compiler-owned Linux isolated loopback; unavailable isolation is `unobserved`, never an
  unsandboxed or host-network substitute.
- Semantic coverage is the closed join of Canonical IR clause inventory and runner evidence. Only
  manifest-selected clauses are policy-gated; certification is not a second runtime truth boundary.

### Python Implementations

- A manifest binding names a compatible implementation with `module:function`. A durable accepted
  agent implementation uses `python/_cott_impl/<module path>/<function>.py`; impl methods use the
  corresponding concrete-type path. Do not assume every example uses the same selection mechanism.
- Imports may use the standard library, `cott_runtime`, exact generated `*_types` modules, or a
  uniquely owned distribution selected by `uv.lock`. Relative, star, facade, and dynamic imports are
  rejected where implementation auditing applies.
- Async helpers are allowed only for declared async callables; explicit async impl methods are
  agent-only exact `async def` helpers. Do not use reflection, dynamic compilation, or suppressions.
- Instantiate nominal values through generated type modules and standard ABI values through
  `cott_runtime`. User enum variants are imported as `<Enum>_<Variant>`; `<Enum>` is the union alias.
- Public callers import generated facades only. Direct or dynamic `_cott_impl`/`cott_bindings` imports
  and public re-exports are rejected.

## Important Files

- `Cargo.toml` — Rust package metadata; `src/main.rs` is the binary bridge.
- `src/cli.rs` — command grammar, exit-code mapping, staged publish, and exact verification.
- `src/manifest.rs` / `src/project.rs` — manifest and path trust boundary.
- `src/hir.rs` / `src/ir.rs` — semantic source of truth and canonical serialization.
- `src/python_emit.rs` / `src/python_runtime.rs` — target ABI and managed artifact layout.
- `src/python_verify.rs` / `src/contract_test.rs` — checker, runtime, dependency, and contract evidence.
- `src/agent.rs` / `src/sandbox.rs` — pinned provider adapters and containment.
- `src/transaction.rs` / `src/cli.rs` — journaled mutation, commands, output, and exit codes.

## Runtime/Tooling Preferences

- Use the committed Rust toolchain through Cargo.
- The Python target is CPython `>=3.14.6,<3.15` with BasedPyright `>=1.39.9`; init and lock
  operations use uv `>=0.12.3`.
- Generated runtime code is standard-library-only. Project implementations may use lock-selected
  external distributions whose installed identity and files verify exactly.

## Testing & QA

- Run `cargo fmt --check` and `cargo test` after compiler code changes.
- Test observable contracts: diagnostics, canonical bytes, signatures and wrappers, provenance,
  sandboxing, transactions, exit codes, output-tree preservation, and semantic-coverage evidence.
- Python verification tests use explicit fake pinned tool wrappers where a real CPython 3.14.6
  environment is unavailable.
- Do not copy or assert transient `.venv/`, `.cott/`, or `__pycache__/` content. Managed example
  output changes only when the requested work includes the compiler-owned result.
