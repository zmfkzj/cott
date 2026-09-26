import collections
import os
import pathlib
import select
import time
from typing import Callable, Final, cast

from prompt_toolkit.application import Application
from prompt_toolkit.data_structures import Point
from prompt_toolkit.filters import Condition
from prompt_toolkit.formatted_text import StyleAndTextTuples
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.key_processor import KeyPressEvent
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.mouse_events import MouseEvent as PtMouseEvent
from prompt_toolkit.mouse_events import MouseEventType
from rich.cells import cell_len

from cott_runtime import CottList, Err, Nothing, Ok, Opaque, Option, Result, Some, U8, UNIT, Unit
from real.toolong.files import close_source, detect_compression, find_line, line_timestamp, locate_time, open_source, poll_source, read_lines, save_lines, scan_breaks, scan_timestamps
from real.toolong.files_types import SourceError_NotFound
from real.toolong.index import add_scanned_breaks, add_tail_breaks, complete_file_scan, line_location, merge_timestamps, start_file_index
from real.toolong.keys import decode_key
from real.toolong.keys_types import TerminalInput_KeyPress
from real.toolong.model_types import FileIndex, FileTimestamps, FindQuery, LineFormat, LineFormat_Json, LogSource, MergedIndex, MergedLine, ParsedLine, ScreenRow, StyledRun, StyledSpan, StyledText, TabIndex, TabIndex_Merged, TabIndex_Single, TimestampEntry, ViewerSetup
from real.toolong.screen import compose_screen
from real.toolong.screen_types import Frame, FrameContent
from real.toolong.text import abbreviate_text, completion_target, default_line_formats, parse_line, pretty_json, search_words, wrap_text
from real.toolong.timestamps import default_timestamp_order, format_local_timestamp
from real.toolong.tui import frame_fragments, open_link
from real.toolong.tui_types import ViewerFailure, ViewerFailure_Terminal
from real.toolong.view import apply_event, handle_key, handle_mouse, initial_viewer, viewer_layout
from real.toolong.view_types import MouseEvent, MouseKind, MouseKind_Click, MouseKind_WheelDown, MouseKind_WheelUp, Severity_Error, Severity_Information, TabView, ViewerEvent, ViewerEvent_Breaks, ViewerEvent_Complete, ViewerEvent_Found, ViewerEvent_Jumped, ViewerEvent_Loaded, ViewerEvent_Notify, ViewerEvent_OpenFailed, ViewerEvent_PanelSize, ViewerEvent_Progress, ViewerEvent_Resize, ViewerEvent_Suggestion, ViewerEvent_Tailed, ViewerEvent_Tick, ViewerEvent_Widths, ViewerRequest, ViewerRequest_Bell, ViewerRequest_CancelScan, ViewerRequest_FindNext, ViewerRequest_Navigate, ViewerRequest_OpenLink, ViewerRequest_Quit, ViewerState, ViewerUpdate

_SCAN_CHUNK: Final[int] = 8388608
_BATCH: Final[int] = 10000
_BUDGET: Final[float] = 0.05
_IO_CHUNKS: Final[int] = 16
_PIPE_CHUNK: Final[int] = 65536
_SUGGEST_LIMIT: Final[int] = 10000
_CACHE_LIMIT: Final[int] = 20000
_RUN_GROUP: Final[int] = 256


def _viewer(state: dict[str, object]) -> ViewerState:
    return cast(ViewerState, state["viewer"])


def _app(state: dict[str, object]) -> Application[None]:
    return cast(Application[None], state["app"])


def _tabs(state: dict[str, object]) -> list[dict[str, object]]:
    return cast(list[dict[str, object]], state["tabs"])


def _number(tab: dict[str, object], name: str) -> int:
    return cast(int, tab[name])


def _sources(tab: dict[str, object]) -> list[LogSource]:
    return cast(list[LogSource], tab["sources"])


def _opened(tab: dict[str, object]) -> list[bool]:
    return cast(list[bool], tab["opened"])


def _index(tab: dict[str, object]) -> TabIndex:
    return cast(TabIndex, tab["index"])


def _single(tab: dict[str, object]) -> FileIndex:
    return cast(TabIndex_Single, tab["index"]).index


def _orders(tab: dict[str, object]) -> CottList[CottList[U8]]:
    return cast(CottList[CottList[U8]], tab["timestamp_orders"])


def _entries(tab: dict[str, object]) -> list[TimestampEntry]:
    return cast(list[TimestampEntry], tab["entries"])


