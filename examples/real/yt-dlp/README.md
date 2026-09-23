# https://github.com/yt-dlp/yt-dlp

A clean-room Cott reimplementation of a media retrieval CLI. Its public contracts model CLI
input, discovery, selection, transfers, rendering, post-processing, and updates.

## Run

```sh
project=examples/real/yt-dlp
UV_PROJECT_ENVIRONMENT="$(pwd)/$project/.venv" uv sync --locked --project "$project/python"
cott generate --agent omp --model anthropic/claude-opus-5-5 --target python --project "$project"
cott verify --project "$project"
PYTHONPATH="$project/generated/python:$project/python" "$project/.venv/bin/python" "$project/python/app.py" --simulate URL
```

Archives contain this client's plain media ids, one UTF-8 line per entry; they
are not upstream yt-dlp's extractor-key/id archive format. Plugin input is a
declarative text manifest (`extractor:NAME` or `postprocessor:NAME`), never
dynamically imported Python code.

The explicit updater API installs the official upstream `yt-dlp` release asset
at the caller's target, not a release of this Cott reimplementation. It verifies
the official HTTPS SHA-256 manifest before descriptor-relative atomic replacement.
`Check` does not replace the file; `Never` performs no update work.
