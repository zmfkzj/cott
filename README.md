# cott

`cott` is a language-like compiler for typed intent and prompt authoring. A bodyless `.cott`
module declares public types, functions, contracts, effects, scenarios, and errors. Those
declarations are the authored intent; Python, Kotlin/JVM, and Dart are verified projections, not second
contract sources. Runtime code uses generated public facades and does not read authored `.cott`
live.

Cott fixes those declarations, renders a scoped generation prompt, records intent fingerprints,
and checks implementation conformance, artifact identity, and observed evidence. It does not
completely formalize intent, and a passing check is not a general proof that an implementation
is correct. The product is typed authoring and evidence, not a speed claim.

`architecture.md` is the normative implemented v1.0 language contract. The package remains `1.0.0`,
Canonical IR schema `8`, contract-test strategy schema `5`, and diagnostics schema `1`.
Python uses generation schema `8`, domain `cott.generation.v8`, and runtime ABI `7`.
Kotlin uses generation schema `2`, domain `cott.kotlin.generation.v2`, and runtime ABI `1`.
Dart uses generation schema `2`, domain `cott.dart.generation.v2`, and runtime ABI `2`.
These are separate closed target identities: readers and runtimes reject other backends and old
records. Dart packages are directly consumable by Flutter; no Kotlin bridge is required.

If these docs and repository source disagree, the source files and closed schema validators are
authoritative; documentation must be corrected rather than inventing a compatibility path.

Implemented v0.8 `.cott` source remains source-compatible with unchanged semantics. Serialized and
generated artifacts are exact-identity: regenerate them after a schema, ABI, or package mismatch.
Normal readers reject old records; there are no compatibility readers or generated aliases.

## Contract and evidence

Cott resolves and type-checks declarations, lowers Canonical IR, projects a target, and records only
the evidence it actually obtains. Invalid syntax, names, types, constants, tags, manifests, and
artifact identities are errors. A missing valid runtime capability does not invent a result:
verification records `unobserved` where execution observation is unavailable. Unsupported or
budget-exhausted bounded proof is `unknown`, not `unobserved` or trust.

Evidence is one of:

| Status | Meaning |
| --- | --- |
| static proof | A deterministic non-executing declaration, signature, type, or target-shape check passed. |
| runtime check | A configured production boundary executed the check. |
| test observation | A permitted valid case executed and observed the contract point. |
| unobserved | No permitted runtime or test observation was available. |
| unknown | Bounded static proof was unsupported or exhausted its proof budget. |
| trust declaration | The declaration is accepted without general proof by Cott. |

Struct invariants are part of the canonical constructor contract. Scenarios use only public facades
and closed filesystem, HTTP, clock, and failure fixtures. Effectful fixture observations require the
compiler-owned Linux bubblewrap isolated-loopback sandbox; missing or unusable isolation is
unobserved, never an unsandboxed or external-network fallback. Semantic coverage joins the Canonical
IR clause inventory to runner evidence; manifest coverage rules may gate selected clauses without
changing artifact certification.

`doc` is non-executable metadata and does not decide conformance. A `doc`-only contract diff is
`DOCUMENTATION`; that label is not the regeneration signal. Changing `doc`, a relevant rule, a
referenced type, or an incoming scenario still updates that callable's intent fingerprint and can
queue agent regeneration. Applied-rule identity, contract constants, and retained generator-rule
identifiers participate in that same scoped closure. Observed clauses do not prove that requirements are complete. `verified`
certifies artifact, type, runtime, proof, and runner evidence for that snapshot; it does not mean
every semantic clause was observed or that a coverage policy passed. Coverage gates only selected
rules; with no selected rules there is no gate. External effects and some boundaries remain trust
declarations. Proof and sampling are bounded: unsupported or budget-exhausted bounded proof is
`unknown`; unavailable execution observation is `unobserved` or trust according to the capability.
Neither is invented success.

Typed Python plus independent tests is a valid baseline for the same task. Cott is worth its cost
when a stable public facade and a provenance/evidence boundary matter. The primary comparison is
the same AI model generating through Cott versus generating Python directly. Human authoring and
review costs are not that comparison and are not synthesized.