def _completed(tab: dict[str, object]) -> list[FileTimestamps]:
    return cast(list[FileTimestamps], tab["completed"])


def _break_count(index: FileIndex) -> int:
    return len(cast(tuple[int, ...], index.breaks.unwrap()))


def _merged_count(index: MergedIndex) -> int:
    return len(cast(tuple[MergedLine, ...], index.lines.unwrap()))


def _file_stamps(opened: bool, size: int, entries: list[TimestampEntry]) -> FileTimestamps:
    return FileTimestamps(opened=opened, size=size, entries=Opaque(tag="timestamp_entries", value=tuple(entries)))


def _view_tab(state: dict[str, object], index: int) -> TabView:
    for number, tab in enumerate(_viewer(state).tabs):
        if number == index:
            return tab
    raise IndexError(index)


def _apply(state: dict[str, object], update: ViewerUpdate) -> None:
    state["viewer"] = update.viewer
    for request in update.requests:
        _request(state, request)


def _event(state: dict[str, object], event: ViewerEvent) -> None:
    _apply(state, apply_event(_viewer(state), event))


def _request(state: dict[str, object], request: ViewerRequest) -> None:
    if isinstance(request, ViewerRequest_Bell):
        _app(state).output.bell()
    elif isinstance(request, ViewerRequest_Quit):
        _app(state).exit()
    elif isinstance(request, ViewerRequest_FindNext):
        if request.tab < len(_tabs(state)):
            tab = _tabs(state)[request.tab]
            view = _view_tab(state, request.tab)
            query = FindQuery(text=view.find_input.value, regex=view.regex, case_sensitive=view.case_sensitive)
            found = find_line(CottList(values=_sources(tab)), _index(tab), view.line_count, request.start, request.direction, query)
            _event(state, ViewerEvent_Found(tab=request.tab, line=found.line, invalid_regex=found.invalid_regex))
    elif isinstance(request, ViewerRequest_Navigate):
        if request.tab < len(_tabs(state)):
            tab = _tabs(state)[request.tab]
            jump = locate_time(CottList(values=_sources(tab)), _index(tab), _view_tab(state, request.tab).line_count, request.from_line, request.steps, request.unit, _orders(tab))
            tab["timestamp_orders"] = jump.orders
            _event(state, ViewerEvent_Jumped(tab=request.tab, line=jump.line))
    elif isinstance(request, ViewerRequest_CancelScan):
        _cancel_scan(state, request.tab)
    elif isinstance(request, ViewerRequest_OpenLink):
        open_link(request.url)
    else:
        suggestion = ""
        target = completion_target(request.value)
        if isinstance(target, Some):
            words = cast(collections.OrderedDict[str, str], state["suggestions"])
            key = target.value.word.lower()
            word = words.get(key)
            if word is not None:
                words.move_to_end(key)
                suggestion = target.value.start + word
        else:
            suggestion = ""
        _event(state, ViewerEvent_Suggestion(value=request.value, suggestion=suggestion))


def _cancel_scan(state: dict[str, object], index: int) -> None:
    if index >= len(_tabs(state)):
        return
    tab = _tabs(state)[index]
    if tab["phase"] != "scan":
        return
    sources = _sources(tab)
    if cast(bool, tab["merged"]):
        files = list(_completed(tab))
        for file_index in range(len(files), len(sources)):
            present = _opened(tab)[file_index]
            partial = list(_entries(tab)) if file_index == _number(tab, "file") and present else []
            files.append(_file_stamps(present, sources[file_index].size if present else 0, partial))
        merged = merge_timestamps(CottList(values=files), False)
        tab["index"] = TabIndex_Merged(index=merged)
        tab["phase"] = "idle"
        _event(state, ViewerEvent_Complete(tab=index, count=_merged_count(merged)))
    else:
        source = sources[0]
        index_file = complete_file_scan(_single(tab), source.size, _number(tab, "lowest"))
        tab["index"] = TabIndex_Single(index=index_file)
        tab["phase"] = "tail"
        tab["tail_position"] = source.size
        _event(state, ViewerEvent_Complete(tab=index, count=_break_count(index_file)))


