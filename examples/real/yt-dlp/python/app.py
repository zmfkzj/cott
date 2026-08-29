from __future__ import annotations

import argparse
from pathlib import Path
from typing import TypeVar
from urllib.parse import unquote, urlsplit

from cott_runtime import CottList, Err, Ok, Result
from real.yt_dlp_types import JsonMode_Lines, JsonMode_Single, MediaItem, TransferRequest
from real.yt_dlp import (
    parse_batch_urls,
    plan_downloads,
    render_items,
    render_output_path,
    transfer_media,
)



_T = TypeVar("_T")
_E = TypeVar("_E")


def result_value(result: Result[_T, _E]) -> _T:
    if isinstance(result, Ok):
        return result.value
    if isinstance(result, Err):
        raise SystemExit(str(result.error))
    raise SystemExit("generated facade returned an invalid result")


def item_from_url(url: str, playlist_index: int) -> MediaItem:
    leaf = unquote(urlsplit(url).path.rsplit("/", 1)[-1])
    stem, dot, ext = leaf.rpartition(".")
    if not dot:
        stem, ext = leaf or f"item-{playlist_index}", "bin"
    return MediaItem(
        url=url,
        id=str(playlist_index),
        title=stem or f"item-{playlist_index}",
        ext=ext or "bin",
        playlist_index=playlist_index,
    )


def read_lines(path: Path) -> list[str]:
    try:
        return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    except OSError as error:
        raise SystemExit(f"cannot read {path}: {error}") from error


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bounded direct HTTP(S) media transfer")
    parser.add_argument("urls", metavar="URL", nargs="*")
    parser.add_argument("--batch-file", type=Path)
    parser.add_argument("--simulate", action="store_true")
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--break-on-existing", action="store_true")
    parser.add_argument("--output", default="%(title)s.%(ext)s")
    parser.add_argument("--missing", default="NA")
    parser.add_argument("--max-bytes", type=int, default=268_435_456)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--json", action="store_true")
    modes.add_argument("--json-lines", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = arguments()
    urls = [url.strip() for url in args.urls if url.strip()]
    if args.batch_file is not None:
        batch = "\n".join(read_lines(args.batch_file))
        urls.extend(result_value(parse_batch_urls(batch, CottList(values=("#", ";")))))
    if not urls:
        raise SystemExit("provide at least one URL or --batch-file")
    if args.max_bytes < 1:
        raise SystemExit("--max-bytes must be positive")

    items = CottList(values=(item_from_url(url, index) for index, url in enumerate(urls, start=1)))
    archive: CottList[str] = CottList(values=read_lines(args.archive)) if args.archive is not None else CottList(values=())
    plan = plan_downloads(items, archive, args.break_on_existing)
    if args.json or args.json_lines:
        mode = JsonMode_Lines() if args.json_lines else JsonMode_Single()
        print(render_items(plan.items, mode), end="")
        return

    for item in plan.items:
        output = result_value(render_output_path(item, args.output, args.missing))
        receipt = result_value(
            transfer_media(
                TransferRequest(
                    url=item.url,
                    destination=Path(output),
                    simulate=args.simulate,
                    max_bytes=args.max_bytes,
                )
            )
        )
        action = "simulated" if receipt.simulated else "downloaded"
        print(f"{action} {receipt.url} -> {receipt.destination} ({receipt.bytes_written} bytes)")


if __name__ == "__main__":
    main()
