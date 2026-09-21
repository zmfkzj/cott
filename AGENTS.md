# Repository Guidelines

## Project Overview

`cott` is a Rust 2024 compiler for language-like typed intent and prompt authoring. A bodyless
`.cott` module is the public contract source. Python, Kotlin, and Dart bindings or accepted agent
implementations are checked projections; generated target facades are the only public import path.
Runtime code does not read authored `.cott` live.

`architecture.md` is the normative implemented v1.0 contract. Preserve the Python closed identity:
package `1.0.0`, Canonical IR schema `8`, generation schema/domain `7`
(`cott.generation.v7`), runtime ABI `7`, contract-test strategy schema `5`, and diagnostics schema
`1`. Kotlin shares package `1.0.0` and Canonical IR `8` but has separate closed generation schema
`1`, domain `cott.kotlin.generation.v1`, and runtime ABI `1`. Dart independently uses generation
schema `1`, domain `cott.dart.generation.v1`, runtime ABI `1`, package `1.0.0` and Canonical IR `8`.
Never put one backend's truth in another backend's fields or accept its record. Do not add legacy
readers, partial profiles, unsandboxed fallbacks, or a second source of truth. When documentation and implementation
source disagree, the source files and closed schema validators are authoritative; update the docs
rather than preserving a contradictory convention.

## Architecture & Data Flow

```text
cott check / fmt / emit / generate / prompt / verify / diff / deploy
  → exactly one closed Python, Kotlin, or Dart target + symlink-safe source discovery
  → lossless CST → AST → complete HIR → Canonical IR
  → intent fingerprints + target binding or scoped agent implementation validation
  → deterministic target facade/runtime/provenance plan
  → prompt inspection, unverified journaled publish, explicit verification, semantic diff, or deployment
```

- `src/manifest.rs` and `src/project.rs` own the single closed manifest parser, exactly-one-target
  selection, paths, and source discovery.
- `src/syntax.rs`, `src/lexer.rs`, `src/parser.rs`, `src/ast.rs`, `src/hir.rs`, and `src/formatter.rs`
  implement the source pipeline; `src/ir.rs` renders and validates canonical JSON.
- `src/intent.rs` fingerprints scoped declaration context (`doc`, applied rules and bases, contract
  constants, types, incoming scenarios, retained generator-rule identifiers) as
  `tools.cott_intent` version 1 hashes.
- `src/binding.rs`, `src/python_emit.rs`, `src/python_runtime.rs`, `src/python_verify.rs`, and
  `src/contract_test.rs` own the unchanged Python generation-7/runtime-7 backend.
- `src/kotlin/{binding,emit,runtime,provenance,pipeline,verify,runner,prompt,generation}.rs` own the
  distinct Kotlin generation-1/runtime-1 module pipeline. Do not reuse Python record fields or
  weaken either validator.
- `src/dart/{binding,emit,types,expressions,runtime,provenance,pipeline,dependencies,verify,runner,prompt,generation}.rs`
  own the independent Dart generation-1/runtime-1 package backend. `src/sandbox/landlock.rs` applies
  Dart runtime filesystem confinement before VM threads; do not move it into already-threaded Dart code.
- `src/agent.rs`, `src/sandbox.rs`, `src/transaction.rs`, and `src/cli.rs` own external execution,
  containment, crash-safe publication, inspection lock, target dispatch, command grammar, and exit
  codes.
- Python deployment selects authored runtime adapters. Kotlin deployment packages the verified
  module and runtime JAR dependencies. `src/cli.rs` and `src/kotlin/pipeline.rs` gate and atomically
  publish new runtime-only directories without rewriting the generated snapshot.
- Generated artifact paths are compiler-owned. Do not hand-edit `generated/`; change the contract or
  the selected implementation source, then use the command that owns the managed output.

## Key Directories

