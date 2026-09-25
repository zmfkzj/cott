# Cott Example Authoring

These rules apply to every project under `examples/`. The root `AGENTS.md` and `architecture.md`
remain authoritative for language, ABI, record and toolchain behavior. This file defines how to
write example contracts so that each example demonstrates what Cott is for.

## Purpose

Cott's center:

> The author owns types, structure and core intent. The selected agent writes the
> implementation. Cott checks what it can and reports, without inflation, what it has not
> checked.

An example is a program: typed data and functions composed through generated public facades,
whose content is contracts. It is neither a list of signatures with prose attached nor the program
rewritten in checkable form. A contract is adequate when all three hold:

1. A type-correct hollow or wrong implementation fails something the example declares or runs.
2. The intended implementation passes.
3. Whatever nothing checks is still reported as unchecked.

Authoring effort is a cost. Choose the cheapest check that rejects plausible wrong
implementations. Never add clauses, scenarios, waivers or README claims to improve counts.

## Where intent belongs

| Intent | Write it as | Not as |
| --- | --- | --- |
| Valid values and states | refined `newtype`, enums instead of boolean flags, `Option`/`Result`, struct `invariant` | prose validity rules |
| Output relation to inputs | `requires`, `ensures`, `ensures table`, `ensures preserves`, closed intrinsics | restated algorithm steps |
| Failures decidable from inputs, and their priority | `error V when ...` or `error V with ... matches ...` in priority order; `errors complete` when these conditions are the whole failure specification | bare `error V` |
| Environment failures (I/O, network) | bare `error V`, observed through a `failure` fixture scenario where a backend exists | disguised domain conditions |
| Concrete behavior, formats, composition | scenarios with `data` values and `matches` assertions | public helpers that exist only for scenarios |
| Obligations formal clauses cannot state | `requirement`, linked with `checked_by` when a scenario provides evidence | README-only rules, behavioral `cott-domain` lines |
| External premises, accepted temporary gaps | `assumption`, `waiver` | disclaimers meant to turn reports green |
| Definitions, units, rationale | `doc` | type-checker or SDK tips |
| Target technique (how, not what) | `generator.rules` | behavior, limits, formats, error mapping, priorities |
| Program behavior whose effects have no fixture backend | labeled external program regression under `tests/` | Cott scenario evidence |

## Authoring order

1. Model the domain with types before writing functions. A type that makes an invalid state
   unrepresentable replaces paragraphs of `doc`.
2. Order each module as types, small leaves, compositions, then the domain-named operation
   (architecture §16.10). Expose a stage only at a meaningful boundary.
3. For every public callable, list the type-correct wrong implementations that would pass today:
   an empty or default result, the first declared error for every input, the input echoed back, a
   skipped facade call, a constant, the right items in the wrong order or multiplicity. Pick the
   cheapest check that rejects the plausible ones: a one-line clause, else a small scenario, else
   a `requirement` that remains `unverified`. Treat this as a design question, not a gate applied
   to every function, and do not rebuild the algorithm as a specification.
4. Write `doc` for what types and clauses leave unsaid: definitions, units, formats, ordering,
   limits, atomicity and failure mapping.
5. Specify composition roots explicitly (see Programs and composition roots).
6. Inspect `cott prompt <module.callable>`. The agent must learn everything it needs from FORMAL
   DECLARATIONS and CURRENT INTENT, never from generator rules that restate behavior.

## Formal clauses

Relate results to inputs:

```cott
fn order_steps(steps: List[BuildStep]) -> Result[List[Str], PipelineError]:
    ensures Result.Ok(order) => permutation_by(order, steps, BuildStep.name)
    ensures Result.Ok(order) => dependency_ordered_by(order, steps, BuildStep.name, BuildStep.needs)

    errors complete
    error PipelineError.BlankStepName when any_blank_by(steps, BuildStep.name)
    error PipelineError.DuplicateStep when not unique_by(steps, BuildStep.name)
    error PipelineError.UnknownDependency when unknown_dependency_by(steps, BuildStep.name, BuildStep.needs)
    error PipelineError.SelfDependency when self_dependency_by(steps, BuildStep.name, BuildStep.needs)
    error PipelineError.Cycle when cyclic_by(steps, BuildStep.name, BuildStep.needs)

    effects []
```

Use the sugar when it states the whole mapping, separate caller duties from reported failures,
and put the facts callers rely on into the success value:

```cott
fn repository(channel: Channel) -> Str:
    ensures table channel:
        Channel.Stable => "yt-dlp/yt-dlp"
        Channel.Nightly => "yt-dlp/yt-dlp-nightly-builds"

    effects []

fn relabel(mark: Mark, label: Str) -> Mark:
    ensures preserves result from mark except label
    ensures result.label == label

    effects []

fn take(values: List[U32], count: U64) -> Result[List[U32], SliceError]:
    requires count > 0

    ensures Result.Ok(part) => part.len == count

    error SliceError.OutOfBounds when count > values.len

    effects []

fn transfer(request: TransferRequest) -> Result[TransferReceipt, TransferError]:
    ensures Result.Ok(receipt) => receipt.destination == request.destination
    ensures Result.Ok(receipt) => receipt.bytes_written <= request.max_bytes

    error TransferError.InvalidLimit when request.max_bytes == 0
    error TransferError.NetworkFailed

    effects [network, file.write]
```

- Every obligation must be falsifiable by some wrong output. Do not write `x.len >= 0`, `n >= 0`
  on unsigned values, `saved == ()` as a behavioral claim, or `Result.Ok(v) =>` conditions that
  ignore `v`. Bounds such as `selected.len <= items.len` are fine beside a real property but never
  as the only one: the empty and identity implementations satisfy them.
- A `Result` with `error` clauses needs one guarded `ensures Result.Ok(v) => ...` (compiler
  lint). Relate `v` to the inputs. If the success value carries nothing checkable, prefer a
  receipt type that exposes the facts callers rely on (destination, byte count, identity). If
  `Unit` is genuinely right, keep the required clause, mark it as structural in a `#` comment and
  carry the duty in a scenario or requirement.
- `requires` is the caller's duty; a violation is a contract violation, not a `Result`. Report
  failures the callee can decide from its inputs as conditional errors.
- Conditional errors are evaluated in source order and the first applicable clause decides the
  variant. Write them in priority order.
- Opt into `errors complete` only when the conditional errors are the entire failure
  specification of a free function. The clause goes after `ensures` and before `error`. It
  rejects bare errors and requires `Ok` for every requires-valid input with no applicable
  condition. With no conditions at all, the function must always succeed. It is a runtime
  obligation, not a termination or correctness proof.
- Closed intrinsics work in every contract expression and in scenario assertions. At the start of
  an unguarded `ensures`, parenthesize the call, as in `ensures (contains(result, "id"))`;
  otherwise it parses as a match guard. Their exact semantics are in architecture §10.4.1: blank
  means the fixed 25-character Unicode White_Space set, multiplicity counts, and unknown
  dependencies add no edge. Never describe them with a target's `strip` or `trim`.
- Contracts have no callee references, quantifiers, indexing, method calls or value
  constructors. Put such properties in scenarios or requirements, never in generator rules.

## Scenarios

```cott
data chain: Pipeline = Pipeline(
    steps: List(
        BuildStep(name: "package", needs: Set("compile")),
        BuildStep(name: "compile", needs: Set("parse")),
        BuildStep(name: "parse", needs: Set()),
    ),
)

scenario chain_orders_dependencies_first:
    call plan = plan_pipeline(chain)
    assert plan matches Result.Ok(value) => value.ordered_steps == List("parse", "compile", "package")

scenario cycle_is_rejected:
    call plan = plan_pipeline(
        Pipeline(
            steps: List(
                BuildStep(name: "a", needs: Set("b")),
                BuildStep(name: "b", needs: Set("a")),
            ),
        ),
    )
    assert plan matches Result.Err(PipelineError.Cycle)

scenario independent_steps_succeed:
    data steps: List[BuildStep] = List(
        BuildStep(name: "b", needs: Set()),
        BuildStep(name: "a", needs: Set()),
    )
    call order = order_steps(steps)
    assert order matches Result.Ok(_)

scenario replace_failure_preserves_previous_bytes:
    fixtures:
        fs files:
            file "out.txt" text("old")
        failure disk_full:
            point: file.replace
            occurrence: 1
            error: disk_full
    call written = replace_text(files.path("out.txt"), "new")
    assert written matches Result.Err(StoreError.WriteFailed)
    call kept = read_text(files.path("out.txt"))
    assert kept matches Result.Ok(text) => text == "old"
```

- Scenarios call public facades only, have at most 64 steps and use the closed fixtures `fs`,
  `http`, `clock` and `failure`. Every effect of a called facade needs a compatible fixture, and
  every declared fixture must be used. Facades with `random`, `process.exit`, `database.*` or
  custom effects cannot be called.
- An impl initializer is a public facade call: `call task = SimpleTask(title: "x", urgency: 1)`.
  Call selected instance methods on that binding: `call label = task.summary()`. Do not import or
  instantiate private implementation classes; method arguments exclude the receiver.
