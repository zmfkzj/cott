---
name: cott
description: Use the Cott 1.0 contract-first DSL compiler to initialize Python, Kotlin, or Dart projects; author .cott contracts; check and format sources; inspect prompts; emit deterministic IR and target facades; generate missing implementations with Codex, Claude, or OMP; verify and deploy releases; inspect semantic diffs; and run the editor language server. Use when creating, changing, generating, validating, deploying, or consuming a Cott project.
compatibility: Requires cott 1.0.0. Python uses uv >=0.12.3, CPython >=3.14.6,<3.15, and BasedPyright >=1.39.9. Kotlin uses kotlinc >=2.2.10, JDK >=17, JVM 17, and coroutine 1.8.0. Dart uses SDK >=3.13.3,<4.0.0; runtime verification requires Linux bubblewrap and Landlock ABI >=3.
metadata:
  version: "1.0.0"
---

# Cott

Treat every bodyless `.cott` module as the only public contract source. Python, Kotlin, and Dart artifacts are checked projections, not additional contract sources. A manifest selects exactly one target.

## Non-negotiable boundaries

- Never hand-edit `generated/`. Change `.cott`, `cott.toml`, or the selected authored implementation source, then run the command that owns the output.
- Public consumers import generated target facades only. Python `_cott_impl`/`cott_bindings`, Kotlin `cott_impl`/`cott_bindings`, and Dart private parts are never public import or re-export paths.
- Keep backend identities closed. Never accept or copy one target's generation record, runtime fields, bindings, or managed code as another target's truth.
- Do not add legacy readers, compatibility shims, partial profiles, or unsandboxed fixture fallbacks. An unavailable isolated fixture is `unobserved`, never host filesystem or network execution.
- `emit` and `generate` always leave the current snapshot unverified. Only explicit `cott verify` certifies it; `cott deploy` additionally requires a fully resolved, coverage-policy-passing, unchanged snapshot.
- Read generation records through `.snapshots[.current]`, not a nested `current` object. The closed
  envelope contains `schema_version`, digest references `current`/`last_verified`, and full blobs in
  `snapshots`; it is self-contained for saved baselines and deployment. Normal readers reject old
  records. See [target identities and record access](references/targets-and-deployment.md).
- Dart ABI `2` uses native member constants such as `Kind.Local` for whole nonempty, nongeneric,
  all-payloadless enums. Use exhaustive constant patterns, not the removed variant classes.
  Payload/generic enums, including `Option`/`Result`, keep ADT constructors. A member matching its
  enum type is escaped with `$` (`Kind.Kind$`), without changing its canonical identity or Cott syntax.
- Cott builds and verifies a Kotlin/JVM module or portable Dart package. Gradle/Android and Flutter retain ownership of applications, UI, resources, platform builds, signing, installation, and devices.

When working in the Cott compiler repository, `architecture.md` is the normative implemented v1.0 contract. If prose conflicts with source or a closed schema validator, follow the implementation and update the prose.

## Start or locate a project

Confirm the compiler identity and command surface:

```bash
cott --version
cott --help
```

Initialize an absent path. Python is the default target:

```bash
cott init path/to/python-project
cott init path/to/kotlin-module --target kotlin
cott init path/to/dart-package --target dart --name dart_package
```

Use `--name` when the path basename is not a valid project name. Python and Kotlin names are lowercase kebab-case; Dart names are non-keyword lowercase snake_case. `init` never overwrites an existing path.

Target initialization is deliberately narrow:

- Python creates the Cott source, Python metadata, lockfile, and normally a synced root `.venv`.
- Kotlin creates the Cott source and Kotlin implementation root, then probes installed Kotlin/JDK tooling. It does not create Gradle or Android files.
- Dart creates the Cott source and Dart implementation root, then probes the installed SDK. It does not create pub metadata, Flutter, or platform files.

`--no-sync` is target-specific. Python still installs/probes managed Python and creates the lock, but skips environment sync and root-venv tool probes. Kotlin and Dart skip their installed toolchain probe.

For an existing project, locate `cott.toml`. Set the root explicitly unless the current directory is that root:

```bash
project=path/to/project
cott check --project "$project"
```

Read [target selection, implementations, and deployment](references/targets-and-deployment.md) before editing a target table, implementation selector, external type projection, dependency input, consumer integration, or deployment flow.

## Author contracts

Load authoring references progressively:

1. Always read [module and declaration basics](references/authoring-basics.md) before creating or changing `.cott`.
2. Read [functions, contracts, and effects](references/contracts-and-effects.md) when changing public behavior.
3. Read [traits, resources, and scenarios](references/traits-and-scenarios.md) only for stateful protocols, async scheduling, or fixture-backed evidence.
4. Read [targets and deployment](references/targets-and-deployment.md) only when target configuration or generated-code boundaries are involved.

Start from the closest maintained example named in the guide; do not load every reference for a small edit.

Author in this order:

1. Choose the file path, then give it the exact source-relative module name: `src/store/order.cott` starts with `module store.order`.
2. Import public symbols explicitly with `use`.
3. Model the domain with aliases, newtypes, structs, enums, constants, and only the generics the public API needs.
4. Add bodyless `fn` or `async fn` declarations.
5. Express caller obligations with `requires`, output relations with ordered `ensures`, observable failures with ordered `error`, and the exact closed capability set with `effects`.
6. Add scenarios only when finite public calls or isolated fixtures demonstrate behavior that clauses alone do not.

