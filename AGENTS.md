# Repository Guidelines

## Project Overview

`cott` is a Rust 2024 compiler for language-like typed intent and prompt authoring. A bodyless
`.cott` module is the public contract source. Python, Kotlin, and Dart bindings or accepted agent
implementations are checked projections; generated target facades are the only public import path.
Runtime code does not read authored `.cott` live.

`architecture.md` is the normative implemented v1.0 contract. Package `1.0.0`, Canonical IR schema
`8`, contract-test strategy schema `5`, and diagnostics schema `1` remain unchanged.
Python uses generation schema `8`, domain `cott.generation.v8`, and runtime ABI `7`.
Kotlin uses generation schema `2`, domain `cott.kotlin.generation.v2`, and runtime ABI `1`.
Dart uses generation schema `2`, domain `cott.dart.generation.v2`, and runtime ABI `2`.
Never put one backend's truth in another backend's fields or accept its record. Do not add legacy
readers, partial profiles, unsandboxed fallbacks, or a second source of truth. When documentation and implementation
source disagree, the source files and closed schema validators are authoritative; update the docs
rather than preserving a contradictory convention.
Keep the existing current/last-verified lifecycle and verification equality invariant, but use the
closed wire envelope `{schema_version,current,last_verified,snapshots}`. `current` is a content
digest, `last_verified` is a content digest or null, and `snapshots` maps exactly the one or two
reachable digests to full snapshot objects. Equal references store one blob; reject unused,
dangling, tampered, or old-format records. JSON callers read `.snapshots[.current].verified`.
Snapshot digests cover full evidence, `AgentRun`, and verification state. `generation_id` separately
excludes the existing volatile fields and uses the normalized target-domain identity wrapper.
Both use the `cott.snapshot.v1` plus NUL structural SHA-256 digest with tagged length-delimited
values and f64 IEEE bits, not raw JSON byte hashing. File content hashes remain raw-byte SHA-256.
Records are self-contained for relocation, saved baselines, and deployment; no external snapshot
cache or sidecars. New generated output requires the new runtime loader and deployment record.
Normal readers reject old schemas. The bounded one-time compiler-linked transaction conversion
preserves source/AgentRun evidence, clears certification, then requires real emit and verify.
It is not a public migration command; never hand-bless source hashes or carry old certification
across a schema/ABI cutover.

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
  `src/contract_test.rs` own the Python generation-8/runtime-7 backend.
- `src/kotlin/{binding,emit,runtime,provenance,pipeline,verify,runner,prompt,generation}.rs` own the
  distinct Kotlin generation-2/runtime-1 module pipeline. Do not reuse Python record fields or
  weaken either validator.
