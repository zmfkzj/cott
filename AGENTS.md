# Repository Guidelines

## Project Overview

`cott` is a Rust 2024 compiler for a static, contract-first DSL. A `.cott` module defines public
shapes; a durable typed Python binding supplies implementation; generated Python facades are the
only public import path.

`architecture.md` is the authoritative and implemented v0.1 contract. Do not add behavior outside
that closed contract or present a partial compatibility profile as an alternate source of truth.

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
  `src/contract_test.rs` own the target ABI and verification pipeline.
- `src/agent.rs`, `src/sandbox.rs`, `src/transaction.rs`, and `src/cli.rs` own external execution,
  crash-safe publication, command grammar, and exit codes.
- Generated artifact paths are compiler-owned. Never hand-edit `generated/`; modify `.cott` or
  `python/_cott_impl/**/run.py`, then re-emit.

## Key Directories

| Path | Purpose |
| --- | --- |
| `src/` | Rust compiler, semantic model, emitter, and CLI |
| `tests/` | Rust integration tests; use public APIs or the built `cott` binary |
| `examples/grammar/` | Ten standalone declaration/ABI examples |
| `examples/simple/` | Ten standalone deterministic programs |
| `examples/complex/` | Eleven standalone composed-data examples, including unresolved `process-bar` generation fixture |
| `examples/**/src/curriculum/*.cott` | Authoritative example contracts |
| `examples/**/python/_cott_impl/curriculum/*/run.py` | Durable example bindings |
| `architecture.md` | Normative implemented v0.1 contract |

Each example is an independent project with `cott.toml`, `src/`, and `python/_cott_impl/`.

## Development Commands

```bash
cargo fmt --check
cargo test
cargo run -- --help
cargo run -- check --project examples/grammar/boolean-identity
cargo run -- emit ir --project examples/grammar/boolean-identity
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
```

`emit` and `generate` publish through the project transaction and leave `current.verified = false`.
`verify` rebuilds and checks the complete target without a cache, then updates only provenance.

## Code Conventions & Common Patterns

### Rust

- Format with `cargo fmt`; remain dependency-light and reuse stdlib before adding crates.
- Prefer deterministic structures (`BTreeMap`/`BTreeSet`) for externally visible ordering and artifact
  plans. Preserve source/module/declaration order where the semantic model owns it.
- Return structured, path-attached diagnostics instead of panicking for user input.
- Treat filesystem paths and output trees as trust boundaries: reject symlinks, unsafe relative paths,
  and partial publication. Keep output staging/publishing in `src/cli.rs`.
- Keep public data types simple (`Clone`, `Debug`, `Eq`, `PartialEq`) when tests need observable values.

### Cott v0.1

- A source file has one module whose name injectively matches its source-relative path.
- Supported types include fixed-width numeric types, `Path`, `Unit`, `Never`, `JsonValue`,
  constrained `Opaque`, nominal and generic user types, and closed standard containers.
- Supported declarations include aliases, refined newtypes, immutable structs with constant defaults,
  payload enums, structural traits, typed constants, and public function signatures.
- Functions support parameters, generics and bounds, `requires`, `ensures`, conditional `error`, and
  the closed `effects` vocabulary. Contract expressions are typed in HIR and enforced by generated
  wrappers according to `runtime_validation`.

### Python Bindings

- A manifest binding names an implementation with `module:function`; generated implementations live
  at `python/_cott_impl/<module path>/<function>.py`. Each file defines exactly one fully annotated
  top-level function and ends in one newline.
- Imports may use the standard library, `cott_runtime`, exact generated `*_types` modules, or a
  uniquely owned distribution selected by `uv.lock`. Relative, star, facade, and dynamic imports are
  rejected.
- Do not use placeholders, async, reflection, dynamic compilation, suppressions, or agent operations.
- Instantiate nominal values through generated type modules and standard ABI values through
  `cott_runtime`.
- User enum variants are imported as `<Enum>_<Variant>`; the `<Enum>` name is the union alias.

## Important Files

- `Cargo.toml` — Rust package metadata; `src/main.rs` is the binary bridge.
- `src/cli.rs` — supported command grammar, exit-code mapping, staged publish, exact verification.
- `src/manifest.rs` / `src/project.rs` — manifest and path trust boundary.
- `src/hir.rs` / `src/ir.rs` — semantic source of truth and canonical serialization.
- `src/python_emit.rs` / `src/python_runtime.rs` — target ABI and managed artifact layout.
- `src/python_verify.rs` / `src/contract_test.rs` — checker, runtime, dependency, and contract evidence.
- `src/agent.rs` / `src/sandbox.rs` — pinned provider adapters and containment.
- `src/transaction.rs` / `src/cli.rs` — journaled mutation, commands, output, and exit codes.

## Runtime/Tooling Preferences

- Use the committed Rust toolchain through Cargo.
- The Python target is CPython >=3.14.6,<3.15 with BasedPyright >=1.39.9; init and lock operations use uv 0.12.3 or later.
- Generated runtime code is standard-library-only. Project implementations may use lock-selected
  external distributions whose installed identity and files verify exactly.

## Testing & QA

- Run `cargo fmt --check` and `cargo test` after code changes.
- Test observable contracts: diagnostics, canonical bytes, signatures and wrappers, provenance,
  sandboxing, transactions, exit codes, and output-tree preservation.
- Python verification tests use explicit fake pinned tool wrappers where a real CPython 3.14.6
  environment is unavailable.
- Remove locally generated example `generated/` and `.cott/` state after smoke testing unless the
  request explicitly includes managed output.