| Path | Purpose |
| --- | --- |
| `src/` | Rust compiler, semantic model, emitter, and CLI |
| `tests/` | Rust integration tests; use public APIs or the built `cott` binary |
| `examples/grammar/` | Six Python declaration and ABI lessons, including `checked-add` binding |
| `examples/simple/` | Three compact Python composition lessons |
| `examples/complex/artifact-pipeline/` | The one pure complex Python curriculum project |
| `examples/complex/process-bar/` | Focused Python full-agent-generation fixture, outside curriculum counts |
| `examples/features/` | Seven focused Python v1.0 feature projects |
| `examples/modular/order-management/` | Python multi-module facade composition |
| `examples/integrations/fastapi-hello/` | Python FastAPI external-type projection |
| `examples/integrations/android-counter/` | Kotlin/JVM Cott module plus standard Gradle-owned Android consumer |
| `examples/kotlin/` | Nineteen Kotlin grammar, composition, feature and modular lessons/fixtures |
| `examples/integrations/flutter-counter/` | Dart Cott package plus standard Flutter Android/web consumer |
| `examples/real/` | Six independent Python real-world generation-first projects |
| `examples/**/src/**/*.cott` | Authoritative example contracts |
| `examples/**/python/cott_bindings/**/*.py` | Selected Python binding sources |
| `examples/**/python/_cott_impl/**/*.py` | Durable accepted Python agent implementation sources |
| `examples/**/kotlin/cott_bindings/**/*.kt` | Selected Kotlin binding sources |
| `examples/**/kotlin/cott_impl/**/*.kt` | Durable accepted Kotlin agent implementation sources |
| `examples/**/dart/cott_bindings/**/*.dart` | Selected private Dart binding sources |
| `examples/**/dart/cott_impl/**/*.dart` | Durable accepted Dart agent implementation sources |
| `architecture.md` | Normative implemented v1.0 contract |

