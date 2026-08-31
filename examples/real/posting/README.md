# https://github.com/darrenburns/posting

Clean-room Cott reimplementation of a terminal HTTP client. The bodyless contract owns parsing,
request transport, typed errors, and response rendering; Python only adapts console I/O and the
standard-library HTTP boundary.

## Run

```bash
project=examples/real/posting
PYTHONPATH="$project/generated/python:$project/python" \
  "$project/.venv/bin/python" "$project/python/posting_cli.py" GET https://example.com
```

Usage is `METHOD URL [BODY]`. Responses print status, final URL, headers, and decoded text.
