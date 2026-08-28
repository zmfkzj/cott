# trait-protocol

## Purpose
This end-to-end example keeps the Cott v0.3 Protocol/generic-function lesson while showing a Cott-owned ordinary `SimpleTask` class whose method bodies are implemented by an agent.

## Protocols and the concrete implementation
- `Summarizable` has the associated `Summary` type and requires `summary() -> Summarizable.Summary`; `SimpleTask` assigns `Summary = Str`. `Prioritizable` requires `priority_level() -> I32`, and `Completable` requires `complete()`. `format_summary[T: Summarizable]` accepts only the summary protocol; `inspect_task[T: Summarizable + Prioritizable]` requires both read protocols.
- `TaskLifecycle` is a resource with initial `Pending`, terminal `Completed`, and its declared `Pending -> Completed` edge. `impl SimpleTask for Summarizable + Prioritizable + Completable` declares `title: Str`, `urgency: I32`, and `lifecycle: TaskLifecycle`, rather than asking the Python application to handwrite a class.
- The compiler owns the generated class shell, resource-state initialization, lock, and contract wrappers. The agent owns only the generated method helper implementations, so application code imports `SimpleTask` from the generated module.

## Contracts and observable behavior
- The class invariant requires a nonempty title and nonnegative urgency. `init(title, urgency)` repeats those preconditions and ensures the initialized title and urgency match its arguments; the omitted `lifecycle` parameter receives the resource initial state, `TaskLifecycle.Pending`.
- `summary` and `priority_level` are pure, contracted read methods. `complete`'s mandatory `Pending -> Completed` transition requires `TaskLifecycle.Pending` and ensures it returns `true`; its helper assigns the generated `TaskLifecycle_Completed` singleton.
- The Python app constructs generated `SimpleTask("Write Documentation", 2)`, passes it through both Protocol consumers, reads its priority, completes it, and prints the resulting values. Its output demonstrates construction, generic Protocol dispatch, priority, and the resource-backed completion transition—not a handwritten Python implementation.