`benchmarks/contract_value.py` measures mutation and runtime cost on already-generated artifacts.
It is not generation or productivity evidence. The actual AI generation comparison is
`benchmarks/ai_generation.py`: both arms implement the same artifact-pipeline task against a
hidden independent 3130-case corpus, from clean implementations, with a fixed model and config.
Each trial runs one Cott `generate` workflow (native per-callable retries included) and one
direct generation invocation, at most `-j 3`. Generation wall time is recorded separately from
verify and acceptance. Cott native provenance reports durations and stream digests only; token
usage is unavailable and is not inferred. This comparison is three pairs of one task. Direct uses
one invocation per trial; Cott uses native per-callable retry. Both arms use the same model and
toolset.

Those recorded trial numbers are historical artifacts tied to the compiler hashes stored with that
run. They are not a performance claim for the current prompt renderer.

The independent pipeline acceptance corpus is not part of `cott verify` and is not a canonical
evidence source or compiler certification. Shared cases live in
`examples/complex/artifact-pipeline/check_semantics.py`. Prerequisite: uv-sync project
environments, an installed authenticated OMP, and a real target environment, then run:

```bash
examples/complex/artifact-pipeline/.venv/bin/python examples/complex/artifact-pipeline/check_semantics.py
examples/complex/artifact-pipeline/.venv/bin/python benchmarks/contract_value.py --cott cott --repeat 3 --output benchmarks/contract-value-results.json
examples/complex/artifact-pipeline/.venv/bin/python benchmarks/ai_generation.py --cott target/debug/cott --repeat 3 --jobs 3 --output benchmarks/ai-generation-results.json
```

## Example workflow

Every example is an independent project. For a Python project, use this sequence from the
repository root and replace `<project>` with an indexed Python path below.

Discover the installed package and commands with `cott --version` (or `cott -V`) and `cott --help`.

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

A manifest selects exactly one of `[target.python]`, `[target.kotlin]`, or `[target.dart]`.
The Kotlin table is closed. `source`, `generated`, and `runtime_validation` are required;
`compiler = "kotlinc"`, `java = "java"`, and `jvm_target = 17` have those defaults and JVM 17 is
the only accepted target. `classpath` contains runtime JARs and `compile_only` contains compile-time
JARs such as an Android SDK `android.jar`; both are hashed compiler inputs, but only `classpath`
JARs are deployed. Bindings and external projections use their target-specific tables:

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

The complete Kotlin-only lifecycle uses the same Cott source language and Canonical IR:

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

`init --target kotlin` creates only a Cott Kotlin module, not an Android application. `check` and
`fmt` do not compile Kotlin. `emit kotlin` never invokes an agent or compiler; it writes
compiler-owned Kotlin sources and an unverified record, omitting unresolved callable facades.
`prompt` writes an `implementation.kt` instruction without invoking a provider or compiler.
`generate --target kotlin` writes only eligible durable implementation sources and also publishes
an unverified snapshot. Only the explicit `verify` command compiles the complete module, runs the
sandboxed bounded contract runner, writes `library/cott-module.jar`, and certifies
`.snapshots[.current].verified = true` with `current == last_verified`. Source, manifest, implementation, tool,
or managed-byte drift fails closed.

Kotlin/JVM erases ordinary type parameters. Cott therefore projects associated types to additional
bounded Kotlin type parameters and resolves concrete impl assignments before overrides; it does not
use reflection or a phantom associated-type wrapper. Free const generics use explicit
`_cott_const_*: CottConst` value-witness parameters so their exact unsigned mathematical values
remain available. Ordinary type and abstract associated-generic relationships remain static
guarantees: runtime validation cannot reify arbitrary erased `T`, and the bounded runner reports an
unsupported abstract associated runtime candidate as unobserved/unknown rather than inventing an
observation.

