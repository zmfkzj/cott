# trait-protocol

## Purpose
This Cott v0.7 lesson puts trait inheritance, selection, exact runtime views, and async state ownership in one `SimpleTask` implementation.

## Trait selection and exact types
- `Summarizable` preserves the associated `Summary` type through `summary() -> Summarizable.Summary`; covariant `TaskView[+T]` inherits it together with `Prioritizable` and uses `T` for `display`. `SimpleTask` selects `TaskView[Str]`, assigns `Summary = Str`, and therefore gives `Dyn[TaskView[Str]]` an exact generic trait identity rather than a structural substitute.
- Every effective slot is async because a single impl cannot mix sync and async trait slots. `summary` and `priority_level` are explicit agent helpers. `display` is selected by `specialize SimpleTask for TaskView[Str]` and dispatches through `specialized_display`; `category` has no helper and dispatches through the verified `default_category` facade. The three paths produce separately labelled application output.
- `task_factory() -> Factory[SimpleTask]` returns the exact generated `SimpleTask` class object without constructing it. The app prints that identity check before calling the factory.

## State and observable behavior
- The compiler owns `title`, `urgency`, `lifecycle`, `completion_count`, initialization, locks, and wrappers. Its invariants require a nonempty title, nonnegative urgency, and nonnegative completion count; `init(title, urgency)` preserves the two caller-supplied fields.
- `await task.complete()` is the one explicit async state transition. It changes `lifecycle` only through `Pending -> Completed`, increments the non-resource `completion_count` under `modifies`, and proves that increment with `old(self.completion_count)`. `modifies` deliberately does not name the resource field because its transition owns that update.
- The app awaits the explicit, specialized, default, Dyn, priority, and completion calls. A second `await task.complete()` has no declared `Completed -> Completed` edge and the generated boundary raises its transition violation; the example does not catch or hide that error.
