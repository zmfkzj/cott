# https://github.com/yt-dlp/yt-dlp

A clean-room Cott reimplementation of a media retrieval CLI. Its public contracts model CLI
input, discovery, selection, transfers, rendering, post-processing, and updates.

## Run

```sh
project=examples/real/yt-dlp
UV_PROJECT_ENVIRONMENT="$(pwd)/$project/.venv" uv sync --project "$project/python"
cott generate --agent omp --target python --project "$project"
PYTHONPATH="$project/generated/python:$project/python" "$project/.venv/bin/python" "$project/python/app.py" --simulate URL
```
