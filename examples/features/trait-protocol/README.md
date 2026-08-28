# trait-protocol

## Purpose
This end-to-end Cott v0.6 example shows a Cott-owned ordinary `SimpleTask` class whose agent-implemented methods satisfy an inherited `TaskView` trait.

## Protocols and the concrete implementation
- `Summarizable` has the associated `Summary` type and requires `summary() -> Summarizable.Summary`; `SimpleTask` assigns `Summary = Str`. `Prioritizable` requires `priority_level() -> I32`, and `Completable` requires `complete()`. `TaskView` inherits `Summarizable + Prioritizable`; `inspect_task[T: TaskView]` therefore requires that named read view, while `format_summary[T: Summarizable]` accepts only the summary protocol.
- `SimpleTask` implements `TaskView + Completable`. `TaskLifecycle` is a resource with initial `Pending`, terminal `Completed`, and its declared `Pending -> Completed` edge. Its implementation declares `title: Str`, `urgency: I32`, and `lifecycle: TaskLifecycle`, rather than asking the Python application to handwrite a class.
- The compiler owns the generated class shell, resource-state initialization, lock, and contract wrappers. The agent owns only the generated method helper implementations, so application code imports `SimpleTask` from the generated module.

## Contracts and observable behavior
- The class invariant requires a nonempty title and nonnegative urgency. `init(title, urgency)` repeats those preconditions and ensures the initialized title and urgency match its arguments; the omitted `lifecycle` parameter receives the resource initial state, `TaskLifecycle.Pending`.
- `summary` and `priority_level` are pure, contracted read methods. `complete`'s mandatory `Pending -> Completed` transition requires `TaskLifecycle.Pending` and ensures it returns `true`; its helper assigns the generated `TaskLifecycle_Completed` singleton.
- The Python app constructs generated `SimpleTask("Write Documentation", 2)`, passes it through the generic consumers, then wraps it nominally as `Dyn(value=task, trait=TaskView)`. `inspect_dyn(Dyn[TaskView]) -> Str` accepts that exact declared trait view and prints `Dyn: Write Documentation (urgency: 2)` alongside the summary, priority, and resource-backed completion output.
