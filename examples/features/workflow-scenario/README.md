# workflow-scenario

## Purpose

This dependency-free Cott v0.8 feature project models immutable public search and save snapshots through manifest-bound Python facades. It intentionally keeps scheduling inside the finite scenario: there are no framework objects, widget trees, private implementation imports, host clocks, sleeps, or effects.

After normal emission, run the public behavior with:

```sh
PYTHONPATH=generated/python .venv/bin/python python/app.py
```

The app resolves an old result, starts a newer search, applies the newer result, then presents the old result to the same public `apply_search` facade. The returned snapshot remains the newer result. It also replaces a queued draft with a newer save request and prints the flushed public receipt.

## Domain and scenario

- `SearchSnapshot` and `SearchResult` carry typed request IDs, query text, and public result state. Their struct invariants require positive request IDs and keep an applied ID at or below its snapshot request ID; compiler-owned canonical constructors enforce those invariants.
- `SearchStatus` and `SaveStatus` make loading, ready, queued, and flushed state explicit without mutable controllers.
- `latest_result_and_coalesced_save` starts and awaits an old worker, starts a new worker, cancels and joins a separate pending worker, applies the new result, then proves through public fields that applying the old result cannot overwrite it. Its save sequence observes coalescing only through `request_save` and `flush_save` values.
- `resolve_search` is the sole async facade. All other facades are pure synchronous transformations, and every manifest entry names one exact typed top-level binding. The manifest has no authored identities.

No generated artifacts or verification records are authored in this project.
