# https://github.com/darrenburns/posting

This is a clean-room Cott reimplementation; it shares no upstream source or prose.

Upstream is Apache-2.0: [LICENSE](https://github.com/darrenburns/posting/blob/main/LICENSE) and [NOTICE](https://github.com/darrenburns/posting/blob/main/NOTICE).

## Bounded behavior

This project is a local terminal HTTP collection client. A collection is one `*.posting.yaml`
file found recursively below a supplied directory; `list` reports matching paths in lexical order.
Each document is one YAML mapping with exactly `name`, `method`, `url`, `headers`, `body`, and
`json`: `name`, `url`, and `body` are strings; `method` is GET, POST, PUT, PATCH, DELETE, HEAD,
or OPTIONS; `headers` is a string-to-string mapping; and `json` is a boolean. Loading and saving
use locked `PyYAML>=6,<7` safe load/dump APIs and saving writes this canonical mapping.

URL variables use `:name`; `::` emits one literal colon. Variables passed as `--var NAME=value`
are newline-delimited values, while host environment values of the same name take precedence.
Unresolved variables are typed errors. When `json` is true, the body is parsed then compactly
serialized as JSON and `Content-Type: application/json` is inserted only when no header already
matches that name case-insensitively. cURL export uses shell-safe argument quoting; YAML export is
canonical. Sending uses `urllib.request` with a positive millisecond timeout, returns HTTP error
responses normally, and returns typed timeout or network errors for transport failures.

## Run

Generate the public Cott facades and implementations, then run the adapter with both source roots:

```bash
project=examples/real/posting
UV_PROJECT_ENVIRONMENT="$(pwd)/$project/.venv" uv sync --project "$project/python"
cott generate --agent omp --target python --project "$project"
PYTHONPATH="$project/generated/python:$project/python" "$project/.venv/bin/python" "$project/python/posting_cli.py" list .
```

Create, inspect, export, and send a request document:

```bash
PYTHONPATH="$project/generated/python:$project/python" "$project/.venv/bin/python" "$project/python/posting_cli.py" save demo.posting.yaml --name health --method GET --url https://example.com/:path
PYTHONPATH="$project/generated/python:$project/python" "$project/.venv/bin/python" "$project/python/posting_cli.py" show demo.posting.yaml
PYTHONPATH="$project/generated/python:$project/python" "$project/.venv/bin/python" "$project/python/posting_cli.py" export curl demo.posting.yaml --var path=health
PYTHONPATH="$project/generated/python:$project/python" "$project/.venv/bin/python" "$project/python/posting_cli.py" send demo.posting.yaml --var path=health --timeout-ms 10000
```