Manifest bindings remain source-owned under `target.kotlin.source`; accepted agent sources live at
`<target.kotlin.source>/cott_impl/<module>/<callable>.kt`. Their package, canonical top-level
function, exact signature, path, content hash, intent fingerprint, and owner are audited. Unimplemented
callables and authentic intent-stale agent sources remain unresolved; unrecorded, moved, or tampered
agent files fail closed rather than refreshing trust from an old record. Public
consumers import only the generated Cott module package, never `cott_bindings` or `cott_impl`.

### Dart module and Flutter workflow

Dart requires SDK `>=3.13.3,<4.0.0`; `project.name` is the lowercase snake_case Dart package name.
Cott owns the module, while Flutter owns widgets, plugins, application resources and platform builds.
`cott init --target dart` creates a Dart Cott module, not a Flutter application.

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
# init creates an empty module. First declare a callable in src/example_module/main.cott,
# for example: fn main() -> Unit
cott check --project path/to/module
cott emit dart --project path/to/module
cott prompt example_module.main.main --project path/to/module
cott generate --agent omp --target dart --project path/to/module
cott verify --project path/to/module
cott diff --project path/to/module
cott deploy --project path/to/module --output dist/example_module
```

`emit dart` and `generate --target dart` always publish an unverified snapshot. Only `verify`
runs the real Dart analyzer, kernel compiler and authenticated bounded runner, then certifies
`current == last_verified`. Authored private implementation functions become compiler-owned Dart
parts; public callers import `package:<name>/modules/<module path>.dart`, not implementation files.
Stateful methods share an owner-private library so state and guard internals remain private.

The runtime preserves I64/U64 through `BigInt`, exact fixed-width bounds, F32 rounding, Unicode,
immutable values and protocol lifecycles. Generic APIs use explicit `CottType<T>` witnesses where
Dart types cannot recover Cott distinctions; checked views enforce Cott variance instead of relying
on Dart covariance. Const generics use `CottConst` witnesses. Cancellation is cooperative and guard
ownership is explicit; arbitrary `Future` preemption is never claimed.

Dart ABI `2` projects a whole nonempty, nongeneric enum to a native Dart enum only when every
variant is payloadless. Cott author syntax is unchanged; callers and implementations use the exact
member spelling `Kind.Local`, without parentheses. `Kind.values`, `value.name`, `value.index` and
exhaustive constant-pattern switches are native Dart operations:

```dart
String label(Kind kind) => switch (kind) {
  Kind.Local => 'local',
  Kind.Remote => 'remote',
};
```

The old variant classes for these eligible enums are removed, not retained as aliases. An enum with
any payload or generic parameter remains a sealed arbitrary-value ADT with generated variant class
constructors, even for its payloadless variants. `Option` and `Result` remain generic ADTs.
The sole member-name escape is an enum member matching its enum type: `Kind.Kind` becomes
`Kind.Kind$`, still native. Its canonical identity is unchanged; native `.name` reflects the `$`.

Verification requires Linux bubblewrap and Landlock ABI `>=3`. The filesystem policy is applied
before Dart VM threads start. It denies process-memory access while permitting the VM's own
`/proc/self/maps` and declared scratch I/O. Runner messages use a fresh stdin-only HMAC-SHA256 key;
candidate stdout cannot certify a snapshot.

For dependencies, set both `target.dart.pubspec` and `target.dart.lockfile` to project-relative
metadata files outside the implementation source tree, for example `dart_package/pubspec.yaml`
and `dart_package/pubspec.lock`. Package name/version must match Cott. Verification is offline and
uses the exact production closure, not dependency overrides or a fresh solver choice. Hosted
packages additionally require the original locked archive at
`$PUB_CACHE/hosted-archives/<registry-cache-key>/<name>-<version>.tar.gz`.
Prepare these archives explicitly from the registry's `archive_url`; Cott checks their compressed
SHA-256 against the lock and compares extracted bytes before trusting the cache. An extracted
pub cache plus its writable hash sidecar is insufficient. Missing archives fail with their required
path; Cott does not silently download them during verification.

The working Flutter consumer is `examples/integrations/flutter-counter`:

```bash
cd examples/integrations/flutter-counter
COTT_BIN=/absolute/path/to/cott FLUTTER_BIN=/absolute/path/to/flutter dart tool/setup.dart
cd flutter
flutter analyze --no-pub
flutter build web --release --no-pub --no-web-resources-cdn
flutter build apk --debug --no-pub
```

Setup emits, verifies and deploys the module to `flutter/cott_module`, refuses an existing output,
then runs Flutter's own `pub get`. The app depends on that directory and imports only
`package:flutter_counter/modules/example/counter.dart`. Dart deployment contains `lib/`,
compiler-owned `pubspec.yaml`, unchanged `generation.json`, `dependencies.json` and verified
runtime vendor packages. It excludes kernel verification artifacts, contracts, authoring copies,
the SDK, runner support and caches. Flutter compiles those portable sources for its chosen platform.
Flutter `3.47.4` with bundled Dart `3.13.3` was exercised: analyzer, release web build and debug
Android APK build passed. Browser interaction confirmed `0 → 1 → 0` and both bounds `0..100`;
the Cott module recorded all six clauses as observed. APK build is not device execution evidence.

### Prompt inspection and snapshot lifecycle

Inspect a callable using its own project and fully qualified name, for example:

```bash
cott prompt curriculum.artifact_pipeline.plan_pipeline --project examples/complex/artifact-pipeline
cott prompt curriculum.artifact_pipeline.plan_pipeline --project examples/complex/artifact-pipeline --format json
```

`cott prompt <fully.qualified.callable> [--project DIR] [--format json]` inspects the exact initial
generation prompt. It does not call a provider or target compiler/checker, and it does not publish
or recover journals. Human mode writes the prompt bytes; JSON is
`{symbol,intent_hash,prompt_hash,generation_required,context,prompt}`. `prompt` matches those
initial bytes, `prompt_hash` hashes only that initial prompt, and retries later append actual
validation feedback. The requested write path is `implementation.py` for Python,
`implementation.kt` for Kotlin, or `implementation.dart` for Dart. Inspection may take the project lock and write lock metadata; a
pending journal is refused without recovery. `context` is the scoped transitive declaration set:
explicit identifier references, `constant_ref` uses, `cott.applied_rule` links and their bases,
relevant incoming scenarios, and global rule prose plus `cott-domain` lines for selected callables.
Prompt sections are authority, current intent, formal declarations, project rules, reference
implementations, target output rules, and optional feedback. Rules and reference prose never
override source; conflicts are surfaced, not NLP-proved.

Target emission never invokes an agent. It updates compiler-owned output, records unresolved
callables, and omits their callable facades. `emit ir` rewrites only IR scope and
`generation.json`; non-IR managed hashes stay the trusted recorded values, so IR-only emission
cannot bless unrelated on-disk edits. Pending unresolved agent sources with authentic `AgentRun`
provenance stay owned across repeated emit and checkpoint until `generate` regenerates them.
Manifest-owned bindings are excluded from intent regeneration. Tampered agent files that do not
match their recorded path and content hash are rejected. `generate` invokes the selected agent only
for eligible unresolved callables; selected bindings and accepted durable implementations are
reused unless their intent fingerprint changed. One generate invocation freezes the advertised
initial prompt snapshot; later accepted wave candidates are used for validation and do not change
that initial `prompt_hash`. Emit and generate always leave the current snapshot unverified. Only
`verify` rebuilds the managed target and certifies evidence without editing source contracts. It
refuses pending unresolved work and does not export old managed implementations that are not in the
current facade. `current` references the last emitted epoch; `last_verified` references the historical
certified baseline or is `null`. A verified current snapshot has the same reference as `last_verified`.
An already deployed snapshot keeps its old contract until `emit` or `generate`; runtime does not read
authored `.cott` live. Valid Python records without `tools.cott_intent` derive fingerprints from the
recorded contract surface; absence is never fresh, and missing manifest or rule evidence invalidates
conservatively. This is not a reader for old schemas.

The closed `generation.json` envelope has exactly `schema_version`, `current`, `last_verified`, and
`snapshots`. Both references are snapshot content digests, and `snapshots` maps those digests to full
snapshot objects. It contains exactly one or two reachable blobs; equal references store the object
once. Read the verification flag with `jq '.snapshots[.current].verified' generation.json`, not by
treating `current` as an object. Unused, dangling, or tampered blobs are rejected.

Snapshot content identity includes all verification evidence, `AgentRun` data, and the `verified`
flag. It is independent of `generation_id`, which excludes the existing volatile fields and hashes
the normalized generation identity in an explicit target-domain wrapper. Both use the structural
JSON digest: SHA-256 over `cott.snapshot.v1` plus NUL and tagged, length-delimited values, with f64
IEEE bits for floating-point numbers—not a hash of raw JSON text. See architecture §16.1 for the
envelope and exact identity rules.

The record is self-contained: saving a diff baseline or relocating/deploying it needs no external
snapshot cache or sidecar. Regenerated output requires the new runtime loader and its self-contained
deployment record. The bounded one-time repository cutover uses compiler-linked transactional
conversion to preserve source and `AgentRun` evidence, clear verification, then run real emit/verify.
It is not a public migration command or normal old-record reader. Old certification never carries
to a new schema or ABI, and editing source hashes cannot bless changed agent code.

`generate --agent` accepts three direct adapters: `codex`, `claude`, and `omp`. `claude` directly
invokes official native Claude Code `>=2.1.89`; an OMP run that selects a Claude model remains
`omp`, not `claude`. Before generation, direct Claude's native-entrypoint check rejects npm
`cli.js` entrypoints and Node shebangs, then runs the exact credential-free, network-disabled probe
`claude --version`. The probe must finish without timeout at status `0`; its stdout must be exactly
one strict SemVer token `>=2.1.89`. Generation is separate: it receives the exact UTF-8 prompt on
stdin, is limited to `Read` and `Write`, and accepts only a successful JSON result. Only generation
may receive an existing `ANTHROPIC_API_KEY` and retain provider network egress; no network-capable
Claude tools are exposed. The normative argv, environment, native-entrypoint, and result contract
is in architecture §17.2.1.

`generated/` and any agent-owned `python/_cott_impl/` or
`<target.kotlin.source>/cott_impl/` files committed in an
example are actual compiler results. They are not an authoring shortcut. `.venv/`, `.cott/`,
`.gradle/`, `build/`, and `__pycache__/` are transient. Public code imports generated Cott facades
only; `_cott_impl`, `cott_bindings`, and `cott_impl` are not public import paths.

## Runtime deployment

`cott deploy [--output <dir>] [--project <dir>] [--format json]` packages the verified
current snapshot into a new directory. The default is `<project>/dist/<name>-<version>/`;
a relative `--output` is relative to the invoking working directory. Existing output is
never overwritten. Source and generated files are not rewritten.

```bash
cott deploy --project examples/grammar/checked-add --output dist/checked-add
cd dist/checked-add
uv venv
uv pip install --require-hashes -r requirements.txt
PYTHONPATH=python .venv/bin/python -c 'from curriculum.checked_add import checked_add; print(checked_add(1, 2))'
```

The bundle contains `python/` with public facades, types, `cott_runtime`, selected implementation
copies and authored Python adapters; unchanged `generation.json`; the exact target `.python-version`;
and hash-pinned production `requirements.txt`. Cott itself, `.cott` sources, `cott.toml`, the
`generated/` directory, IR, stubs, tests, private authoring copies, development directories,
virtual environments and caches are excluded. Runtime Python code is relocated, not removed:
`cott_runtime` and `generation.json` remain necessary for the existing provenance loader.
Non-Python application resources are not inferred or copied.

Deployment requires a verified, fully resolved snapshot with a passing selected coverage policy,
unchanged compiler inputs and exact managed bytes. It does not generate or re-verify code.
Runtime dependencies are exported offline from the frozen lock with uv `>=0.12.3`, excluding
development/default dependency groups; dependency-free projects need no uv during packaging.
Python and third-party distributions are installed separately on the destination, which must
match the recorded CPython patch, OS and architecture. No Cott executable is needed there.

For Kotlin, deployment contains `cott-module.jar`, unchanged `generation.json`,
`dependencies.json`, and `runtime-libs/`. The exact compiler-distribution
`kotlinx-coroutines-core-jvm.jar` version `1.8.0` and every verified `classpath` JAR are runtime
libraries. Kotlin stdlib is a required, hash-recorded dependency supplied by Kotlin or the Android
Gradle plugin and is not bundled a second time; `compile_only` JARs are never deployed.

The Android counter is a normal Gradle consumer of that deployed module:

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

Use the example's pinned Gradle `9.1.0` wrapper; it pins the official distribution SHA-256
`a17ddd85a26b6a7f5ddb71ff8b05fc5104c0202c6e64782429790c933686c806`. The standard Android
project uses Android Gradle plugin `9.0.1` (bundled Kotlin `2.2.10`), compile/target SDK `36`, min
SDK `26`, and JVM 17. `COTT_BIN` selects an in-tree compiler while developing and may be omitted
for an installed `cott`. The Gradle task consumes only the deployed module JAR and runtime
dependency JARs. Application code imports the public `example.counter.increment` and
`example.counter.decrement` functions. A separate native JVM consumer has compiled and run against
the published module (`increment(0) == 1`, `decrement(100) == 99`, and invalid
`increment(100)` is rejected), and verification recorded all six clauses as observed with no
unknown or unobserved clause. The pinned Gradle build also assembled and installed the debug APK
on an AOSP API 36 software emulator; UI interaction observed the bounded counter transition
`0 → 1 → 0`. This is emulator evidence, not a physical-device claim.

Cott owns compilation, verification, and deployment of the Cott module only. Standard
Android/Gradle owns the UI source, `AndroidManifest.xml`, resources, dependency graph, DEX,
APK/AAB assembly, signing, installation, and device lifecycle. Cott does not scaffold an Android
app and does not run Python on-device.

## Reduced example index

The authored inventory contains 26 Python projects, 20 Kotlin projects and one Dart/Flutter project.
The Python set has six grammar lessons, three simple lessons, one complex curriculum project, the
separate `process-bar` fixture, seven features, one modular project, one FastAPI integration and six
real-world projects. `examples/kotlin/` contains 19 corresponding Kotlin lessons/fixtures, with
`integrations/android-counter` as the twentieth Kotlin project.
`integrations/flutter-counter` is the Dart module and standard Flutter consumer.

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

### Real — 6

| Project | Distinct contract |
| --- | --- |
| `real/yt-dlp` | Playlist selection, archive-aware download planning, output templates, JSON rendering, and bounded media transfer. |
| `real/harlequin` | SQLite statement execution, schema catalog search, and deterministic query and catalog rendering. |
| `real/pgcli` | Connection precedence, SQL completion, query rendering, backslash commands, and database execution. |
| `real/posting` | YAML HTTP-request collections, variable resolution, curl export, persistence, and bounded network requests. |
| `real/toolong` | Bounded log paging, JSONL rendering, merging, searching, and appended-file reads. |
| `real/frogmouth` | Markdown document navigation, loading, state persistence, and sidebar application behavior. |

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

### Python composition and integration — 2

| Project | Distinct contract |
| --- | --- |
| `modular/order-management` | `store.order` and `store.catalog` compose through generated module facades. |
| `integrations/fastapi-hello` | FastAPI projection: external `HttpRequest` maps to `starlette.requests:Request`; the generated `read_root` facade is registered by the small app adapter. |

### Kotlin/Android integration — 1

| Project | Distinct contract |
| --- | --- |
| `integrations/android-counter` | A Kotlin/JVM 17 Cott counter module deployed as a JAR and consumed by a standard Gradle-owned Android application through public `example.counter` imports. |

## Editor analysis

Run the parameterless language server from a Cott project:

```bash
cott lsp
```

It serves stdio JSON-RPC diagnostics, completion, hover, and definition with UTF-16 positions and
full document sync. It analyzes open documents only; it does not emit, publish, or invoke an agent.
