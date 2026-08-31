# https://github.com/Textualize/toolong

Clean-room Cott reimplementation of a terminal log reader. The bodyless contract owns parsing,
file loading, filtering, typed errors, and rendering; Python only adapts console I/O.

## Run

```bash
project=examples/real/toolong
PYTHONPATH="$project/generated/python:$project/python" \
  "$project/.venv/bin/python" "$project/python/toolong.py" --contains error /path/to/app.log
```

Without `--contains TEXT`, every line is rendered as `path:line text`.
