# https://github.com/Textualize/toolong

This is a clean-room Cott reimplementation of a bounded log viewer. It is not derived from upstream source or prose.

Upstream SPDX license: [MIT](https://github.com/Textualize/toolong/blob/main/LICENSE).

## Supported scope

- Open UTF-8 plain-text and `.bz2` logs, retaining at most the requested number of records.
- Recognize JSONL records, render valid JSON with stable two-space indentation, and preserve non-JSON text.
- Detect ISO-8601 and common-log timestamps; classify common/combined access logs, error-like lines, JSON, and plain lines.
- Search retained text case-insensitively, merge pages by timestamp without disturbing ties, and append-read plain files from byte offsets.
- Run a Textual 6.6.0 viewer with one tab per file, a merged tab, live tailing, and in-app search.

Compressed files are initial-load only; append reads reject `.bz2` sources. The viewer never asks the facade for more than `--lines` records per read.

## Run

From the repository root, generate the Cott facade and install the project-local runtime:

```sh
project=examples/real/toolong
UV_PROJECT_ENVIRONMENT="$(pwd)/$project/.venv" uv sync --project "$project/python"
cott generate --agent omp --target python --project "$project"
```

Create a sample log, then print its retained entries:

```sh
printf '%s\n' '2026-08-29T12:00:00Z sample request' > "$project/sample.log"
PYTHONPATH="$project/generated/python:$project/python" "$project/.venv/bin/python" "$project/python/toolong.py" --print --lines 200 "$project/sample.log"
```

Launch the TUI for a log at a path you supply:

```sh
PYTHONPATH="$project/generated/python:$project/python" "$project/.venv/bin/python" "$project/python/toolong.py" --lines 200 /path/to/access.log
```

Launch the merged TUI for two log paths you supply:

```sh
PYTHONPATH="$project/generated/python:$project/python" "$project/.venv/bin/python" "$project/python/toolong.py" --merge --lines 200 /path/to/access.log /path/to/app.log
```
