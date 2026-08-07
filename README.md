# cott

`cott` is a Rust compiler for a contract-first DSL. The `.cott` module is the source of truth; a
local typed Python binding is copied into a generated package and loaded through the generated
public facade.

`architecture.md` remains the v0.1 design authority. The executable implementation is deliberately
smaller: it supports a closed project manifest, parsing, constrained semantic analysis, canonical
IR, durable binding validation, deterministic Python emission, and byte-for-byte verification.

## Run an example

From the repository root:

```bash
cargo run -- emit python --project examples/grammar/boolean-identity
cargo run -- verify --project examples/grammar/boolean-identity
cd examples/grammar/boolean-identity/generated/python
python3 -m curriculum.boolean_identity
# True
```

`cott emit python` atomically replaces the compiler-owned `generated/` tree only after a complete
plan is written to staging. `cott verify` rebuilds that plan in memory and rejects missing, extra,
or modified managed artifacts. Standard `__pycache__/*.pyc` files produced by Python are ignored;
other unexpected artifacts fail verification. It does not edit generated files.

The compiler does not provision Python. Run the generated entry module with a supplied Python that
supports the generated standard-library runtime.

## Current command surface

```text
cott emit python [--project <dir>]
cott verify [--project <dir>]
```

Run the binary through Cargo during development (`cargo run -- …`). `init`, `check`, `fmt`,
`generate`, `diff`, dependency locking, agent execution, runtime contract checking, and type-checker
integration are design-specified but not implemented commands.

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
source = "src"

[target.python]
generated = "generated/python"
entry = "curriculum.example.run"
```

Emission writes these compiler-owned artifacts below `generated/`:

```text
ir/                 canonical JSON IR
generation.json     planned artifact hashes
python/             runtime, public facades, types, and verified binding copies
stubs/              tool-only Python stubs
```

Never edit `generated/`; change the `.cott` contract or the durable binding, then emit again.
Bindings must be regular UTF-8 files with one annotated top-level zero-argument function. They may
import the standard library, `cott_runtime`, or that module's generated `*_types` module; dynamic,
relative, star, agent, and placeholder imports/operations are rejected.

## Example catalog

The current Profile-P slice accepts signature-only, zero-argument public functions. The examples
are deterministic executable snapshots of their named domain shape; titles such as “validation” or
“transition” do **not** claim parameterized contract enforcement yet. That work belongs to the
unimplemented contract-clause/runtime-validation path.

| Category | Example | Entry module | Observed output |
| --- | --- | --- | --- |
| Grammar | `boolean-identity` | `curriculum.boolean_identity` | `True` |
| Grammar | `signed-addition` | `curriculum.signed_addition` | `5` |
| Grammar | `positive-counter` | `curriculum.positive_counter` | `PositiveCount(value=3)` |
| Grammar | `named-timestamp` | `curriculum.named_timestamp` | `7` |
| Grammar | `record-echo` | `curriculum.record_echo` | `Message(text='hello', sequence=7)` |
| Grammar | `priority-selection` | `curriculum.priority_selection` | `High()` |
| Grammar | `optional-label` | `curriculum.optional_label` | `Some(value="enabled")` |
| Grammar | `result-division-guard` | `curriculum.result_division_guard` | `Err(error=ZeroDivisor())` |
| Grammar | `unit-echo` | `curriculum.unit_echo` | `UNIT` |
| Grammar | `constant-greeting` | `curriculum.constant_greeting` | `"hello"` |
| Simple | `normalize-flag` | `curriculum.normalize_flag` | `True` |
| Simple | `clamp-score` | `curriculum.clamp_score` | `0.75` |
| Simple | `increment-count` | `curriculum.increment_count` | `42` |
| Simple | `greeting-length` | `curriculum.greeting_length` | `4` |
| Simple | `byte-count` | `curriculum.byte_count` | `ByteCount(data=b'abc', count=3)` |
| Simple | `nonempty-name` | `curriculum.nonempty_name` | `NonemptyName(value='Ada')` |
| Simple | `default-nickname` | `curriculum.default_nickname` | `Nothing()` |
| Simple | `parity-classification` | `curriculum.parity_classification` | `Odd()` |
| Simple | `checked-subtract` | `curriculum.checked_subtract` | `Ok(value=5)` |
| Simple | `message-sequence` | `curriculum.message_sequence` | `Message(text='x', sequence=5)` |
| Complex | `validated-user-card` | `curriculum.validated_user_card` | `Ok(value=UserCard(...))` |
| Complex | `retry-configuration` | `curriculum.retry_configuration` | `RetryConfiguration(...)` |
| Complex | `order-state-transition` | `curriculum.order_state_transition` | `Ok(value=Paid(receipt='r1'))` |
| Complex | `profile-summary` | `curriculum.profile_summary` | `ProfileSummary(...)` |
| Complex | `transfer-decision` | `curriculum.transfer_decision` | `Ok(value=Accepted())` |
| Complex | `address-validation` | `curriculum.address_validation` | `Ok(value=Address(...))` |
| Complex | `contact-preference` | `curriculum.contact_preference` | `Email()` |
| Complex | `subscription-activation` | `curriculum.subscription_activation` | `Ok(value=Subscription(...))` |
| Complex | `invoice-decision` | `curriculum.invoice_decision` | `Rejected(reason='missing tax id')` |
| Complex | `access-grant` | `curriculum.access_grant` | `Ok(value=Granted())` |

## Development

```bash
cargo fmt --check
cargo test
```

The test suite covers parsing, semantic/profile rejection, canonical IR determinism, manifest and
source discovery, binding provenance, artifact emission, CLI publish/verify behavior, and a
conditional generated-Python smoke path.
