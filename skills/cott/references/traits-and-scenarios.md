# Authoring traits, resources, and scenarios

Read this reference only when the public contract needs stateful trait implementations or finite scenario evidence. For ordinary data and functions, use [authoring-basics.md](authoring-basics.md) and [contracts-and-effects.md](contracts-and-effects.md).

## Model a state machine as a resource

Declare the allowed states and transitions; do not encode lifecycle strings in implementation code:

```cott
resource TaskLifecycle:
    initial Pending
    state Pending
    state Completed
    terminal Completed
    transition Pending -> Completed
```

A terminal state has no implicit self-transition. If repeated completion is valid, it needs an explicit public transition; otherwise the generated boundary rejects it.

## Declare behavior as traits

Traits may expose associated types, inherit other traits, and use type parameters:

```cott
trait Summarizable:
    type Summary
    async fn summary(self) -> Summarizable.Summary

trait Prioritizable:
    async fn priority_level(self) -> I32

trait TaskView[+T] for Summarizable + Prioritizable:
    async fn display(self) -> T
    async fn category(self) -> Str = curriculum.trait_protocol.default_category
```

Use an exact dynamic trait view when runtime polymorphism is part of the API:

```cott
async fn inspect_dyn(item: Dyn[TaskView[Str]]) -> Str:
    effects []
```

Do not add a trait for a single bodyless top-level function. A plain function is the smaller contract.

## Specialize and implement exact trait identities

A specialization selects a helper for one concrete slot:

```cott
specialize SimpleTask for TaskView[Str]:
    display = curriculum.trait_protocol.specialized_display
```

The implementation owns typed state, construction clauses, invariants, and methods:

```cott
impl SimpleTask for TaskView[Str] + Completable:
    type Summary = Str
    state:
        title: Str
        urgency: I32
        lifecycle: TaskLifecycle
        completion_count: I32 = 0

    invariant self.title.len > 0
    invariant self.urgency >= 0
    invariant self.completion_count >= 0

    init(title: Str, urgency: I32):
        requires title.len > 0
        requires urgency >= 0
        ensures self.title == title
        ensures self.urgency == urgency

    async fn complete(self) -> Bool:
        transitions self.lifecycle: TaskLifecycle.Pending -> TaskLifecycle.Completed
        modifies self.completion_count
        ensures result == true
        ensures old(self.completion_count) + 1 == self.completion_count
        effects []
```

`transitions` owns the resource-field change. `modifies` names other mutable state explicitly. Use `old(...)` only to relate post-state to pre-state.

Associated types and const generics project differently on erased or reified target runtimes. Keep their meaning in the Cott declaration; do not hand-invent Kotlin reflection wrappers or Dart runtime-type conventions. Follow [targets and deployment](targets-and-deployment.md) for generated target boundaries.

## Use scenarios for finite public behavior

A scenario calls public facades and asserts only public values. Keep reusable inputs as typed constants:

```cott
const OLD_REQUEST_ID: U64 = 1
const NEW_REQUEST_ID: U64 = 2
const OLD_QUERY: Str = "old"
const NEW_QUERY: Str = "new"

scenario latest_result_wins:
    call old_state = begin_search(OLD_REQUEST_ID, OLD_QUERY)
    spawn old_worker = resolve_search(OLD_REQUEST_ID, OLD_QUERY)
    tick
    await old_worker as old_result
    call newest_state = begin_search(NEW_REQUEST_ID, NEW_QUERY)
    spawn new_worker = resolve_search(NEW_REQUEST_ID, NEW_QUERY)
    tick
    await new_worker as new_result
    call applied = apply_search(newest_state, new_result)
    call protected = apply_search(applied, old_result)
    assert protected.request_id == NEW_REQUEST_ID
```

Available patterns demonstrated by `examples/features/workflow-scenario` are:

- `call name = function(...)` for synchronous facade calls.
- `spawn worker = async_function(...)` to start finite async work.
- `tick` to advance the controlled schedule.
- `await worker as value` to join successfully.
- `cancel worker` followed by `await worker cancelled` to observe cancellation.
- `assert expression` for public outcomes.

Do not use sleeps, host clocks, framework objects, private target implementation paths, or generated internals to drive a scenario.

## Use compiler-owned fixtures for effects

Filesystem fixtures and injected failures:

```cott
scenario filesystem_replace_failure:
    fixtures:
        fs files:
            file "input.txt" text("new text")
            file "output.txt" text("old text")
        failure disk_full:
            point: file.replace
            occurrence: 1
            error: disk_full
    call failed = copy_text(files.path("input.txt"), files.path("output.txt"))
    call preserved = read_text(files.path("output.txt"))
```

Isolated local HTTP fixtures:

```cott
fixtures:
    http service:
        route "/utf8" -> response(status: 200, body: text("café"), encoding: "utf-8")
        route "/redirect" -> redirect(status: 302, location: "/utf8")
```

Deterministic clock fixtures:

```cott
fixtures:
    clock clock:
        start_ms: 17
        tick_ms: 1
```

Declare the corresponding function effects exactly as described in [contracts-and-effects.md](contracts-and-effects.md). Fixture identities live in the scenario, not in host configuration.

## Keep evidence meaningful

- Assert through public fields or small public observation facades.
- Cover ordering, cancellation, state protection, and injected failure only when they are contractual behavior.
- Do not inspect Python `_cott_impl`/`cott_bindings`, Kotlin `cott_impl`/`cott_bindings`, Dart private parts, or runtime-private fixture state.
- Do not add a scenario that merely repeats an `ensures` clause without exercising a distinct case.
- An unavailable isolated fixture remains `unobserved`; never weaken containment to force a pass.

Use these maintained references for full syntax:

- Python: `examples/features/trait-protocol/src/curriculum/trait_protocol.cott`
- Python: `examples/features/workflow-scenario/src/curriculum/workflow_scenario.cott`
- Python: `examples/features/effects-selection/src/curriculum/effects_selection.cott`
- Kotlin equivalents: `examples/kotlin/features/trait-protocol/`, `examples/kotlin/features/workflow-scenario/`, and `examples/kotlin/features/effects-selection/`
