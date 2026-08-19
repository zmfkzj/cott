# trait-protocol

## Purpose
This end-to-end example keeps the Cott v0.1 Protocol/generic-function lesson while showing a Cott-owned ordinary `SimpleTask` class whose method bodies are implemented by an agent.

## Protocols and the concrete implementation
- `Summarizable` requires `summary() -> Str`, `Prioritizable` requires `priority_level() -> I32`, and `Completable` requires `complete()`. `format_summary[T: Summarizable]` accepts only the summary protocol; `inspect_task[T: Summarizable + Prioritizable]` requires both read protocols.
- `impl SimpleTask for Summarizable + Prioritizable + Completable` is the concrete-class contract. It declares `title: Str`, `urgency: I32`, and `completed: Bool = false`, rather than asking the Python application to handwrite a class.
- The compiler owns the generated class shell, state, lock, and contract wrappers. The agent owns only the generated method helper implementations, so application code imports `SimpleTask` from the generated module.

## Contracts and observable behavior
- The class invariant requires a nonempty title and nonnegative urgency. `init(title, urgency)` repeats those preconditions and ensures the initialized state matches its arguments with `completed == false`.
- `summary` and `priority_level` are pure, contracted read methods. `complete` is also pure in the Cott effect sense, declares that it modifies only `completed`, and uses `old(self.completed)` with result and receiver postconditions to describe completion.
- The Python app constructs generated `SimpleTask("Write Documentation", 2)`, passes it through both Protocol consumers, reads its priority, completes it, and prints the resulting values. Its output demonstrates construction, generic Protocol dispatch, priority, and the completion transition—not a handwritten Python implementation.