def _scan_single(state: dict[str, object], index: int) -> None:
    tab = _tabs(state)[index]
    source = _sources(tab)[0]
    size = source.size
    end = _number(tab, "chunk")
    start = max(0, end - _SCAN_CHUNK)
    breaks = scan_breaks(source, start, end)
    found = cast(tuple[int, ...], breaks.unwrap())
    old = _single(tab)
    _event(state, ViewerEvent_Progress(tab=index, message=f"Scanning… ({_break_count(old) // 1000:,}K lines)- ESCAPE to cancel", progress=1 - start / size))
    lowest = min(_number(tab, "lowest"), min(found)) if found else _number(tab, "lowest")
    tab["lowest"] = lowest
    new = add_scanned_breaks(old, breaks, lowest)
    tab["index"] = TabIndex_Single(index=new)
    _event(state, ViewerEvent_Breaks(tab=index, count=_break_count(new)))
    tab["chunk"] = start
    if start == 0 and tab["phase"] == "scan":
        new = complete_file_scan(new, size, 0)
        tab["index"] = TabIndex_Single(index=new)
        tab["phase"] = "tail"
        tab["tail_position"] = size
        _event(state, ViewerEvent_Complete(tab=index, count=_break_count(new)))


def _scan_merged(state: dict[str, object], index: int) -> None:
    tab = _tabs(state)[index]
    file_index = _number(tab, "file")
    sources = _sources(tab)
    if file_index >= len(sources):
        merged = merge_timestamps(CottList(values=_completed(tab)), True)
        tab["index"] = TabIndex_Merged(index=merged)
        tab["phase"] = "idle"
        count = _merged_count(merged)
        _event(state, ViewerEvent_Complete(tab=index, count=count))
        _save_merge(state, index, count)
        return
    if not _opened(tab)[file_index]:
        _completed(tab).append(_file_stamps(False, 0, []))
        tab["file"] = file_index + 1
        return
    source = sources[file_index]
    orders = [order for order in _orders(tab)]
    batch = scan_timestamps(source, _number(tab, "position"), _number(tab, "line"), _BATCH, orders[file_index])
    orders[file_index] = batch.order
    tab["timestamp_orders"] = CottList(values=orders)
    entries = cast(tuple[TimestampEntry, ...], batch.entries.unwrap())
    _entries(tab).extend(entries)
    tab["line"] = _number(tab, "line") + len(entries)
    tab["position"] = batch.position
    total = _number(tab, "total")
    progress = (_number(tab, "earlier") + batch.position) / total if total else 1.0
    _event(state, ViewerEvent_Progress(tab=index, message=f"Merging {source.name} - ESCAPE to cancel", progress=progress))
    if tab["phase"] != "scan":
        return
    if len(entries) == 0 or batch.position >= source.size:
        _completed(tab).append(_file_stamps(True, source.size, _entries(tab)))
        tab["earlier"] = _number(tab, "earlier") + source.size
        tab["file"] = file_index + 1
        tab["position"] = 0
        tab["line"] = 0
        tab["entries"] = []


def _save_merge(state: dict[str, object], index: int, count: int) -> None:
    setup = cast(ViewerSetup, state["setup"])
    target = setup.save_merge
    if isinstance(target, Some):
        path = target.value
        tab = _tabs(state)[index]
        result = save_lines(CottList(values=_sources(tab)), _index(tab), count, path)
        if isinstance(result, Ok):
            _event(state, ViewerEvent_Notify(title="", message=f"Saved merged log files to {str(path)!r}", severity=Severity_Information()))
        else:
            _event(state, ViewerEvent_Notify(title="", message=f"Failed to save {str(path)!r}; {result.error.message}", severity=Severity_Error()))
    else:
        return


def _tail(state: dict[str, object], index: int) -> None:
    tab = _tabs(state)[index]
    source = _sources(tab)[0]
    for _ in range(_IO_CHUNKS):
        position = _number(tab, "tail_position")
        chunk = poll_source(source, position)
        if chunk.position == position:
            break
        old = _single(tab)
        new = add_tail_breaks(old, chunk.breaks, chunk.position)
        tab["index"] = TabIndex_Single(index=new)
        tab["tail_position"] = chunk.position
        _event(state, ViewerEvent_Tailed(tab=index, before=_break_count(old), after=_break_count(new)))


def _pipe(state: dict[str, object]) -> None:
    feed = cast(tuple[int, pathlib.Path] | None, state["pipe"])
    if feed is None:
        return
    descriptor, path = feed
    try:
        for _ in range(_IO_CHUNKS):
            ready, _writing, _errors = select.select([descriptor], [], [], 0)
            if not ready:
                break
            chunk = os.read(descriptor, _PIPE_CHUNK)
            if not chunk:
                os.close(descriptor)
                state["pipe"] = None
                break
            with open(path, "ab") as output:
                output.write(chunk)
    except OSError:
        state["pipe"] = None


