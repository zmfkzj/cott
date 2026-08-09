# cott

`cott` is a Rust compiler for a contract-first DSL. The `.cott` module is the source of truth; a
local typed Python binding is copied into a generated package and loaded through the generated
public facade.

`architecture.md` is the executable v0.1 contract. The compiler implements the CST → AST → HIR →
Canonical IR → deterministic Python pipeline, durable manifest or generated implementations,
contract-aware facades, provenance, atomic publication, and exact verification.

## Run an example

From the repository root:

```bash
cargo run -- emit python --project examples/grammar/boolean-identity
cargo run -- verify --project examples/grammar/boolean-identity
PYTHONPATH=examples/grammar/boolean-identity/generated/python \
  examples/grammar/boolean-identity/.venv/bin/python -c 'from curriculum.boolean_identity import run; print(run())'
# True
```

`cott emit python` atomically publishes the complete compiler-owned managed set and records
`current.verified = false`. `cott verify` regenerates it in staging, checks exact managed bytes,
BasedPyright, verified-loader runtime signatures, dependency provenance, and deterministic pure
contract cases, then records the same snapshot as `current` and `last_verified`.

The Python target is fixed to CPython 3.14.6, BasedPyright 1.39.9, and uv 0.12.3. `cott init`
provisions that environment; existing projects must supply the configured interpreter and checker.

## Command surface

```text
cott init <path> [--name <name>] [--no-sync] [--format json]
cott check [<source.cott>] [--project <dir>] [--format json]
cott fmt [--check] [--project <dir>] [--format json]
cott emit ir|python [--project <dir>] [--format json]
cott generate [<fully.qualified.function>] --agent codex|omp --target python [--project <dir>] [--format json]
cott verify [--project <dir>] [--format json]
cott diff [--baseline <generation.json>] [--exit-code] [--project <dir>] [--format json]
```

Run the binary through Cargo during development (`cargo run -- …`). `generate` invokes only the
explicitly selected, pinned Codex or OMP CLI and publishes a candidate only after scoped staging
validation.

## Project layout

Every example is an independent project:

```text
examples/<category>/<slug>/
├── cott.toml
├── src/curriculum/<slug>.cott
└── python/_cott_impl/curriculum/<slug>/run.py
```

The manifest is intentionally closed:

```toml
[project]
name = "example-name"
version = "0.1.0"
source = "src"

[target.python]
source = "python"
generated = "generated/python"
stubs = "generated/stubs"
interpreter = ".venv/bin/python"
type_checker = ".venv/bin/basedpyright"
runtime_validation = "boundary"
```

Emission writes these compiler-owned artifacts below `generated/`:

```text
ir/                 canonical JSON IR
generation.json     planned artifact hashes
python/             runtime, public facades, types, and verified binding copies
stubs/              tool-only Python stubs
```

Never edit `generated/`; change the `.cott` contract or durable implementation, then emit again.
Manifest bindings use `[target.python.implementations]`; unresolved functions may instead be filled
under `python/_cott_impl/` by `cott generate`. Implementations are regular single-link UTF-8 files
with one fully annotated top-level function. Standard-library, exact generated type-module, and
lock-selected external imports are supported; dynamic, relative, star, reflective, agent, and
placeholder operations are rejected.

## Example catalog

The examples remain small deterministic programs, but they compile through the full v0.1 semantic
and Python pipeline.

| Category | Example | Entry module | Observed output |
| --- | --- | --- | --- |
| Grammar | `boolean-identity` | `curriculum.boolean_identity` | `True` |
| Grammar | `signed-addition` | `curriculum.signed_addition` | `5` |
| Grammar | `positive-counter` | `curriculum.positive_counter` | `PositiveCount(value=3)` |
| Grammar | `named-timestamp` | `curriculum.named_timestamp` | `7` |
| Grammar | `record-echo` | `curriculum.record_echo` | `Message(text='hello', sequence=7)` |
| Grammar | `priority-selection` | `curriculum.priority_selection` | `Priority_High()` |
| Grammar | `optional-label` | `curriculum.optional_label` | `Some(value="enabled")` |
| Grammar | `result-division-guard` | `curriculum.result_division_guard` | `Err(error=DivideError_ZeroDivisor())` |
| Grammar | `unit-echo` | `curriculum.unit_echo` | `UNIT` |
| Grammar | `constant-greeting` | `curriculum.constant_greeting` | `"hello"` |
| Simple | `normalize-flag` | `curriculum.normalize_flag` | `True` |
| Simple | `clamp-score` | `curriculum.clamp_score` | `0.75` |
| Simple | `increment-count` | `curriculum.increment_count` | `42` |
| Simple | `greeting-length` | `curriculum.greeting_length` | `4` |
| Simple | `byte-count` | `curriculum.byte_count` | `ByteCount(data=b'abc', count=3)` |
| Simple | `nonempty-name` | `curriculum.nonempty_name` | `NonemptyName(value='Ada')` |
| Simple | `default-nickname` | `curriculum.default_nickname` | `Nothing()` |
| Simple | `parity-classification` | `curriculum.parity_classification` | `Parity_Odd()` |
| Simple | `checked-subtract` | `curriculum.checked_subtract` | `Ok(value=5)` |
| Simple | `message-sequence` | `curriculum.message_sequence` | `Message(text='x', sequence=5)` |
| Complex | `validated-user-card` | `curriculum.validated_user_card` | `Ok(value=UserCard(...))` |
| Complex | `retry-configuration` | `curriculum.retry_configuration` | `RetryConfiguration(...)` |
| Complex | `order-state-transition` | `curriculum.order_state_transition` | `Ok(value=OrderState_Paid(receipt='r1'))` |
| Complex | `profile-summary` | `curriculum.profile_summary` | `ProfileSummary(...)` |
| Complex | `transfer-decision` | `curriculum.transfer_decision` | `Ok(value=TransferDecision_Accepted())` |
| Complex | `address-validation` | `curriculum.address_validation` | `Ok(value=Address(...))` |
| Complex | `contact-preference` | `curriculum.contact_preference` | `ContactPreference_Email()` |
| Complex | `subscription-activation` | `curriculum.subscription_activation` | `Ok(value=Subscription(...))` |
| Complex | `invoice-decision` | `curriculum.invoice_decision` | `InvoiceDecision_Rejected(reason='missing tax id')` |
| Complex | `access-grant` | `curriculum.access_grant` | `Ok(value=AccessGrant_Granted())` |

## Development

```bash
cargo fmt --check
cargo test
```

The test suite covers lossless parsing and formatting, HIR and contract validation, canonical IR,
closed manifests and source discovery, sandboxing, transactions, agent adapters, provenance,
deterministic artifacts, generated runtime behavior, CLI publication, diff, and verification.