- `data view: Dyn[TaskView[Str]] = Dyn(value: task)` wraps a previously constructed or
  returned impl instance with the expected trait. Use the same closed value form in a facade
  argument or assertion; it is not an arbitrary target-language cast.
- Module-level `data` names are snake_case templates. They are type-checked even when unused and
  inlined into each scenario with fixture references rebound. Scenario-level `data` is evaluated
  once and reused. Value constructors are available only in scenario arguments, `data` and
  assertions.
- `assert x matches Pattern => condition` fails when the pattern does not match, and its bindings
  exist only in that condition. Check the payload, not just the variant, whenever the
  specification fixes it.
- Derive expected values from the specification, never from running the current implementation.
- Every example manifest uses `runtime_validation = "boundary"`, so each scenario call also
  evaluates the facade's `requires`, `ensures`, allowed errors and conditional error obligations.
  Do not restate those relations in assertions; assert what they leave open. When several outputs
  are valid, assert only such open properties (`matches Result.Ok(_)`, or an intrinsic predicate
  the contract does not already state), or choose inputs with exactly one valid answer. Pinning
  one arbitrary answer silently adds a requirement.
- For effects, assert both the result and the resulting state read back through a facade. Use a
  `failure` fixture to check that the previous state survives.
- Facade observations made during scenario calls count as clause evidence. Automatic candidates
  never execute effectful callables, whose clauses remain `trust_declaration` unless a scenario
  observes them, and cannot construct inputs for some predicates (`unsupported_expression`). Add
  a small scenario for each condition you need observed.
- The Python fixture clock is in milliseconds (`start_ms`). State units and conversions in the
  contract.
- Do not add public `*_is_ok`-style helpers to observe results; pattern assertions replace them.

## Requirements

```cott
requirement CYCLE_IS_REJECTED for plan_pipeline:
    text "A cyclic pipeline is rejected rather than returned as a partial plan."
    checked_by cycle_is_rejected assert 1

requirement ERRORS_OMIT_SECRETS for transfer:
    text "Error messages never include credentials, response bodies or query strings."
    assumption "The HTTP client does not copy request headers into exception text."
```

- Use requirements for obligations clauses cannot state, such as composition duties, secrecy,
  atomicity and cleanup, and cross-call protocols. Do not restate formal clauses.
- The ID is `<module>.requirement.<NAME>` with an UPPER_SNAKE name. The target is a local free
  function.
- `text` and `assumption` enter CURRENT INTENT and the intent fingerprint, so editing them queues
  regeneration. `checked_by` links and waivers do not.
- `checked_by <scenario>` covers all assertions of that scenario; `assert N` covers the N-th
  assertion (1-based). Link only checks that exercise the statement. Reordering assertions makes
  previous evidence stale.
- Status is the worst link: `failed` > `unknown` > `unverified` > `observed`. `observed` is bounded
  evidence, not proof. An unlinked requirement is `unverified`, which is an honest result; do not
  add weak scenarios just to change it.
- `assumption` records an external premise; `waiver` records a temporary exception with an
  owner. Neither changes a status. Do not use either as a disclaimer.

## `doc` and generator rules

- `doc` is normative intent in CURRENT INTENT. Do not demote behavior to comments or the README.
  Prescribe a technique only when the technique itself is required, for example no-follow,
  descriptor-relative file replacement.
- Turn a crisp obligation in `doc` into a clause or a `requirement` when feasible. K101 warnings
  are hints, never gates.
- `generator.rules` holds only target technique that the compiler's output rules do not already
  state, such as satisfying the pinned type checker around an untyped SDK. When a generation retry
  exposes an SDK pitfall that affects correctness (for example a cursor that silently opens a
  separate transaction), state the required behavior in the contract and keep only the technique
  in rules. Add no behavioral `cott-domain` lines, and migrate existing ones when you edit an
  example.

## Programs and composition roots

- `complex/` and `real/` examples are programs. A domain-named operation composes the leaves
  through facades, and a CLI keeps `run` thin: parse, execute, print, exit.
- Specify each root: the participating facades, the data flow, failure propagation, the stages
  each mode skips and the contents of the result. Back these responsibilities with requirements.
  An unspecified root is how `real.yt_dlp.execute` once verified while returning an empty report.
- Design for observability. Keep effect leaves narrow, separate pure planning from effects, and
  pass nondeterminism as an explicit input (for example a seed) when the domain allows, because
  `random` has no fixture backend.
