from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from textual import on
from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Input, Static, TabbedContent, TabPane

from cott_runtime import CottList
from real.toolong import LogEntry, LogPage, LogSource, load_log, merge_pages, read_appended, render_jsonl, search_entries


def unwrap(result: Any) -> Any:
    try:
        return result.value
    except AttributeError as error:
        raise RuntimeError(str(result.error)) from error


def positive(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be positive")
    return number


def source_pages(sources: Sequence[LogSource], limit: int) -> CottList[LogPage]:
    return CottList(values=tuple(unwrap(load_log(source, limit)) for source in sources))


def filtered(entries: Sequence[LogEntry], needle: str, limit: int) -> CottList[LogEntry]:
    values = CottList(values=tuple(entries))
    return unwrap(search_entries(values, needle, limit)) if needle else values


class ToolongApp(App[None]):
    CSS = """
    Input { margin: 1; }
    Static { padding: 0 1; }
    """
    BINDINGS = [("m", "show_merged", "Merged")]

    def __init__(self, sources: Sequence[LogSource], limit: int, merged: bool) -> None:
        super().__init__()
        self.sources = list(sources)
        self.limit = limit
        self.start_merged = merged
        self.entries: list[list[LogEntry]] = []
        self.offsets: list[int] = []

    def compose(self) -> ComposeResult:
        yield Header()
        yield Input(placeholder="Search retained log text", id="search")
        initial = "merged" if self.start_merged else "file-0"
        with TabbedContent(initial=initial):
            for index, source in enumerate(self.sources):
                with TabPane(source.path.name, id=f"file-{index}"):
                    yield Static(id=f"view-{index}")
            with TabPane("Merged", id="merged"):
                yield Static(id="view-merged")
        yield Footer()

    def on_mount(self) -> None:
        try:
            pages = source_pages(self.sources, self.limit)
        except RuntimeError as error:
            self.notify(str(error), severity="error")
            self.exit()
            return
        self.entries = [list(page.entries) for page in pages]
        self.offsets = [page.next_byte for page in pages]
        self.refresh_views()
        self.set_interval(1, self.tail)

    @on(Input.Changed, "#search")
    def on_search_changed(self, _: Input.Changed) -> None:
        self.refresh_views()

    def action_show_merged(self) -> None:
        self.query_one(TabbedContent).active = "merged"

    def pages(self) -> CottList[LogPage]:
        return CottList(
            values=tuple(
                LogPage(source=source, entries=CottList(values=tuple(entries)), next_byte=offset, complete=True)
                for source, entries, offset in zip(self.sources, self.entries, self.offsets, strict=True)
            )
        )

    def text(self, entries: Sequence[LogEntry]) -> str:
        needle = self.query_one(Input).value
        matching = filtered(entries, needle, self.limit)
        return "\n".join(unwrap(render_jsonl(matching, 2)))

    def refresh_views(self) -> None:
        for index, entries in enumerate(self.entries):
            self.query_one(f"#view-{index}", Static).update(self.text(entries))
        merged = unwrap(merge_pages(self.pages(), self.limit))
        self.query_one("#view-merged", Static).update(self.text(merged))

    def tail(self) -> None:
        changed = False
        for index, source in enumerate(self.sources):
            if source.path.suffix.lower() == ".bz2":
                continue
            try:
                page = unwrap(read_appended(source, self.offsets[index], self.limit))
            except RuntimeError as error:
                self.notify(str(error), severity="error")
                continue
            self.offsets[index] = page.next_byte
            if page.entries:
                self.entries[index] = (self.entries[index] + list(page.entries))[-self.limit :]
                changed = True
        if changed:
            self.refresh_views()


def print_logs(sources: Sequence[LogSource], limit: int, merged: bool, needle: str) -> None:
    pages = source_pages(sources, limit)
    entries: CottList[LogEntry]
    if merged:
        entries = unwrap(merge_pages(pages, limit))
    else:
        entries = CottList(values=tuple(entry for page in pages for entry in page.entries))
    for line in unwrap(render_jsonl(filtered(entries, needle, limit), 2)):
        print(line)


def main() -> None:
    parser = argparse.ArgumentParser(description="bounded clean-room Toolong log viewer")
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--lines", type=positive, default=200)
    parser.add_argument("--merge", action="store_true")
    parser.add_argument("--search", default="")
    parser.add_argument("--print", dest="print_mode", action="store_true")
    args = parser.parse_args()
    sources = [LogSource(path=path) for path in args.paths]
    if args.print_mode:
        print_logs(sources, args.lines, args.merge, args.search)
    else:
        ToolongApp(sources, args.lines, args.merge).run()


if __name__ == "__main__":
    main()
