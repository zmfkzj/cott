# Repository Guidelines

## Project Overview

`cott` is a Rust 2024 compiler for a static, contract-first DSL. A `.cott` module defines public
shapes; a durable typed Python binding supplies implementation; generated Python facades are the
only public import path.

`architecture.md` is the authoritative v0.1 design. The committed implementation is a deliberately
smaller Profile-P slice: parsing, constrained semantic analysis, canonical IR, binding validation,
Python emission, and exact generated-tree verification. Do not present unimplemented design commands
as available.

## Architecture & Data Flow

```text
cott emit python / verify
  → project manifest + source discovery
  → parser → constrained semantic analyzer → canonical IR
  → durable Python binding validation + SHA-256 identity
  → in-memory Python artifact plan
  → staged publish, or byte-for-byte verification
```

- `src/project.rs` owns the closed `cott.toml` parser, project paths, and symlink-safe source discovery.
- `src/parser.rs`, `src/lexer.rs`, `src/ast.rs`, and `src/semantic.rs` turn source into the constrained
  semantic model; `src/ir.rs` renders deterministic canonical JSON.
- `src/binding.rs` accepts exactly one regular UTF-8 implementation per public function and records its
  bytes plus SHA-256 identity.
- `src/python_runtime.rs` renders the stdlib-only runtime. `src/python_emit.rs` produces the complete
  deterministic artifact map. `src/cli.rs` owns CLI grammar, staging publication, and verification.
- Generated artifact paths are compiler-owned. Never hand-edit `generated/`; modify `.cott` or
  `python/_cott_impl/**/run.py`, then re-emit.

## Key Directories

| Path | Purpose |
| --- | --- |
| `src/` | Rust compiler, semantic model, emitter, and CLI |
| `tests/` | Rust integration tests; use public APIs or the built `cott` binary |
| `examples/grammar/` | Ten standalone declaration/ABI examples |
| `examples/simple/` | Ten standalone deterministic programs |
| `examples/complex/` | Ten standalone composed-data examples |
| `examples/**/src/curriculum/*.cott` | Authoritative example contracts |
| `examples/**/python/_cott_impl/curriculum/*/run.py` | Durable example bindings |
| `architecture.md` | Future/full design; not a claim of implemented behavior |

Each example is an independent project with `cott.toml`, `src/`, and `python/_cott_impl/`.

## Development Commands

```bash
cargo fmt --check
cargo test
cargo run -- --help
cargo run -- emit python --project examples/grammar/boolean-identity
cargo run -- verify --project examples/grammar/boolean-identity
cd examples/grammar/boolean-identity/generated/python
python3 -m curriculum.boolean_identity
```

The only implemented command forms are:

```text
cott emit python [--project <dir>]
cott verify [--project <dir>]
```

`emit python` builds a complete plan before replacing `generated/`. `verify` rebuilds the plan and
fails on missing, extra, or changed managed files; it does not rewrite them. `init`, `check`, `fmt`,
`emit ir`, `generate`, and `diff` remain unimplemented.

## Code Conventions & Common Patterns

### Rust

- Format with `cargo fmt`; stay dependency-light. The only current dependency is `sha2`.
- Prefer deterministic structures (`BTreeMap`/`BTreeSet`) for externally visible ordering and artifact
  plans. Preserve source/module/declaration order where the semantic model owns it.
- Return structured, path-attached diagnostics instead of panicking for user input.
- Treat filesystem paths and output trees as trust boundaries: reject symlinks, unsafe relative paths,
  and partial publication. Keep output staging/publishing in `src/cli.rs`.
- Keep public data types simple (`Clone`, `Debug`, `Eq`, `PartialEq`) when tests need observable values.

### Cott Profile-P

- A source file has one module; the module name matches its source-relative path. Use two segments for
  examples, e.g. `src/curriculum/boolean_identity.cott` → `module curriculum.boolean_identity`.
- The current semantic profile supports aliases, newtypes without refinements, structs without defaults,
  enums, literal constants, `Option`, `Result`, and **signature-only zero-argument** public functions.
- It currently rejects function parameters, clauses (`requires`, `ensures`, `error`, `effects`), traits,
  user generics, newtype refinements, and field defaults. Do not fake support in examples or docs.
- Use explicit types. `Option[T]` represents absence and `Result[T, ErrorEnum]` represents expected
  failure. Error types in `Result` must be local enum declarations.

### Python Bindings

- A binding lives at `python/_cott_impl/<module path>/<function>.py` and defines exactly one annotated
  top-level `def function() -> ...:`. It must end in exactly one newline.
- Imports may use the standard library, `cott_runtime`, or that project’s exact generated
  `<module>_types` module. Relative/star/project-local facade/external imports are rejected.
- Do not use placeholders (`pass`, `...`, `NotImplementedError`), async, dynamic import, `eval`, `exec`,
  `compile`, or agent operations in bindings.
- Instantiate nominal structs/newtypes/enums through generated `*_types` imports; return `Ok`, `Err`,
  `Some`, `Nothing`, or `UNIT` from `cott_runtime` where the contract requires them.

## Important Files

- `Cargo.toml` — Rust package metadata; `src/main.rs` is the binary bridge.
- `src/cli.rs` — supported command grammar, exit-code mapping, staged publish, exact verification.
- `src/project.rs` — closed manifest and source-discovery contract.
- `src/semantic.rs` — Profile-P acceptance/rejection rules.
- `src/python_emit.rs` and `src/python_runtime.rs` — generated Python ABI and artifact layout.
- `README.md` — runnable examples, current limits, and observed outputs.

## Runtime/Tooling Preferences

- Use the committed Rust toolchain through Cargo; do not add dependencies for parsing, CLI handling, or
  filesystem traversal when the standard library suffices.
- Generated Python uses only the standard library. The compiler does not install, choose, or manage a
  Python interpreter.
- `architecture.md` specifies a future CPython 3.14/`uv`/BasedPyright workflow. Those tools are not part
  of the current implementation and must not be made implicit in tests or commands.

## Testing & QA

- Run `cargo fmt --check` and `cargo test` after code changes.
- Add tests for externally observable contracts: diagnostics, exact artifact paths/bytes, command exit
  codes, output-tree preservation, and generated-runtime behavior.
- `tests/cli.rs` has a conditional `python3` smoke test for a generated module; do not make Rust tests
  require a Python installation when the behavior can be covered without it.
- For example changes, emit, verify, and run the entry module with a supplied Python:

  ```bash
  cargo run -- emit python --project examples/<category>/<slug>
  cargo run -- verify --project examples/<category>/<slug>
  (cd examples/<category>/<slug>/generated/python && python3 -m curriculum.<slug>)
  ```

  Remove locally generated example `generated/` directories after smoke testing unless managed output is
  explicitly part of the requested change.