```cott
module store.catalog

struct Item:
    sku: Str
    price_cents: U64

struct Catalog:
    items: List[Item]

enum CatalogError:
    ItemNotFound(sku: Str)

fn find_item(catalog: Catalog, sku: Str) -> Result[Item, CatalogError]:
    requires sku.len > 0
    ensures Result.Ok(item) => item.sku == sku
    error CatalogError.ItemNotFound
    effects []
```

Use four-space indentation. Tabs and semicolons are invalid. Keep validation in the contract and generated boundary rather than duplicating it in target implementation code.

## Use the command pipeline

Use `--format json` for automation on commands that accept it. Diagnostics use the closed diagnostics schema v1. Successful `prompt` and `diff` calls have their own closed JSON payloads; do not scrape human output or assume every success payload is a diagnostics envelope.

### 1. Check and format

```bash
cott check --project "$project" --format json
cott fmt --check --project "$project" --format json
```

Fix diagnostics at the source. If formatting is the only problem, apply the official formatter and re-check:

```bash
cott fmt --project "$project" --format json
cott check --project "$project" --format json
```

A single source path is useful for diagnosis, but project-wide checking remains the integration gate:

```bash
cott check src/store/order.cott --project "$project" --format json
```

### 2. Inspect intent when needed

Render the same frozen initial prompt that generation would use, without invoking a provider or target compiler/checker:

```bash
cott prompt store.order.calculate --project "$project" --format json
```

The JSON payload is `{symbol,intent_hash,prompt_hash,generation_required,context,prompt}`. The target write path in the prompt is `implementation.py`, `implementation.kt`, or `implementation.dart`. Formal declarations are authoritative; project rules and references add context but never override them.

### 3. Emit deterministic artifacts

Emit only Canonical IR when inspecting the compiler's semantic interpretation:

```bash
cott emit ir --project "$project" --format json
```

Emit the selected target projection without invoking an agent or target compiler:

```bash
target=python # python, kotlin, or dart; must match cott.toml
cott emit "$target" --project "$project" --format json
```

Unresolved callables are recorded and intentionally omitted from public facades. Do not add placeholders. Both IR-only and target emission invalidate current certification while preserving verified history.

### 4. Supply implementations

Prefer an exact compatible manifest-selected binding or fresh durable accepted source. Otherwise generate all eligible unresolved callables with an explicitly selected adapter and matching target:

```bash
cott generate --agent codex --target "$target" --project "$project" --format json
```

Generate one callable by exact canonical FQN when the task is scoped; use `-j` only for independent unresolved callables:

```bash
cott generate store.order.calculate --agent omp --target "$target" -j 1 --project "$project" --format json
```

Accepted adapters are `codex`, direct native `claude`, and `omp`. A Claude model selected inside OMP still uses the `omp` adapter. Do not invoke providers separately, copy generated implementation files between projects or targets, or refresh stale provenance by hand.

### 5. Verify the complete target

```bash
cott verify --project "$project" --format json
```

`verify` rebuilds without a result cache, rejects unresolved work and source/managed drift, checks exact signatures and provenance, audits facade-only consumption, exercises supported contracts and scenarios, records semantic coverage, and runs the real selected target verifier:

- Python: CPython and BasedPyright against the complete generated package.
- Kotlin: kotlinc/JDK/JAR inputs plus the sandboxed public-facade runner.
- Dart: offline pub resolution where configured, analyzer/kernel compilation, and the sandboxed public-facade runner after Landlock confinement.

`verify` does not repair sources or managed files; run `emit` or `generate` first. Only report the project as releasable when full verification succeeds. Exit `8` means certification evidence was recorded but the selected semantic-coverage policy gate failed, so release and deployment still fail.

### 6. Review compatibility

```bash
cott diff --project "$project"
cott diff --exit-code --project "$project"
```

Use `--baseline path/to/generation.json` for an explicit saved baseline. Without `--exit-code`, reported differences return success. With it, a breaking or version-incompatible change returns exit `7`.

Cott classifies removals and contract, type, or effect changes conservatively as breaking. For a project API version, breaking changes require at least a minor bump while major is `0`, otherwise a major bump; additive public changes require at least a minor bump.

### 7. Deploy a verified snapshot

```bash
cott deploy --project "$project" --format json
cott deploy --output path/to/new-package --project "$project" --format json
```

The default destination is `<project>/dist/<name>-<version>/`. Relative `--output` is resolved from the calling working directory. Deployment never overwrites an existing destination and never generates, re-verifies, invokes an agent, or infers application resources. Payloads differ by target; follow [targets and deployment](references/targets-and-deployment.md).

## Editor integration

Run the stdio language server with no options or operands from a Cott project:

```bash
cott lsp
```

It provides diagnostics, completion, hover, and definition for open documents. It never emits, publishes, or invokes an agent.

## Completion checklist

- `.cott` and `cott.toml` remain the contract and configuration sources; exactly one target is selected.
- `cott check` succeeds project-wide.
- `cott fmt --check` succeeds.
- Compiler-owned output was refreshed with `emit` or `generate`, never edited manually.
- Every implementation uses the exact prompted target signature and remains in its owned source path.
- Public consumers use generated facades only.
- `cott verify` succeeds for the full selected target and coverage policy.
- `cott diff --exit-code` and the project API version agree with the intended compatibility change when a baseline exists.
- If packaging was requested, `cott deploy` publishes to a new destination and the consumer uses only that target payload.
