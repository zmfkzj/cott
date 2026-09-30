# Target selection, implementations, and deployment

Read this reference when selecting a backend, editing `cott.toml`, supplying an implementation, consuming a generated facade, or deploying a verified snapshot. Contract syntax remains target-neutral; each manifest selects exactly one closed target.

## Keep backend identities separate

Cott package `1.0.0`, Canonical IR schema `9`, and diagnostics schema `1` are shared. Generation and runtime records are not interchangeable:

| Target | Generation identity | Runtime ABI | Contract strategy |
| --- | --- | --- | --- |
| Python | schema `8`, `cott.generation.v8` | `7` | schema `6` |
| Kotlin | schema `2`, `cott.kotlin.generation.v2` | `1` | schema `6` |
| Dart | schema `2`, `cott.dart.generation.v2` | `2` | schema `6` |
| Rust | schema `1`, `cott.rust.generation.v1` | `1` | schema `6` |

Never copy fields, generation records, bindings, managed output, or accepted implementation source between targets. A manifest with no target or more than one target is invalid.

## Choose the target and toolchain

| Target | Initialize | Required verification tools | Cott owns |
| --- | --- | --- | --- |
| Python | `cott init path/to/project` | uv `>=0.12.3`, CPython `>=3.14.6,<3.15`, BasedPyright `>=1.39.9` | Python package facade, runtime, stubs, contract strategies, provenance |
| Kotlin | `cott init path/to/module --target kotlin` | kotlinc `>=2.2.10`, JDK `>=17`, JVM target `17`, coroutine `1.8.0` | JVM module source, verified JAR, runtime dependency record |
| Dart | `cott init path/to/package --target dart --name package_name` | Dart SDK `>=3.13.3,<4.0.0`; Linux bubblewrap and Landlock ABI `>=3` for runtime verification | portable Dart package, analyzer/kernel verification, dependency record |
| Rust | `cott init path/to/crate --target rust --name crate_name` | same-release cargo/rustc `>=1.85.0,<2.0.0`, edition 2024; Linux bubblewrap/Landlock ABI >=3 | portable Cargo library, offline locked verification, dependency/provenance records |

Python is the default. Python and Kotlin project names are lowercase kebab-case; Dart and Rust package names are non-keyword lowercase snake_case. `init` requires an absent destination and never overwrites.

`--no-sync` is target-specific. Python still installs and probes managed Python and creates the lock, but skips the environment sync and root-venv tool probes. Kotlin and Dart skip their installed toolchain probe. Kotlin init does not create Gradle or Android files; Dart init does not create pub metadata, Flutter, or platform files. Rust skips toolchain probe and staging emit with --no-sync; otherwise it probes and emits before atomic publication.

## Configure one closed target

Minimal target tables:

```toml
[target.python]
source = "python"
generated = "generated/python"
stubs = "generated/stubs"
lockfile = "python/uv.lock"
interpreter = ".venv/bin/python"
type_checker = ".venv/bin/basedpyright"
runtime_validation = "boundary"
```

```toml
[target.kotlin]
source = "kotlin"
generated = "generated/kotlin"
compiler = "kotlinc"
java = "java"
jvm_target = 17
runtime_validation = "boundary"
```

```toml
[target.dart]
source = "dart"
generated = "generated/dart"
sdk = "dart"
runtime_validation = "boundary"
```

```toml
[target.rust]
source = "rust"
generated = "generated/rust"
cargo = "cargo"
rustc = "rustc"
runtime_validation = "boundary"
# cargo_manifest = "rust_deps/Cargo.toml"
# lockfile = "rust_deps/Cargo.lock"
```

The manifest schema is closed. Do not add guessed fields. Kotlin `classpath` and `compile_only` are disjoint project-relative JAR lists; only `classpath` is deployed. Dart `pubspec` and `lockfile` are optional but must be specified together. Dart verification is offline and requires each locked hosted dependency's original archive in the configured pub cache.
Rust cargo_manifest/lockfile must be paired and match project name/version. Only crates.io and project-local paths are allowed; git/patch/replace/override and escaped or unsafe paths fail closed. Locked original .crate archives must be prepared in $CARGO_HOME/registry/cache/index.crates.io-*/; verify never downloads. Runtime tokio =1.53.1 plus pin-project-lite 0.2.17 are included in the frozen checksum-verified closure.

## Select implementations without changing the contract

A manifest-selected binding points to authored target code:

```toml
[target.python.implementations]
"store.order.calculate" = "cott_bindings.store.order:calculate"

[target.python.external_types]
"store.http.Request" = "framework.requests:Request"
```

```toml
[target.kotlin.implementations]
"store.order.calculate" = "cott_bindings.store.calculate"

[target.kotlin.external_types]
"store.platform.Bundle" = "android.os.Bundle"
```

```toml
[target.dart.implementations]
"store.order.calculate" = "cott_bindings/order/calculate.dart:_calculate"

[target.dart.external_types]
"store.clock.Moment" = "dart:core#DateTime"
```