- Exercise roots with scenarios when their effects are fixture-compatible. Otherwise add an
  external program regression that follows `tests/yt_dlp_program.rs`. It runs the `cott deploy`
  output with real generated facades in the isolated-loopback sandbox, against local HTTP and
  scratch files, and is labeled `external_program_regression`. Its type-valid defect
  implementations are bound only in throwaway copies. It never counts as Cott evidence, so its
  requirements stay `unverified` unless a Cott check is linked.
- End-to-end checks must not mock internal leaves. Label checks that do as composition checks.

## Generate, verify, report

```sh
cott check --project <project>
cott fmt --project <project>
cott prompt <module.callable> --project <project>
cott generate --agent omp --target python -j 3 --project <project>
cott verify --project <project>
cott requirements --project <project> --format json
```

- `generated/` and the agent-owned `python/_cott_impl/`, `kotlin/cott_impl/` and `dart/cott_impl/`
  sources are results. Change the contract and regenerate; never edit them or bless hashes.
- Only `grammar/checked-add` selects a manifest binding. Never add bindings or `cott_bindings/`
  sources to get past a generation, run or verification failure.
- Do not rebuild the compiler while `generate` or `verify` runs. Generation records the compiler
  executable's hash when it publishes, and replacing the binary mid-run breaks publication.
- `examples/generate.sh` runs emit and generate for every example without verify or deploy.
  `COTT_BIN` selects the compiler.
- Contract tests run in the Linux bubblewrap sandbox. Scenarios with `http` fixtures run in
  isolated loopback, which also needs `/usr/sbin/ip` and `/usr/bin/setpriv`. Missing capability
  yields `unobserved` evidence, never host networking. Kotlin native tests need
  `COTT_KOTLIN_HOME` and `JAVA_HOME`; run them with `--test-threads=1` on memory-limited hosts.
  Dart native tests need `COTT_DART`.

Report results without inflation:

- `verified` means artifacts, types, runtime checks, proofs and runner evidence certified this
  snapshot. It does not mean the program is correct or ready for release.
- Clause statuses are `observed` (bounded observation), `unobserved`, `trust_declaration` and
  `unknown`. Coverage policy `selected: 0` means no clause is policy-gated.
- READMEs state what is formally specified, what scenarios or labeled regressions observe, and what
  remains unverified. Never write "proved" or "guaranteed" without a proof status. Keep
  `README.kr.md` in sync where it exists.
- Curriculum READMEs use `# <name>`, `## Purpose` and `## Key points`; feature READMEs start with
  `## Purpose`. A real-world README starts with `# <canonical upstream URL>`; the next nonblank
  line must contain "Cott reimplementation", and the introduction states what is not
  reimplemented.

## By category

- `grammar/`: one construct per lesson in the smallest meaningful program. Its clauses must still
  reject wrong implementations.
- `simple/`: two or three leaves and a composition. Add a scenario over the composed path unless
  clauses already reject a hollow composition, and propagate errors unchanged.
- `complex/`: `artifact-pipeline` is the pure-algorithm reference: relational predicates,
  `errors complete`, scenarios per error condition and linked requirements. Its independent
  oracle remains separate acceptance evidence. `process-bar` stays the full-generation fixture.
- `features/`: each project must actually exercise its feature. Evidence expectations accept
  capability-limited `unobserved` with its reason.
- `modular/`: each module owns its types, composition crosses facades, and the end-to-end scenario
  lives in the top module.
- `integrations/`: contracts cover the Cott module boundary. Gradle, Flutter and FastAPI own
  platform concerns. Claim nothing beyond recorded evidence.
- `real/`: generation-first with no bindings, and host boundaries are agent implementations.
  Specify the root, link what scenarios can observe and use external regressions for the rest.
- `kotlin/` and the Dart package: the same principles apply. Lessons that mirror Python lessons
  stay semantically aligned, although tests do not enforce it. Keep target differences explicit,
  such as Kotlin's nanosecond fixture clock read versus the Python millisecond adapter.

## Before finishing an example change

- [ ] Types carry the constraints, and enums replace boolean state flags.
- [ ] Each public callable rejects its plausible hollow implementations or has an explicit
      `unverified` requirement.
- [ ] No success obligation is tautological or ignores the success value.
- [ ] Failures decidable from inputs are conditional errors in priority order.
- [ ] Composition roots are specified and exercised by a scenario or a labeled external regression.
- [ ] Scenario expectations come from the specification, without observation helpers or an
      arbitrary choice among valid answers.
- [ ] `generator.rules` states no behavior.
- [ ] `check`, `fmt --check`, `generate` (when intent changed), `verify` and `requirements` ran,
      and the README reports the evidence honestly.
- [ ] Nothing under `generated/` or `*_impl/` was edited by hand, and no binding was added.
