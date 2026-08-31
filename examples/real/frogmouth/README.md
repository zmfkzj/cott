# https://github.com/Textualize/frogmouth

Clean-room Cott reimplementation of a terminal Markdown browser. Cott owns location resolution,
typed load results, and document data. Python supplies Textual and file/network boundaries.

## Run

```bash
project=examples/real/frogmouth
PYTHONPATH="$project/generated/python:$project/python" \
  "$project/.venv/bin/python" -m frogmouth_ui.run_browser README.md
```

The address bar accepts a local Markdown path or an HTTP(S) URL. `Ctrl+L` focuses it,
`Ctrl+R` reloads, and `q` exits. Documents are limited to 5 MiB.