```toml
[target.rust.implementations]
"store.order.calculate" = "cott_bindings/order/calculate.rs:calculate"

[target.rust.external_types]
"store.clock.Moment" = "std::time::SystemTime"
```

Durable accepted agent source belongs under the selected target source root:

| Target | Agent-owned path | Required shape |
| --- | --- | --- |
| Python | `python/_cott_impl/<module>/<function>.py` | exact typed function; concrete owner path for methods |
| Kotlin | `kotlin/cott_impl/<module>/<function>.kt` | one canonical `internal` top-level function; concrete owner path for methods |
| Dart | `dart/cott_impl/<module>/<function>.dart` | exact private function; concrete owner path for methods |
| Rust | `rust/cott_impl/<module>/<function>.rs` | exact `pub(crate) fn`/`pub(crate) async fn`; concrete owner path for methods |

Use the exact signature and imports rendered by `cott prompt <fully.qualified.callable>`. Do not move, rename, copy, or hand-refresh accepted agent source: path, bytes, owner, intent fingerprint, and provenance are authenticated together. Manifest bindings are not regenerated, but their exact signature and source bytes are still checked.

Dart implementations are transformed into compiler-owned private parts. Do not add `library`, `part`, or `export` directives. Kotlin and Dart erased/runtime type distinctions use compiler-generated witnesses; do not replace them with reflection, runtime type text, unchecked casts, or phantom associated wrappers.

Private Dart type-module aliases use `_cott_t_` plus module segments, escaping `_` as `_u` and
joining segments with `__`: `foo_bar.baz` becomes `_cott_t_foo_ubar__baz`. Use the prompt's aliases;
they do not change canonical names or public facade imports. Preserve authenticated agent bytes;
do not cosmetically edit accepted sources and then refresh their hashes by hand.
Rust embeds authored bytes into compiler-private cott_impl modules. Audit rejects unsafe/extern, include/env macros, mod/path/inner attributes, extra public items, compiler-private control and forbidden process/env/stdio access. Use only the prompted public facade/runtime and frozen production crate imports; never hand-author or refresh accepted agent provenance.
Function identifiers use the exact renderer spelling: raw-capable Rust keywords are r#keyword; self/Self/super/crate and their underscore-only suffix chains gain one underscore. Raw self/Self/super/crate/_, non-keyword r# spellings and bare keywords fail validation. Canonical Cott symbols and agent source path segments do not change.
Use only audited vec!/format!/matches! macros (no imported aliases, nested macros or qualified token-tree paths) and doc attributes. Generated get_<field>() is read-only; set_/update_ receiver writes must match declared modifies/transitions. The three provider adapters, scoped waves and frozen initial prompt hashes keep the common generation contract.
Only top-level imports/private helper functions extend an implementation; scoped/nested imports, type/impl/static items and intrinsic/imported-type shadowing are invalid. TaskScope.spawn needs a proven typed or approved constructed lexical receiver, never local/closure shadowing or direct std/tokio executor APIs. Field identifiers are audited; clock access needs clock effect while pure Duration does not.
Preserve receiver identity across method boundaries. Direct *receiver/raw-field assignment, std/core mem replace/take/swap through receiver/reborrow/field aliases, Option-style field take/replace, helper mutable-parameter escapes and mem function-pointer aliases are invalid. Only declared guarded set_/update_ mutation is allowed; the ABI runtime identity check is defense in depth, not a substitute for source audit.

## Consume only public facades

- Python callers import the generated Cott module facade. They do not import or re-export `_cott_impl`, `cott_bindings`, stubs, or generated internals.
- Kotlin callers depend on the verified `cott-module.jar` and import the generated Cott package. They do not add raw generated source or import/re-export `cott_impl` or `cott_bindings`.
- Dart callers import `package:<project>/modules/<module>.dart`. They do not import implementation parts, raw state, seals, or private runtime controls.
- Rust callers link the deployed Cargo library and call `<crate>::modules::<module path>`; ABI values live in `<crate>::cott_runtime`. Never access crate-private cott_impl, authoring sources, seals or compiler controls. ContractViolation uses panic_any and declared errors use Result; catching violations requires panic="unwind".

For Dart ABI `2`, a whole nonempty enum with no type/const generics and only payloadless variants
is a native enum. Preserve exact Cott spelling: use `Kind.Local`, not `KindLocal()` or
`Kind.Local()`. `Kind.values`, `value.name`, and `value.index` are native Dart operations, and a
switch can exhaustively match constant members without a wildcard:

```dart
String label(Kind kind) => switch (kind) {
  Kind.Local => 'local',
  Kind.Remote => 'remote',
};
```

