# workflow-scenario

## Purpose

This dependency-free feature project exercises a finite async workflow scenario over immutable search and save snapshots. Scheduling lives only in the scenario (`spawn`, `tick`, `cancel`, `await`); there are no framework objects, widget trees, private implementation imports, host clocks, sleeps, or effects. All six implementations are agent-generated, and the manifest has no bindings.

After normal emission, run the public behavior with:

```sh
PYTHONPATH=generated/python .venv/bin/python python/app.py
```

The app resolves an old result, starts a newer search, applies the newer result, then presents the old result to the same public `apply_search` facade; the snapshot keeps the newer result. It also coalesces a draft save into a newer one and prints `new result` and `published`.

## Contracts

- `SearchSnapshot` invariants: a positive request ID; `Loading` means nothing is applied (`applied_request_id == 0` and an empty result); `Ready` means the snapshot's own request was applied (`applied_request_id == request_id`). `SearchResult`, `SaveSnapshot`, and `SaveReceipt` require a positive request ID or revision.
- `begin_search` returns a `Loading` snapshot for the given request ID and query.
- `resolve_search` is the only async facade. Its result keeps the request ID and query, and its text is the query followed by ` result`. Contracts have no string concatenation, so the clauses state this with `starts_with`, `ends_with`, and `result.len == query.len + 7`.
- `apply_search` always preserves the request ID and query. A candidate for the snapshot's request makes it `Ready` with the candidate's result; any other candidate returns the snapshot unchanged, so an older result cannot overwrite a newer request.
- `begin_save` queues the first request. `request_save` replaces the pending request only for a strictly newer revision; an equal or older revision returns the snapshot unchanged. `flush_save` returns a `Flushed` receipt with the snapshot's revision and text.
- Requirement `PENDING_SEARCH_IS_CANCELLABLE` states what the clauses cannot: a spawned resolution stays pending until the scheduler's next turn, so cancelling it before that turn ends it cancelled.

## Evidence

`latest_result_and_coalesced_save` awaits an old worker, starts a newer search, cancels and joins a separate pending worker, applies the new result and then the old one. It asserts that the final snapshot equals request 2, query `new`, result `new result`, `Ready`, and that flushing after a newer request and a stale one yields revision 2, `published`, `Flushed`.

With `runtime_validation = "boundary"`, every scenario call also checks the facade's clauses, and bounded automatic candidates exercise the pure facades. The last Python `cott verify` recorded the scenario as a test observation, semantic coverage `observed=23` with no `unobserved`, `trust_declaration`, or `unknown` clause, and `PENDING_SEARCH_IS_CANCELLABLE` as `observed` through the scenario. These are bounded observations, not proofs.

The Kotlin mirror in `examples/kotlin/features/workflow-scenario` carries the same contract, and its last `cott verify` recorded the same results: the scenario as a test observation, `observed=23`, and the requirement `observed`. The Kotlin runner starts a spawned worker undispatched, so its `resolve_search` implementation must suspend before completing to satisfy the cancellation requirement.
