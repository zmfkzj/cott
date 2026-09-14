# Target selection, implementations, and deployment

Read this reference when selecting a backend, editing `cott.toml`, supplying an implementation, consuming a generated facade, or deploying a verified snapshot. Contract syntax remains target-neutral; each manifest selects exactly one closed target.

## Keep backend identities separate

Cott package `1.0.0`, Canonical IR schema `8`, and diagnostics schema `1` are shared. Generation and runtime records are not interchangeable:

| Target | Generation identity | Runtime ABI | Contract strategy |
| --- | --- | --- | --- |
| Python | schema `7`, `cott.generation.v7` | `7` | schema `5` |
| Kotlin | schema `1`, `cott.kotlin.generation.v1` | `1` | target-owned |
| Dart | schema `1`, `cott.dart.generation.v1` | `1` | target-owned |

Never copy fields, generation records, bindings, managed output, or accepted implementation source between targets. A manifest with no target or more than one target is invalid.

## Choose the target and toolchain

| Target | Initialize | Required verification tools | Cott owns |
| --- | --- | --- | --- |
| Python | `cott init path/to/project` | uv `>=0.12.3`, CPython `>=3.14.6,<3.15`, BasedPyright `>=1.39.9` | Python package facade, runtime, stubs, contract strategies, provenance |
| Kotlin | `cott init path/to/module --target kotlin` | kotlinc `>=2.2.10`, JDK `>=17`, JVM target `17`, coroutine `1.8.0` | JVM module source, verified JAR, runtime dependency record |
| Dart | `cott init path/to/package --target dart --name package_name` | Dart SDK `>=3.13.3,<4.0.0`; Linux bubblewrap and Landlock ABI `>=3` for runtime verification | portable Dart package, analyzer/kernel verification, dependency record |

Python is the default. Python and Kotlin project names are lowercase kebab-case; Dart package names are non-keyword lowercase snake_case. `init` requires an absent destination and never overwrites.

`--no-sync` is target-specific. Python still installs and probes managed Python and creates the lock, but skips the environment sync and root-venv tool probes. Kotlin and Dart skip their installed toolchain probe. Kotlin init does not create Gradle or Android files; Dart init does not create pub metadata, Flutter, or platform files.

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

The manifest schema is closed. Do not add guessed fields. Kotlin `classpath` and `compile_only` are disjoint project-relative JAR lists; only `classpath` is deployed. Dart `pubspec` and `lockfile` are optional but must be specified together. Dart verification is offline and requires each locked hosted dependency's original archive in the configured pub cache.

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

Durable accepted agent source belongs under the selected target source root:

| Target | Agent-owned path | Required shape |
| --- | --- | --- |
| Python | `python/_cott_impl/<module>/<function>.py` | exact typed function; concrete owner path for methods |
| Kotlin | `kotlin/cott_impl/<module>/<function>.kt` | one canonical `internal` top-level function; concrete owner path for methods |
| Dart | `dart/cott_impl/<module>/<function>.dart` | exact private function; concrete owner path for methods |

Use the exact signature and imports rendered by `cott prompt <fully.qualified.callable>`. Do not move, rename, copy, or hand-refresh accepted agent source: path, bytes, owner, intent fingerprint, and provenance are authenticated together. Manifest bindings are not regenerated, but their exact signature and source bytes are still checked.

Dart implementations are transformed into compiler-owned private parts. Do not add `library`, `part`, or `export` directives. Kotlin and Dart erased/runtime type distinctions use compiler-generated witnesses; do not replace them with reflection, runtime type text, unchecked casts, or phantom associated wrappers.

## Consume only public facades

- Python callers import the generated Cott module facade. They do not import or re-export `_cott_impl`, `cott_bindings`, stubs, or generated internals.
- Kotlin callers depend on the verified `cott-module.jar` and import the generated Cott package. They do not add raw generated source or import/re-export `cott_impl` or `cott_bindings`.
- Dart callers import `package:<project>/modules/<module>.dart`. They do not import implementation parts, raw state, seals, or private runtime controls.

Android/Gradle owns UI, manifests, resources, dependency resolution, DEX, APK/AAB, signing, installation, and devices. Flutter owns UI, plugins, platform scaffolds, assets, APK/AAB, and web compilation. Cott owns only the typed module, its verification, and its deployment package.

## Preserve the publication lifecycle

1. `cott emit ir` updates only Canonical IR scope and `generation.json`.
2. `cott emit python|kotlin|dart` must match the selected manifest target. It invokes no agent or target compiler and always leaves `current.verified = false`.
3. `cott generate ... --target python|kotlin|dart` invokes the selected adapter only for eligible unresolved callables. It also leaves the snapshot unverified.
4. `cott verify` rebuilds the complete selected target, rejects unresolved work or source/managed drift, runs the real target verifier, and is the only command that certifies the current snapshot.
5. `cott deploy` accepts only a verified, fully resolved, policy-passing, unchanged snapshot and publishes to a new destination. It never overwrites, generates, verifies, or infers application resources.

Deploy payloads are target-specific:

- Python: runtime code under `python/`, authored adapters, unchanged `generation.json`, exact `.python-version`, and hash-pinned production `requirements.txt`.
- Kotlin: `cott-module.jar`, unchanged `generation.json`, `dependencies.json`, coroutine runtime JAR, and verified runtime `classpath` JARs. Kotlin stdlib is required but provided by Kotlin/Gradle; `compile_only` JARs are excluded.
- Dart: portable `lib/`, compiler-owned `pubspec.yaml`, unchanged generation and dependency records, and the authenticated runtime `vendor/` closure. Kernel, runner, SDK, contracts, and caches are excluded.

Treat a successful `emit` or `generate` as publication of an unverified development snapshot, not a release. Treat successful `verify` as certification of that exact snapshot. Treat successful `deploy` as packaging, not application build or device validation.
