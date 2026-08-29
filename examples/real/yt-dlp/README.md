# https://github.com/yt-dlp/yt-dlp

This is a clean-room Cott reimplementation of deliberately bounded yt-dlp behavior.

Upstream is licensed under SPDX [Unlicense](https://github.com/yt-dlp/yt-dlp/blob/master/LICENSE).

## Supported behavior

- Parses direct URLs and batch text, ignoring blank lines and configured comment prefixes.
- Expands one-based inclusive playlist ranges over supplied items.
- Plans in input order, omitting exact archived URLs and optionally stopping at the first one.
- Renders `%(id)s`, `%(title)s`, `%(ext)s`, and `%(playlist_index)s` output fields.
- Emits compact JSON Lines or one compact JSON array.
- Simulates without network or filesystem writes, or transfers one direct HTTP(S) resource.
- Bounds transfers with `--max-bytes` and reports typed failures through generated facades.

It has no site extractors, media format selection, authentication, playlists from remote sites,
ffmpeg integration, plugins, retries, or parity with the upstream project.

## Run

From the repository root, create the project-local environment, generate the Cott Python facades, and run:

```sh
project=examples/real/yt-dlp
UV_PROJECT_ENVIRONMENT="$(pwd)/$project/.venv" uv sync --project "$project/python"
cott generate --agent omp --target python --project "$project"
printf '%s\n' 'https://example.com/media.bin' > "$project/urls.txt"
: > "$project/done.txt"
PYTHONPATH="$project/generated/python:$project/python" "$project/.venv/bin/python" "$project/python/app.py" --simulate https://example.com/media.bin
PYTHONPATH="$project/generated/python:$project/python" "$project/.venv/bin/python" "$project/python/app.py" --batch-file "$project/urls.txt" --archive "$project/done.txt"
PYTHONPATH="$project/generated/python:$project/python" "$project/.venv/bin/python" "$project/python/app.py" --json-lines https://example.com/media.bin
```