def _work(state: dict[str, object]) -> None:
    deadline = time.monotonic() + _BUDGET
    tabs = _tabs(state)
    active = int(_viewer(state).active)
    order = ([active] if active < len(tabs) else []) + [number for number in range(len(tabs)) if number != active]
    for index in order:
        tab = tabs[index]
        while tab["phase"] == "scan" and time.monotonic() < deadline:
            if cast(bool, tab["merged"]):
                _scan_merged(state, index)
            else:
                _scan_single(state, index)
        if tab["phase"] == "tail" and time.monotonic() < deadline and _sources(tab)[0].can_tail:
            _tail(state, index)
    _pipe(state)


def _feed_suggestions(state: dict[str, object], plain: str) -> None:
    words = cast(collections.OrderedDict[str, str], state["suggestions"])
    for entry in search_words(plain):
        key = entry.prefix.lower()
        if key in words:
            words.move_to_end(key)
            if len(words[key]) < len(entry.word):
                words[key] = entry.word
        else:
            words[key] = entry.word
            if len(words) > _SUGGEST_LIMIT:
                words.popitem(last=False)


def _parsed(state: dict[str, object], tab_index: int, line: int, fresh: list[StyledText]) -> ParsedLine:
    tab = _tabs(state)[tab_index]
    location = line_location(_index(tab), line)
    file_index = int(location.file)
    key = (tab_index, file_index, int(location.span.start), int(location.span.end))
    cache = cast(dict[tuple[int, int, int, int], ParsedLine], state["cache"])
    cached = cache.get(key)
    if cached is not None:
        return cached
    sources = _sources(tab)
    formats = cast(list[CottList[LineFormat]], tab["format_orders"])
    text = ""
    if file_index < len(sources):
        for item in read_lines(sources[file_index], CottList(values=[location.span])):
            text = item
        order = formats[file_index]
    else:
        order = default_line_formats()
    parsed = parse_line(text, order)
    if file_index < len(sources):
        formats[file_index] = parsed.order
    if len(cache) >= _CACHE_LIMIT:
        cache.clear()
    cache[key] = parsed
    _feed_suggestions(state, parsed.text.text)
    fresh.append(parsed.text)
    return parsed


def _split_styled(text: StyledText) -> list[StyledText]:
    rows: list[StyledText] = []
    start = 0
    for piece in text.text.split("\n"):
        end = start + len(piece)
        spans: list[StyledSpan] = []
        for span in text.spans:
            low = max(start, span.start)
            high = min(end, span.end)
            if low < high:
                spans.append(StyledSpan(start=low - start, end=high - start, style=span.style))
        rows.append(StyledText(text=piece, spans=CottList(values=spans)))
        start = end + 1
    return rows


def _compose(state: dict[str, object]) -> None:
    viewer = _viewer(state)
    lines: list[StyledText] = []
    panel: list[StyledText] = []
    meta = ""
    if viewer.active < len(viewer.tabs):
        index = int(viewer.active)
        tab = _tabs(state)[index]
        view = _view_tab(state, index)
        fresh: list[StyledText] = []
        for row in range(viewer_layout(viewer).text.height):
            line = view.scroll_y + row
            if line >= view.line_count:
                break
            lines.append(abbreviate_text(_parsed(state, index, line, fresh).text, 1000))
        if fresh:
            widest = max(cell_len(abbreviate_text(text, 1000).text) for text in fresh)
            if widest > view.content_width:
                _event(state, ViewerEvent_Widths(tab=index, width=widest))
        view = _view_tab(state, index)
        pointer = view.pointer
        current = int(pointer.value) if isinstance(pointer, Some) else int(view.scroll_y)
        parts: list[str] = []
        if view.merged:
            location = line_location(_index(tab), current)
            for file_index, name in enumerate(view.file_names):
                if file_index == location.file:
                    parts.append(name)
                    break
        stamp = line_timestamp(CottList(values=_sources(tab)), _index(tab), current, _orders(tab))
        tab["timestamp_orders"] = stamp.orders
        if isinstance(stamp.timestamp, Some):
            parts.append(format_local_timestamp(stamp.timestamp.value))
        parts.append(str(current + 1))
        meta = " • ".join(parts)
        rect = viewer_layout(_viewer(state)).panel
        if view.show_panel and isinstance(pointer, Some) and isinstance(rect, Some):
            parsed = _parsed(state, index, current, [])
            pretty: Option[StyledText] = pretty_json(parsed.line) if isinstance(parsed.format, LineFormat_Json) else Nothing()
            if isinstance(pretty, Some):
                panel = _split_styled(pretty.value)
            else:
                panel = [row for row in wrap_text(abbreviate_text(parsed.text, 100000), max(0, rect.value.width - 6))]
            widest_row = max((cell_len(row.text) for row in panel), default=0)
            if view.panel_lines != len(panel) or view.panel_width != widest_row:
                _event(state, ViewerEvent_PanelSize(tab=index, lines=len(panel), width=widest_row))
    state["meta"] = meta
    content = FrameContent(lines=Opaque(tag="styled_lines", value=tuple(lines)), panel=Opaque(tag="styled_lines", value=tuple(panel)), meta=meta)
    state["frame"] = compose_screen(_viewer(state), content)


