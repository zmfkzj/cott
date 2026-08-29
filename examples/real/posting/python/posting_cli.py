from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from real.posting.client import (
    discover_collections,
    export_curl,
    export_yaml,
    load_request,
    make_request,
    normalize_json_content,
    parse_method,
    resolve_request,
    save_request,
    send_request,
)


def _unwrap(result: Any) -> Any | None:
    if hasattr(result, "value"):
        return result.value
    print(f"posting: {result.error}", file=sys.stderr)
    return None


def _variables(values: list[str]) -> str:
    return "\n".join(values)


def _load(path: str) -> Any | None:
    return _unwrap(load_request(Path(path)))


def _normalized(request: Any) -> Any | None:
    return _unwrap(normalize_json_content(request))


def _command_list(args: argparse.Namespace) -> int:
    entries = _unwrap(discover_collections(Path(args.root)))
    if entries is None:
        return 1
    for entry in entries:
        print(f"{entry.path}\t{entry.name}")
    return 0


def _command_show(args: argparse.Namespace) -> int:
    request = _load(args.path)
    if request is None:
        return 1
    print(export_yaml(request), end="")
    return 0


def _command_save(args: argparse.Namespace) -> int:
    method = _unwrap(parse_method(args.method))
    if method is None:
        return 1
    body = args.json if args.json is not None else args.body
    request = _unwrap(
        make_request(args.name, method, args.url, "\n".join(args.header), body, args.json is not None)
    )
    if request is None:
        return 1
    return 0 if _unwrap(save_request(Path(args.path), request)) is not None else 1


def _command_export(args: argparse.Namespace) -> int:
    request = _load(args.path)
    if request is None:
        return 1
    if args.format == "yaml":
        print(export_yaml(request), end="")
        return 0
    request = _normalized(request)
    if request is None:
        return 1
    exported = _unwrap(export_curl(request, _variables(args.var)))
    if exported is None:
        return 1
    print(exported)
    return 0


def _command_send(args: argparse.Namespace) -> int:
    if args.timeout_ms == 0:
        print("posting: --timeout-ms must be positive", file=sys.stderr)
        return 2
    request = _load(args.path)
    if request is None:
        return 1
    request = _normalized(request)
    if request is None:
        return 1
    request = _unwrap(resolve_request(request, _variables(args.var)))
    if request is None:
        return 1
    response = _unwrap(send_request(request, args.timeout_ms))
    if response is None:
        return 1
    print(f"HTTP {response.status}")
    for header in response.headers:
        print(f"{header.name}: {header.value}")
    print()
    sys.stdout.buffer.write(response.body)
    if response.body and not response.body.endswith(b"\n"):
        print()
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="posting")
    commands = parser.add_subparsers(dest="command", required=True)

    list_command = commands.add_parser("list")
    list_command.add_argument("root", nargs="?", default=".")
    list_command.set_defaults(handler=_command_list)

    show_command = commands.add_parser("show")
    show_command.add_argument("path")
    show_command.set_defaults(handler=_command_show)

    save_command = commands.add_parser("save")
    save_command.add_argument("path")
    save_command.add_argument("--name", required=True)
    save_command.add_argument("--method", required=True)
    save_command.add_argument("--url", required=True)
    save_command.add_argument("--header", action="append", default=[])
    body = save_command.add_mutually_exclusive_group()
    body.add_argument("--body", default="")
    body.add_argument("--json")
    save_command.set_defaults(handler=_command_save)

    export_command = commands.add_parser("export")
    export_command.add_argument("format", choices=("curl", "yaml"))
    export_command.add_argument("path")
    export_command.add_argument("--var", action="append", default=[])
    export_command.set_defaults(handler=_command_export)

    send_command = commands.add_parser("send")
    send_command.add_argument("path")
    send_command.add_argument("--var", action="append", default=[])
    send_command.add_argument("--timeout-ms", type=int, default=10_000)
    send_command.set_defaults(handler=_command_send)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