- `src/dart/{binding,emit,types,expressions,runtime,provenance,pipeline,dependencies,verify,runner,prompt,generation}.rs`
  own the independent Dart generation-2/runtime-2 package backend. `src/sandbox/landlock.rs` applies
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
| `examples/grammar/checked-add/python/cott_bindings/**/*.py` | The sole selected Python binding source (binding-syntax lesson) |
| `examples/**/python/_cott_impl/**/*.py` | Durable accepted Python agent implementation sources |
| `examples/**/kotlin/cott_impl/**/*.kt` | Durable accepted Kotlin agent implementation sources |
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
cott generate [<fully.qualified.callable>] --agent codex|claude|omp [--model <model>] --target python|kotlin|dart [-j <jobs>] [--project <dir>] [--format json]
cott prompt <fully.qualified.callable> [--project <dir>] [--format json]
cott verify [--project <dir>] [--format json]
cott requirements [--project <dir>] [--format json]
cott deploy [--output <dir>] [--replace] [--project <dir>] [--format json]
cott diff [--baseline <generation.json>] [--exit-code] [--project <dir>] [--format json]
cott lsp
```

`deploy` packages a verified, fully resolved snapshot with passing coverage policy and unchanged
input/managed bytes into `<project>/dist/<name>-<version>/` or `--output` (relative to the calling
working directory). Existing output is never overwritten unless `--replace` is given. Replacement
requires a real no-follow prior Cott deployment with this target's closed record and the same
project identity; Python additionally hash-verifies the deployed runtime identity. A parseable
`generation.json` alone is insufficient. Swap complete sibling trees with real `RENAME_EXCHANGE`,
not two `RENAME_NOREPLACE` moves with an output-missing gap. Durable journal/marker ownership
proof and no-follow locking govern recovery. Never roll back to a partially deleted old tree
after commit: post-commit cleanup failure leaves the NEW deployment usable and retains recoverable
state. Unsupported filesystem capabilities fail closed, without an unsafe fallback. Continuous
pathname visibility is not a multi-open reader snapshot guarantee.
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
`.snapshots[.current].verified = false` in the record; only explicit `verify` certifies a snapshot. Target emit never invokes
an agent. Unresolved callables are omitted from the callable facade. `emit ir` rewrites only IR
scope and `generation.json`; non-IR managed hashes stay trusted recorded values and cannot bless
unrelated on-disk edits. Pending unresolved agent sources with authentic `AgentRun` provenance keep
their old bytes across repeated emit and checkpoint until regeneration. Manifest-owned bindings
are excluded from intent regeneration. Missing intent metadata fallback applies only to valid
current-schema Python records; Kotlin and Dart have separate generation schema 2 contracts. Missing manifest/rule evidence and source/path/hash
drift invalidate conservatively. `generate` invokes the selected agent only for eligible unresolved
callables and freezes all advertised initial prompts before accepting any wave candidate.

`cott prompt` renders that same initial snapshot without a provider or target compiler/checker.
JSON is `{symbol,intent_hash,prompt_hash,generation_required,context,prompt}`; `prompt_hash` covers
only the initial bytes. The requested write path is `implementation.py` for Python,
`implementation.kt` for Kotlin and `implementation.dart` for Dart. Context is the scoped transitive
declaration closure, including explicit references, `constant_ref`, applied rules/bases, relevant scenarios, and scoped
`cott-domain` directives. Prompt sections stay separated: authority, current intent, formal
declarations, project rules, references, target output rules, and feedback. Formal declarations
are authoritative; rules and references never override them. `FORMAL DECLARATIONS` projects only
the selected resolved canonical context, without source rereads, span slicing, or broad
re-expansion. Expression/pattern strings use unambiguous `kind(field=value,...)` constructors,
nested constructors, ordered lists and JSON-quoted strings, not formatted Cott source. Preserve
resolved types, fully qualified symbols/bindings, variant identities, exact integer values and
IEEE float bits, operators and guard binding scopes. Coordinates are diagnostic only; omit
spans/source_order/doc from this view while keeping clause identities/order. CURRENT INTENT owns
doc. The `context` and intent fingerprint contracts remain unchanged.

`verify` rebuilds and checks the complete selected target without a result cache, refuses unresolved
work, and publishes certification only after real target verification. Kotlin verify uses
kotlinc `>=2.2.10`, JDK `>=17`, JVM target 17, compiler-distribution stdlib and coroutine `1.8.0`,
then compiles `library/cott-module.jar` and executes the bounded runner in the existing sandbox.
For Kotlin and Dart, `.snapshots[.current].verified = true` requires `current == last_verified`. Emit, generate, and
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
- Free functions may opt into `errors complete` after ensures and before errors. This mode
  rejects bare error allowances and requires `Ok` when no conditional error applies; functions
  without it retain their existing meaning. It is an obligation, not a termination proof.
  The graph predicates and fixed Unicode White_Space semantics are defined in architecture §10.4.1.
- An input-scrutinee guard such as `ensures key matches Kind.X => result == ...` retains the
  return-value `result` in its condition, alongside clause-local pattern bindings. In contrast,
  `ensures result matches Pattern => condition` and its shorthand `ensures Pattern => condition`
  expose pattern bindings, not `result`, to the condition. Bindings never leak into later clauses,
  and guards do not introduce return-value `result` into `requires`, refinements, or invariants.
- `ensures table key:` has indented rows such as `Kind.Local => "local"`. Require exhaustive,
  unique zero-payload enum variants and lower each row to a guarded result-equality obligation,
  never an executable implementation. `ensures preserves result from mark except value, image_bytes`
  requires the same concrete struct and generic arguments, preserving nonexcluded fields in
  canonical field order. Reject unknown/duplicate exclusions and excluding every field.
  `table`, `preserves`, `from`, `except` are contextual, not globally reserved.
- Ordinary acyclic rules may precede either sugar in a callable, but sugar inside rule declarations
  is rejected for lack of a callable-local concrete environment. Rules remain restricted,
  terminating clause helpers; arbitrary calls and recursion are unavailable. Preserve implication
  versus match-guard disambiguation, including formatter-required parentheses.
- Scenario fixtures are closed and facade-only. Effectful HTTP observation is available only through
  compiler-owned Linux isolated loopback; unavailable isolation is `unobserved`, never an
  unsandboxed or host-network substitute.
- Scenario arguments, `data` and assertions accept closed nested canonical struct/enum/container
  values. Module-local `data name: Type = VALUE` is reusable test data; scenario-local data
  evaluates exactly once. `assert value matches Pattern => condition` must match and keeps
  bindings local to that assertion. No arbitrary calls or public builder helpers are introduced.
- `requirement NAME for callable:` needs only normative `text`. Optional `checked_by` links name
  local scenarios or assertion ordinals; `assumption` and `waiver` remain separate and never
  convert failed or missing evidence into success. Requirements enter CURRENT INTENT without
  demoting existing doc. `cott requirements` is a read-only, version-1 report tied to the current
  target snapshot after normal freshness checks. Observed linked checks do not prove the prose.
  K101 remains advisory. External program regression results are not Cott scenario evidence.
- Semantic coverage is the closed join of Canonical IR clause inventory and runner evidence. Only
  manifest-selected clauses are policy-gated; certification is not a second runtime truth boundary.
- Evidence comes from actual emitted predicate observations in the exact callable/invocation/method
  scope: evaluate once and only after the guard matches. No runner post-hoc reevaluation/guessing
  and no "previously observed" fallback may upgrade missing or unknown evidence. Python's
  compiler-private observer tokens/sinks cannot be supplied by implementations; target ABI and
  record/evidence schemas stay unchanged. Deterministic bounded literal/boundary/candidate
  breadth-first exploration improves positive reachability, not full-function correctness.
  Preserve honest unknown/unobserved statuses and explicit policy allowances.

### Python Implementations

- A manifest binding names a compatible implementation with `module:function`. A durable accepted
  agent implementation uses `python/_cott_impl/<module path>/<function>.py`; impl methods use the
  corresponding concrete-type path. Do not assume every example uses the same selection mechanism.
  Only `grammar/checked-add` selects a manifest binding. Never introduce `[target.*.implementations]`
  mappings or `cott_bindings/` sources to work around a generation, run, or verification failure;
  fix the contract, generator rules, or toolchain instead.
- Imports may use the standard library, `cott_runtime`, exact generated `*_types` modules,
  scoped generated callable facades, or a uniquely owned distribution selected by `uv.lock`.
  Facade calls must name declarations in the selected context and be covered by the caller's
  effects; do not alias or pass Cott callables as values. Relative, star, private implementation,
  and dynamic imports are rejected where implementation auditing applies.
- Async helpers are allowed only for declared async callables; explicit async impl methods are
  agent-only exact `async def` helpers. Do not use reflection, dynamic compilation, or suppressions.
- Instantiate nominal values through generated type modules and standard ABI values through
  `cott_runtime`. User enum variants are imported as `<Enum>_<Variant>`; `<Enum>` is the union alias.
- Public callers import generated facades only. Direct or dynamic `_cott_impl`/`cott_bindings` imports
  and public re-exports are rejected.

- Each `examples/real/` project is generation-first with project API `0.1.0`: adapters use public
  facades only, and its README H1 is the canonical upstream URL. After the generation phase,
  commit its verified generated artifacts. Real projects select no manifest bindings: host
  boundaries such as yt-dlp transfer, Harlequin REPL, Posting HTTP, and Frogmouth document loading
  are agent-generated like every other callable.

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
- Private type-module aliases are `_cott_t_` plus segments with `_` escaped as `_u`, joined by
  `__`: `foo_bar.baz` becomes `_cott_t_foo_ubar__baz`. Canonical symbols, public facade imports and
  hash identity rules are unchanged by alias spelling. This alias cutover is separate from the
  native-enum runtime ABI 2 change; neither supplies compatibility aliases or an automatic old-source reader.
  Manifest-owned sources may update aliases. Authenticated agent-owned bytes require legitimate
  regeneration, not cosmetic edits followed by blessing; preserve source/record hash checks.
- I64/U64 use `BigInt`; small integer bounds and F32 rounding remain exact. Generic/associated
  distinctions use explicit `CottType<T>` witnesses and checked variance views; consts use
  `CottConst`. Never substitute `Any`, Dart covariance, or runtimeType text for canonical evidence.
- Every immutable struct exposes named extension `<Struct>$CopyWith` and `value.copyWith(...)`;
  explicit `<Struct>$CopyWith(value).copyWith(...)` is also available. An extension adds no
  instance-member implementation requirement to checked generic view implementers. Cott fields
  must be snake_case; do not invent a migration for an invalid source field named `copyWith`.
  Omitted fields keep exact stored values, not constructor defaults; explicit overrides including
  `Nothing`, zero, false and canonical-Any null are distinct from omission. Forward stored
  witnesses and rerun the canonical constructor/invariants.
- `optionFromNullable<T extends Object>`/`optionToNullable<T extends Object>` accept only
  nonnullable payload types; never conflate `Some(null)` with `Nothing`. General `Option[Any]`
  still uses explicit variants. `CottBytes.readOnlyView` is a zero-copy read-only `List<int>`;
  `toUint8List()` stays a mutable defensive copy.
- Native Dart enums apply to a whole nonempty enum with no type/const generic parameters and no
  variant payloads. Preserve exact Cott member spelling: `Kind.Local`, never `KindLocal()` or
  `Kind.Local()`. Public callers and implementations use native `.values`, `.name`, `.index` and
  exhaustive constant patterns such as `switch (kind) { Kind.Local => ..., Kind.Remote => ... }`.
  Remove the old per-variant classes and aliases for eligible declarations. Enums with any payload
  or generic parameter remain sealed arbitrary-value ADTs with generated class constructors,
  including their payloadless variants. `Option` and `Result` remain generic ADTs. This projection
  changes Dart runtime ABI to `2`, not Cott author syntax or the package version.
  If a member matches its own enum type name, append `$`: `Kind.Kind$`. It remains native,
  canonical identity stays unchanged, and native `.name` reflects the target-language escape.
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
