# https://github.com/Textualize/frogmouth

Clean-room Cott reimplementation of a terminal Markdown browser. Cott owns address resolution,
document loading, title derivation and the `open_location` root; Python supplies the Textual UI
(`python/frogmouth_ui/`). Frogmouth's history, bookmarks, table of contents, local file browser,
`~` expansion and GitHub/GitLab shortcuts are not reimplemented.

## Run

```bash
project=examples/real/frogmouth
PYTHONPATH="$project/generated/python:$project/python" \
  "$project/.venv/bin/python" -m frogmouth_ui.run_browser README.md
```

The address bar accepts a local Markdown path or an `http://`/`https://` URL. `Ctrl+L` focuses
it, `Ctrl+R` reloads, and `q` exits. Documents are limited to 5 MiB of strict UTF-8.

## Contract

- `frogmouth.model`: a `Location` has a non-empty target and an HTTP location's target starts
  with `http://` or `https://`; a `Document` has a non-empty title (type invariants).
- `frogmouth.navigation.resolve_location`: exact classification with `errors complete`
  (`EmptyInput`, `UnsupportedScheme` for other `://` schemes); local paths are joined to the
  working directory without normalization. `display_location` returns the target.
- `frogmouth.document.derive_title`: a pure stage (first ATX heading line, otherwise the last
  path segment of the target).
- `frogmouth.document.load_document`: local and HTTP loading, the 5 MiB limit, strict UTF-8 and
  the error mapping; every error carries the location's target.
- `frogmouth.document.open_location`: the root used by the address bar and reload,
  `resolve_location` → `load_document`, with errors wrapped in `OpenError`. Requirements state
  this composition and that the title comes from `derive_title`.

## Evidence

`cott verify` certifies the current snapshot with `observed=23 trust_declaration=4 unknown=0
unobserved=0` clause observations. One scenario checks titles on pure inputs. The other calls
`open_location` against the compiler-owned filesystem and loopback HTTP fixtures: an exact local
`Document`, a remote title and body, missing local and HTTP (404) documents, invalid UTF-8, a 500
status as `NetworkFailed`, an unsupported scheme and empty input. The local cases observe the
implementation's fixture-adapter branch; the production branch that reads host files is not
observed by Cott evidence. HTTP runs through the same standard-library client as in production.

The four `trust_declaration` clauses are `load_document`'s `TooLarge` and `ReadFailed` errors and
their source guards: the fixtures cannot hold 5 MiB and inject no read failure. The Textual
adapter and redirect handling are not observed either.

`cott requirements` reports both requirements (`LOAD_TITLE_IS_DERIVED`,
`OPEN_RESOLVES_THEN_LOADS`) as `observed` for the current snapshot: bounded scenario evidence,
not proof.
