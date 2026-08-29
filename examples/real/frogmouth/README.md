# https://github.com/Textualize/frogmouth

This is a clean-room Cott reimplementation of a bounded Markdown browser. It is independently authored from the Cott contracts and does not reuse upstream source.

Upstream Frogmouth is Copyright (c) 2023 Textualize, Inc. and licensed under SPDX `MIT`:
https://github.com/Textualize/frogmouth/blob/15c3e85a6e84b2e4a6845723acf12beb54c81eb2/LICENSE

## Supported behavior

This bounded browser loads UTF-8 Markdown from local files, HTTP(S) URLs, GitHub (`gh owner/repo`), and Codeberg (`cb owner/repo`) repositories. It supports location fragments, relative navigation from the current document, front-matter removal, title discovery, help/history/bookmark sidebars, sidebar docking, and durable JSON history/bookmarks. Reads are limited to 5 MiB; network reads use a 15-second limit. It reports invalid locations, file, network, HTTP, encoding, and state errors in the UI.

It deliberately does not claim support for arbitrary schemes, non-Markdown rendering, browser scripting, authentication, or upstream feature parity beyond these contracts.

## Run

From the repository root, generate the Cott facade, install the project-local runtime, and launch the module with the project's README:

```sh
project=examples/real/frogmouth
UV_PROJECT_ENVIRONMENT="$(pwd)/$project/.venv" uv sync --project "$project/python"
cott generate --agent omp --target python --project "$project"
PYTHONPATH="$project/generated/python:$project/python" "$project/.venv/bin/python" -m frogmouth_ui.run_browser "$project/README.md"
```