The eligible enum's former variant classes are removed without aliases. Any payload or generic
parameter keeps the entire enum as a sealed arbitrary-value ADT with generated variant class
constructors, including payloadless variants. `Option` and `Result` remain generic ADTs.
These are target projection rules, not changes to `.cott` author syntax.
The only member-name escape is a member matching its enum type: `Kind.Kind$`, not `Kind.Kind`.
It remains native; its canonical identity is unchanged, while native `.name` includes the `$`.

Dart structs retain the named `<Struct>$CopyWith` extension and `value.copyWith(...)`; omitted
fields preserve exact stored values and explicit overrides rerun the canonical constructor.
Nullable Option helpers require `T extends Object`, so `Some(null)` is never conflated with
`Nothing`. General `Option[Any]` uses explicit variants. `CottBytes.readOnlyView` is zero-copy and
read-only; `toUint8List()` returns a mutable defensive copy.

Android/Gradle owns UI, manifests, resources, dependency resolution, DEX, APK/AAB, signing, installation, and devices. Flutter owns UI, plugins, platform scaffolds, assets, APK/AAB, and web compilation. Cott owns only the typed module, its verification, and its deployment package.
Cargo owns application dependency resolution, linking, profiles and execution. The Rust runtime is a module within each Cott crate, not a colliding standalone runtime package.

## Preserve the publication lifecycle

1. `cott emit ir` updates only Canonical IR scope and `generation.json`.
2. `cott emit python|kotlin|dart|rust` must match the selected manifest target. It invokes no agent or target compiler and always leaves `.snapshots[.current].verified = false` in the record.
3. `cott generate ... --target python|kotlin|dart|rust` invokes the selected adapter only for eligible unresolved callables. It also leaves the snapshot unverified.
4. `cott verify` rebuilds the complete selected target, rejects unresolved work or source/managed drift, runs the real target verifier, and is the only command that certifies the current snapshot.
5. `cott deploy` accepts only a verified, fully resolved, policy-passing, unchanged snapshot and publishes to a new destination. It never overwrites, generates, verifies, or infers application resources.

Deploy payloads are target-specific:

- Python: runtime code under `python/`, authored adapters, unchanged `generation.json`, exact `.python-version`, and hash-pinned production `requirements.txt`.
- Kotlin: `cott-module.jar`, unchanged `generation.json`, `dependencies.json`, coroutine runtime JAR, and verified runtime `classpath` JARs. Kotlin stdlib is required but provided by Kotlin/Gradle; `compile_only` JARs are excluded.
- Dart: portable `lib/`, compiler-owned `pubspec.yaml`, unchanged generation and dependency records, and the authenticated runtime `vendor/` closure. Kernel, runner, SDK, contracts, and caches are excluded.
- Rust: portable src/, exact-pinned compiler Cargo.toml/Cargo.lock, unchanged generation/dependency records and frozen path deps/. Copy solver-only path packages too so Cargo metadata/lock remains closed. Registry vendor/.cargo, verification rlib/runner, contracts, Cott tests and caches are excluded; consumers share registry tokio instead of vendored path copies.

Treat a successful `emit` or `generate` as publication of an unverified development snapshot, not a release. Treat successful `verify` as certification of that exact snapshot. Treat successful `deploy` as packaging, not application build or device validation.

## Read and relocate a generation record

`generation.json` is a closed envelope with exactly four keys: `schema_version`, `current`,
`last_verified`, and `snapshots`. `current` is a content digest; `last_verified` is a digest or
`null`. `snapshots` maps each reachable digest to a full snapshot object. Exactly one or two blobs
are stored; identical current/last-verified references share one. For example:

```bash
jq '.snapshots[.current].verified' generated/generation.json
jq 'if .last_verified == null then null else .snapshots[.last_verified] end' generated/generation.json
```

Snapshot content identity includes full evidence, `AgentRun` data, and the verified flag.
`generation_id` instead excludes the existing volatile fields in a normalized target-domain
identity wrapper. Both use SHA-256 over the `cott.snapshot.v1` domain plus NUL and a structural
encoding of tagged, length-delimited values and f64 IEEE bits—not raw JSON text. Input and managed
file hashes still cover raw file bytes. See architecture §16.1 for the envelope sample.

Readers reject old formats, unused/dangling blobs, and digest/content tampering. There is no
external snapshot cache or sidecar: one record contains everything needed to resolve both
snapshots when saved as a diff baseline or relocated into deployment. Generated output must use
the new runtime loader and carry its self-contained deployment record.

The bounded one-time repository conversion is compiler-linked and transactional: preserve source
and `AgentRun` evidence, clear verification, then run real emit and verify. It is not a public
migration command or a compatibility reader. Old certification does not carry across schema/ABI
changes; never edit hashes to bless changed source. The package version remains `1.0.0`.
Rust schema 1 has no legacy conversion. Native regressions require absolute COTT_CARGO (and optional COTT_RUSTC); examples/integrations/rust-counter/tool/setup.sh requires an absolute in-tree COTT_BIN and refuses prior output before real emit/verify/deploy. Generate accepted counter implementations with Cott first, then run the standard app/ consumer after deployment.