The authored inventory contains 26 Python projects, 20 Kotlin projects and one Dart/Flutter project. The Python set is
grammar 6, simple 3, complex curriculum 1, `process-bar` fixture 1, features 7, modular 1, FastAPI
integration 1, and real-world 6 (`yt-dlp`, `harlequin`, `pgcli`, `posting`, `toolong`,
`frogmouth`). `examples/kotlin/` contains 19 Kotlin lessons/fixtures; `integrations/android-counter`
adds the Kotlin/JVM module and Android consumer. `integrations/flutter-counter` is the Dart module
and standard Flutter consumer. Every project has `cott.toml` and `src/`; its output and implementation layout follows its one selected
target and generation record. Committed `generated/` and agent-owned implementation content are
compiler results. Never treat `.venv/`, `.cott/`, `.gradle/`, `.dart_tool/`, `build/`, Flutter's
`cott_module/` deployment, or `__pycache__/` as managed project content.

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
cott init <path> [--target python|kotlin|dart] [--name <name>] [--no-sync] [--format json]
cott check [<source.cott>] [--project <dir>] [--format json]
cott fmt [--check] [--project <dir>] [--format json]
cott emit ir|python|kotlin|dart [--project <dir>] [--format json]
cott generate [<fully.qualified.callable>] --agent codex|claude|omp --target python|kotlin|dart [-j <jobs>] [--project <dir>] [--format json]
cott prompt <fully.qualified.callable> [--project <dir>] [--format json]
cott verify [--project <dir>] [--format json]
cott deploy [--output <dir>] [--replace] [--project <dir>] [--format json]
cott diff [--baseline <generation.json>] [--exit-code] [--project <dir>] [--format json]
cott lsp
```

`deploy` packages a verified, fully resolved snapshot with passing coverage policy and unchanged
input/managed bytes into `<project>/dist/<name>-<version>/` or `--output` (relative to the calling
working directory). Existing output is never overwritten unless `--replace` is given, which
atomically swaps in a freshly staged tree only when the output is a prior Cott deployment of the
same project (real no-follow directory holding a parseable `generation.json` for this target).
Python deployment preserves runtime code
under `python/`, authored adapters, unchanged `generation.json`, exact `.python-version`, and
hash-pinned production `requirements.txt`. Kotlin deployment preserves `cott-module.jar`, unchanged
`generation.json`, `dependencies.json`, compiler-bundled coroutine `1.8.0`, and verified runtime
`classpath` JARs under `runtime-libs/`; Kotlin stdlib is recorded as required and provided by
Kotlin/Gradle, while `compile_only` JARs are excluded. Dart deployment preserves portable `lib/`,
compiler-owned pubspec, unchanged generation/dependency records and the authenticated runtime
vendor closure, not native kernel or runner output. All targets exclude contracts, the original
generated layout, tests, authoring implementation copies, and caches. Deploy never generates,
re-verifies, runs an agent, or infers application resources.

`emit` and `generate` publish through the project transaction and always leave
`current.verified = false`; only explicit `verify` certifies a snapshot. Target emit never invokes
an agent. Unresolved callables are omitted from the callable facade. `emit ir` rewrites only IR
scope and `generation.json`; non-IR managed hashes stay trusted recorded values and cannot bless
unrelated on-disk edits. Pending unresolved agent sources with authentic `AgentRun` provenance keep
their old bytes across repeated emit and checkpoint until regeneration. Manifest-owned bindings
are excluded from intent regeneration. Same-v7 fallback derivation applies only to Python records;
Kotlin and Dart remain separate closed generation schema 1 targets. Missing manifest/rule evidence and source/path/hash
drift invalidate conservatively. `generate` invokes the selected agent only for eligible unresolved
callables and freezes all advertised initial prompts before accepting any wave candidate.

`cott prompt` renders that same initial snapshot without a provider or target compiler/checker.
JSON is `{symbol,intent_hash,prompt_hash,generation_required,context,prompt}`; `prompt_hash` covers
only the initial bytes. The requested write path is `implementation.py` for Python,
`implementation.kt` for Kotlin and `implementation.dart` for Dart. Context is the scoped transitive
declaration closure, including explicit references, `constant_ref`, applied rules/bases, relevant scenarios, and scoped
`cott-domain` directives. Prompt sections stay separated: authority, current intent, formal
declarations, project rules, references, target output rules, and feedback. Formal source is
authoritative; rules and references never override it.

`verify` rebuilds and checks the complete selected target without a result cache, refuses unresolved
work, and publishes certification only after real target verification. Kotlin verify uses
kotlinc `>=2.2.10`, JDK `>=17`, JVM target 17, compiler-distribution stdlib and coroutine `1.8.0`,
then compiles `library/cott-module.jar` and executes the bounded runner in the existing sandbox.
For Kotlin and Dart, `current.verified = true` requires `current == last_verified`. Emit, generate, and
actual format edits retain history but invalidate current certification. An already deployed
snapshot keeps its old contract until a later deployment.

Kotlin/JVM erases ordinary type parameters. Associated projections become additional bounded Kotlin
type parameters, with concrete impl assignments resolved before overrides; never add reflection or
phantom associated wrappers. Free const generics require `_cott_const_*: CottConst` value witnesses.
Runtime evidence must not claim arbitrary erased `T` or abstract associated values were reified:
unsupported bounded candidates remain unobserved/unknown.

`generate` has three direct adapters: `codex`, direct `claude`, and `omp`; selecting a Claude
model inside OMP is still `omp`, never the direct Claude adapter. Before generation, direct Claude's
native-entrypoint check rejects npm `cli.js` entrypoints and Node shebangs, then runs exactly
`claude --version` with no credentials (including `ANTHROPIC_API_KEY`) and network disabled. The
probe must finish without a timeout at status `0`; stdout must be exactly one strict SemVer token
`>=2.1.89`. Generation is separate: official native Claude Code runs exactly `claude --bare --print --input-format text --output-format json --permission-mode dontAsk --tools Read,Write --allowedTools Read,Write --disallowedTools Bash,Edit,Glob,Grep,WebFetch,WebSearch,Task,mcp__* --no-session-persistence`. Send the exact UTF-8 prompt through stdin in the isolated workspace; use common Cott runtime variables plus an existing `ANTHROPIC_API_KEY` only, always set `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1`, `DISABLE_TELEMETRY=1`, and `DISABLE_ERROR_REPORTING=1`, and never forward OAuth/auth-token/base-url/cloud/provider/customization variables. Accept stdout only as JSON `{type:"result", subtype:"success", is_error:false, result:<string>}`; otherwise fail closed. Generation provider egress may remain available, but no network-capable Claude tools are exposed; the normative environment and result contract is architecture §17.2.1.

## Code Conventions & Common Patterns

### Rust

- Format with `cargo fmt`; remain dependency-light and reuse stdlib before adding crates.
- Prefer deterministic structures (`BTreeMap`/`BTreeSet`) for externally visible ordering and
  artifact plans. Preserve source/module/declaration order where the semantic model owns it.
- Return structured, path-attached diagnostics instead of panicking for user input.
- Treat filesystem paths and output trees as trust boundaries: reject symlinks, unsafe relative paths,
  and partial publication. Keep output staging/publishing in `src/cli.rs`.
- Keep public data types simple (`Clone`, `Debug`, `Eq`, `PartialEq`) when tests need observable values.

### Cott v1.0

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

- Each `examples/real/` project is generation-first with project API `0.1.0`: adapters use public
  facades only, and its README H1 is the canonical upstream URL. After the generation phase,
  commit its verified generated artifacts. Manifest bindings are limited to the essential host
  boundaries: yt-dlp transfer, Harlequin REPL, Posting HTTP, and Frogmouth document loading.

### Kotlin Implementations and Android Boundary

- `[target.kotlin.implementations]` maps a Cott callable to a Kotlin package/function FQN under
  `target.kotlin.source`. Durable agent files use
  `<target.kotlin.source>/cott_impl/<module path>/<function>.kt`; methods include the concrete-type
  path.
- Audit exact package, one canonical internal top-level function, signature, owner, source/runtime
  origin, content hash, intent fingerprint, and permitted private helpers. Unimplemented callables
  and authenticated intent-stale agent sources remain unresolved; unrecorded, moved, tampered, or
  manifest-shadowed agent files fail closed. Never refresh trust from old provenance.
- Public consumers import the generated Cott package only. Direct `cott_bindings`/`cott_impl`
  imports or public re-exports are boundary violations.
- `target.kotlin.classpath` and `target.kotlin.compile_only` are disjoint normalized
  project-relative JAR lists and hashed compiler inputs. Only `classpath` is a deployable runtime
  dependency.
- The Android counter uses Android Gradle plugin `9.0.1` (bundled Kotlin `2.2.10`), SDK `36`,
  min SDK `26`, JVM 17, and its
  pinned Gradle `9.1.0` wrapper with distribution SHA-256
  `a17ddd85a26b6a7f5ddb71ff8b05fc5104c0202c6e64782429790c933686c806`; set `COTT_BIN` to an
  absolute in-tree compiler path during development.
- Cott owns the Cott module's compilation, contract verification, and deployment. Standard
  Gradle/Android owns UI, `AndroidManifest.xml`, resources, dependency resolution, DEX, APK/AAB,
  signing, installation, and device lifecycle. Do not claim Cott scaffolds an Android app or runs
  Python on-device.

### Dart Implementations and Flutter Boundary

- Dart SDK is `>=3.13.3,<4.0.0`. A Dart project name is its lowercase snake_case package name.
  `[target.dart]` owns source/generated/sdk/runtime_validation, optional paired pubspec/lockfile,
  private implementation selectors and external type projections. Exactly one target is selected.
- A manifest implementation is `source-relative/file.dart:_privateFunction`; accepted agents use
  `<target.dart.source>/cott_impl/<module>/<function>.dart` and the exact signature from `cott prompt`.
  Compiler-owned private names use `_cott_`; only exact declared witness/function identifiers are
  accepted. Original source hashes are distinct from transformed managed private-part hashes.
- Public consumers import `package:<name>/modules/<module>.dart`. Implementations are Dart-library
  private parts; stateful methods share their owner-private library. Do not expose raw state/seals,
  public unchecked setters, or private implementation import paths.
- I64/U64 use `BigInt`; small integer bounds and F32 rounding remain exact. Generic/associated
  distinctions use explicit `CottType<T>` witnesses and checked variance views; consts use
  `CottConst`. Never substitute `Any`, Dart covariance, or runtimeType text for canonical evidence.
- Cancellation is cooperative. Structured tasks and exact live guard/mutation leases are explicit;
  inherited Zone data never grants task ownership and arbitrary Futures are not preempted.
- Freeze manifest, rules, Cott/Dart sources and pub metadata once. Missing authentic agent source
  stays unresolved; moved/tampered/unrecorded source fails. Pending successful-provider source may
  remain for repair, but emit/generate never certify or refresh stale intent by syntax alone.
- Verify uses real offline Dart pub/analyzer/kernel tools and authenticated facade evidence.
  Linux bubblewrap and Landlock ABI >=3 are required; Landlock is installed before all VM threads.
  The evidence key is a fresh stdin-only secret, never source/argv/env/metadata.
- Hosted dependencies require locked original archives in
  `PUB_CACHE/hosted-archives/<registry-key>/<name>-<version>.tar.gz`. Check compressed SHA256,
  safe bounded members and exact extracted bytes; mutable cache hash sidecars are not authority.
  Verification never silently downloads missing archives. Frozen path dependencies stay in-project.
- Deploy portable `lib/`, compiler-owned pubspec, unchanged generation record/dependency metadata
  and exact runtime vendor closure, not kernel/runner/SDK/contracts/caches or inferred app assets.
  Flutter owns UI, plugins, platform resources, APK/AAB and web compilation.
- `examples/integrations/flutter-counter` uses Flutter 3.47.4/Dart 3.13.3; its standard Android
  scaffold uses SDK 36, AGP 9.1.0, Kotlin 2.4.0 and Gradle 9.3.1 with a distribution SHA256 pin.
  Its `tool/setup.dart` refuses existing deployment output and invokes real emit/verify/deploy.

## Important Files

- `Cargo.toml` — Rust package metadata; `src/main.rs` is the binary bridge.
- `src/cli.rs` — command grammar, exactly-one-target dispatch, exit codes, and Python publication.
- `src/manifest.rs` / `src/project.rs` — shared manifest and path trust boundary.
- `src/hir.rs` / `src/ir.rs` — semantic source of truth and canonical serialization.
- `src/intent.rs` — scoped intent context and `tools.cott_intent` version 1 fingerprints.
- `src/python_emit.rs` / `src/python_runtime.rs` / `src/python_verify.rs` — unchanged Python ABI.
- `src/kotlin/` — Kotlin ABI, binding, emission, provenance, prompt/generation, verification,
  runner, publication, diff, init, and deployment.
- `src/agent.rs` / `src/sandbox.rs` — pinned provider adapters and containment.
- `src/transaction.rs` — journaled mutation and inspection lock.

## Runtime/Tooling Preferences

- Use the committed Rust toolchain through Cargo.
- The Python target is CPython `>=3.14.6,<3.15` with BasedPyright `>=1.39.9`; Python init and lock
  operations use uv `>=0.12.3`.
- The Kotlin target is kotlinc `>=2.2.10`, JDK `>=17`, JVM 17, compiler-matched stdlib, and the
  exact compiler-distribution `kotlinx-coroutines-core-jvm` `1.8.0`.
- Dart native regressions use `COTT_DART` as an absolute SDK executable path. The portable generated
  Dart runtime is standard-library-only; pinned crypto sources are compiler-only runner support.
- Python generated runtime code is standard-library-only. Kotlin generated runtime code additionally
  requires the recorded coroutine JAR. Project dependencies remain target-manifest inputs.

## Testing & QA

- Run `cargo fmt --check` and `cargo test` after compiler code changes.
- Test observable contracts: diagnostics, canonical bytes, signatures and wrappers, provenance,
  sandboxing, transactions, target dispatch, output-tree preservation, and semantic coverage.
- Python verification tests use explicit fake pinned tool wrappers where a real CPython 3.14.6
  environment is unavailable. Kotlin verification tests use controlled Kotlin/JDK toolchains; real
  Android integration remains a standard Gradle consumer check, distinct from Cott module verify.
- Dart native tests are explicitly COTT_DART-gated; execute ignored runtime, native consumer,
  verifier, scenario and dependency tests with the real SDK. Flutter browser/APK verification is
  distinct from Cott module certification.
- Do not copy or assert transient `.venv/`, `.cott/`, `.gradle/`, `.dart_tool/`, `build/`, or `__pycache__/`
  content. Managed example output changes only when the requested work includes the compiler-owned
  result.