def _on_render(state: dict[str, object]) -> None:
    size = _app(state).output.get_size()
    viewer = _viewer(state)
    if size.columns != viewer.width or size.rows != viewer.height:
        _event(state, ViewerEvent_Resize(width=max(0, min(65535, size.columns)), height=max(0, min(65535, size.rows))))
    _work(state)
    _event(state, ViewerEvent_Tick(now_ms=int((time.monotonic() - cast(float, state["start"])) * 1000)))
    _compose(state)
    state["rendered"] = True


def _on_keys(state: dict[str, object], event: KeyPressEvent) -> None:
    for press in event.key_sequence:
        key = press.key
        name = key.value if isinstance(key, Keys) else key
        decoded = decode_key(TerminalInput_KeyPress(name=name, data=press.data))
        if isinstance(decoded, Some):
            _apply(state, handle_key(_viewer(state), decoded.value))
        else:
            continue


def _on_mouse(state: dict[str, object], event: PtMouseEvent) -> object:
    kind: MouseKind
    if event.event_type == MouseEventType.MOUSE_UP:
        kind = MouseKind_Click()
    elif event.event_type == MouseEventType.SCROLL_UP:
        kind = MouseKind_WheelUp()
    elif event.event_type == MouseEventType.SCROLL_DOWN:
        kind = MouseKind_WheelDown()
    else:
        return NotImplemented
    mouse = MouseEvent(x=max(0, min(65535, event.position.x)), y=max(0, min(65535, event.position.y)), kind=kind)
    _apply(state, handle_mouse(_viewer(state), mouse, cast(str, state["meta"])))
    return None


def _fragments(state: dict[str, object]) -> StyleAndTextTuples:
    frame = cast(Frame | None, state["frame"])
    if frame is None:
        return []
    mouse_handler: Callable[[PtMouseEvent], object] = lambda event: _on_mouse(state, event)
    fragments: list[tuple[str, str, Callable[[PtMouseEvent], object]]] = []
    rows = cast(tuple[ScreenRow, ...], frame.rows.unwrap())
    for number, row in enumerate(rows):
        if number > 0:
            fragments.append(("", "\n", mouse_handler))
        runs: list[StyledRun] = [run for run in row.runs]
        for begin in range(0, len(runs), _RUN_GROUP):
            group = ScreenRow(runs=CottList(values=runs[begin:begin + _RUN_GROUP]))
            for piece in frame_fragments(group):
                fragments.append((piece.style, piece.text, mouse_handler))
    return cast(StyleAndTextTuples, fragments)


def _cursor(state: dict[str, object]) -> Point | None:
    frame = cast(Frame | None, state["frame"])
    if frame is None:
        return None
    cursor = frame.cursor
    if isinstance(cursor, Some):
        return Point(x=cursor.value.x, y=cursor.value.y)
    else:
        return None


def _hidden(state: dict[str, object]) -> bool:
    return _cursor(state) is None


def _placeholder(path: pathlib.Path) -> LogSource:
    name = path.name
    return LogSource(path=path, name=name, compression=detect_compression(name), descriptor=Nothing(), size=0, can_tail=False)


def _open_tabs(state: dict[str, object], setup: ViewerSetup) -> list[ViewerEvent]:
    pending: list[ViewerEvent] = []
    registry = cast(list[LogSource], state["opened"])
    for index, plan in enumerate(setup.tabs):
        sources: list[LogSource] = []
        opened: list[bool] = []
        for path in plan.paths:
            result = open_source(path)
            if isinstance(result, Ok):
                sources.append(result.value)
                registry.append(result.value)
                opened.append(True)
            else:
                error = result.error
                sources.append(_placeholder(path))
                opened.append(False)
                if plan.merged:
                    pending.append(ViewerEvent_Notify(title="", message=f"Failed to open {error.name!r}; {error.message}", severity=Severity_Error()))
                elif isinstance(error, SourceError_NotFound):
                    pending.append(ViewerEvent_OpenFailed(tab=index, message=f"File {error.name!r} not found."))
                else:
                    pending.append(ViewerEvent_OpenFailed(tab=index, message=f"Failed to open {error.name!r}; {error.message}"))
        tab: dict[str, object] = {
            "merged": plan.merged,
            "sources": sources,
            "opened": opened,
            "format_orders": [default_line_formats() for _ in sources],
            "timestamp_orders": CottList(values=[default_timestamp_order() for _ in sources]),
        }
        if plan.merged:
            tab["index"] = TabIndex_Merged(index=MergedIndex(lines=Opaque(tag="merged_lines", value=()), breaks=Opaque(tag="merged_breaks", value=()), scanned_size=0))
            tab["phase"] = "scan"
            tab["file"] = 0
            tab["position"] = 0
            tab["line"] = 0
            tab["entries"] = []
            tab["completed"] = []
            tab["earlier"] = 0
            tab["total"] = sum(source.size for source, present in zip(sources, opened) if present)
            pending.append(ViewerEvent_Loaded(tab=index))
        elif opened and opened[0]:
            size = sources[0].size
            tab["index"] = TabIndex_Single(index=start_file_index(size))
            tab["tail_position"] = size
            if size == 0:
                tab["phase"] = "tail"
                pending.append(ViewerEvent_Complete(tab=index, count=0))
            else:
                tab["phase"] = "scan"
                tab["chunk"] = size
                tab["lowest"] = size
        else:
            tab["index"] = TabIndex_Single(index=start_file_index(0))
            tab["phase"] = "idle"
            if not sources:
                pending.append(ViewerEvent_Complete(tab=index, count=0))
        _tabs(state).append(tab)
    return pending


def _close_all(state: dict[str, object]) -> None:
    for source in cast(list[LogSource], state["opened"]):
        close_source(source)


def run_viewer(setup: ViewerSetup) -> Result[Unit, ViewerFailure]:
    tabs: list[dict[str, object]] = []
    opened: list[LogSource] = []
    cache: dict[tuple[int, int, int, int], ParsedLine] = {}
    suggestions: collections.OrderedDict[str, str] = collections.OrderedDict()
    state: dict[str, object] = {"tabs": tabs, "opened": opened, "cache": cache, "suggestions": suggestions, "frame": None, "meta": "", "setup": setup, "pipe": None, "rendered": False, "start": time.monotonic()}
    feed = setup.pipe
    if isinstance(feed, Some):
        state["pipe"] = (feed.value.descriptor, feed.value.path)
    else:
        state["pipe"] = None
    try:
        pending = _open_tabs(state, setup)
        try:
            bindings = KeyBindings()
            key_handler: Callable[[KeyPressEvent], None] = lambda event: _on_keys(state, event)
            bindings.add(Keys.Any)(key_handler)
            text_handler: Callable[[], StyleAndTextTuples] = lambda: _fragments(state)
            cursor_handler: Callable[[], Point | None] = lambda: _cursor(state)
            hidden_handler: Callable[[], bool] = lambda: _hidden(state)
            control = FormattedTextControl(text_handler, focusable=True, get_cursor_position=cursor_handler)
            window = Window(control, always_hide_cursor=Condition(hidden_handler))
            app: Application[None] = Application(layout=Layout(window), key_bindings=bindings, full_screen=True, mouse_support=True, refresh_interval=0.05)
            app.ttimeoutlen = 0.05
            app.timeoutlen = 0.05
            state["app"] = app
            size = app.output.get_size()
        except Exception as error:
            return Err(error=ViewerFailure_Terminal(message=str(error)))
        state["viewer"] = initial_viewer(setup.tabs, max(0, min(65535, size.columns)), max(0, min(65535, size.rows)))
        for event in pending:
            _event(state, event)
        render_handler: Callable[[Application[None]], None] = lambda application: _on_render(state)
        app.before_render += render_handler
        try:
            app.run()
        except Exception as error:
            if not cast(bool, state["rendered"]):
                return Err(error=ViewerFailure_Terminal(message=str(error)))
    except Exception:
        return Ok(value=UNIT)
    finally:
        _close_all(state)
    return Ok(value=UNIT)
