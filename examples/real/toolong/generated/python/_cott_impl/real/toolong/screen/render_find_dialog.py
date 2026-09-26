from rich.cells import cell_len

from cott_runtime import CottList, Nothing, Some, U16
from real.toolong.model_types import FindQuery, ScreenRow, StyledRun, StyledSpan, StyledText, TermColor_Rgb
from real.toolong.screen import text_runs, theme_color
from real.toolong.screen_types import Cursor, FindDialogView, ThemeColor, ThemeColor_Accent, ThemeColor_Background, ThemeColor_Error, ThemeColor_Muted, ThemeColor_Panel, ThemeColor_Success, ThemeColor_Surface, ThemeColor_Text
from real.toolong.text import line_matches
from real.toolong.view_types import Focus, Focus_FindCase, Focus_FindInput, Focus_FindRegex, TabView


def _hex(color: ThemeColor) -> str:
    value = theme_color(color)
    if isinstance(value, TermColor_Rgb):
        return "#%02x%02x%02x" % (value.red, value.green, value.blue)
    else:
        return "default"


def _code(fg: ThemeColor, bold: bool, underline: bool) -> str:
    code = "fg:" + _hex(fg) + " bg:" + _hex(ThemeColor_Surface())
    if bold:
        code += " bold"
    if underline:
        code += " underline"
    return code


def _put(cells: list[tuple[str, str]], text: str, style: str) -> None:
    for ch in text:
        cells.append((ch, style))


def _runs_to_cells(runs: CottList[StyledRun]) -> list[tuple[str, str]]:
    cells: list[tuple[str, str]] = []
    for run in runs:
        for ch in run.text:
            size = cell_len(ch)
            if size <= 0:
                continue
            cells.append((ch, run.style))
            if size == 2:
                cells.append(("", run.style))
    return cells


def _bordered(content: list[tuple[str, str]], w: int, color: ThemeColor) -> list[list[tuple[str, str]]]:
    bs = _code(color, False, False)
    blank = _code(ThemeColor_Text(), False, False)
    inner = max(0, w - 2)
    body = content[:inner]
    while len(body) < inner:
        body.append((" ", blank))
    top: list[tuple[str, str]] = []
    mid: list[tuple[str, str]] = []
    bot: list[tuple[str, str]] = []
    _put(top, "▊" + "▔" * inner + "▎", bs)
    _put(mid, "▊", bs)
    mid.extend(body)
    _put(mid, "▎", bs)
    _put(bot, "▊" + "▁" * inner + "▎", bs)
    return [top[:w], mid[:w], bot[:w]]


def _checkbox(label: str, on: bool, focused: bool) -> list[tuple[str, str]]:
    blank = _code(ThemeColor_Text(), False, False)
    panel = _code(ThemeColor_Panel(), False, False)
    mark = _code(ThemeColor_Success(), True, False) if on else _code(ThemeColor_Muted(), False, False)
    cells: list[tuple[str, str]] = []
    _put(cells, " ", blank)
    _put(cells, "▐", panel)
    _put(cells, "X", mark)
    _put(cells, "▌", panel)
    _put(cells, " ", blank)
    _put(cells, label, _code(ThemeColor_Text(), False, focused))
    _put(cells, " ", blank)
    return cells


def _to_row(cells: list[tuple[str, str]]) -> ScreenRow:
    texts: list[str] = []
    styles: list[str] = []
    for ch, st in cells:
        if styles and styles[-1] == st:
            texts[-1] += ch
        else:
            texts.append(ch)
            styles.append(st)
    runs: list[StyledRun] = []
    for text, st in zip(texts, styles):
        if text:
            runs.append(StyledRun(text=text, style=st))
    return ScreenRow(runs=CottList(values=runs))


def render_find_dialog(tab: TabView, width: U16, focus: Focus, suggestion: str) -> FindDialogView:
    blank = _code(ThemeColor_Text(), False, False)
    input_focus = isinstance(focus, Focus_FindInput)
    rows: list[list[tuple[str, str]]] = [[], [], [], []]
    cursor_x = -1

    input_w = width - 35
    if input_w > 0:
        value = tab.find_input.value
        pos = tab.find_input.cursor
        area = max(0, input_w - 6)
        content: list[tuple[str, str]] = []
        _put(content, "  ", blank)
        start = 0
        if value == "":
            styled = StyledText(text="Regex" if tab.regex else "Find", spans=CottList(values=[]))
            base = _code(ThemeColor_Muted(), False, False)
        else:
            start = max(0, pos - (area - 1))
            shown = value[start:]
            spans: list[StyledSpan] = []
            if input_focus and len(suggestion) > len(value):
                extra = suggestion[len(value):]
                spans.append(StyledSpan(start=len(shown), end=len(shown) + len(extra), style="fg:" + _hex(ThemeColor_Muted())))
                shown = shown + extra
            styled = StyledText(text=shown, spans=CottList(values=spans))
            base = blank
        content.extend(_runs_to_cells(text_runs(styled, base, 0, area, blank)))
        _put(content, "  ", blank)
        if input_focus:
            color: ThemeColor = ThemeColor_Accent()
        elif tab.regex and line_matches(" ", FindQuery(text=value, regex=True, case_sensitive=False)).invalid_regex:
            color = ThemeColor_Error()
        else:
            color = ThemeColor_Background()
        box = _bordered(content, input_w, color)
        for i in range(3):
            rows[i + 1].extend(box[i])
        if input_focus:
            before = value[start:pos] if value != "" else ""
            cursor_x = 3 + cell_len(before)

    for label, on, focused, left, right in (
        ("Case sensitive", tab.case_sensitive, isinstance(focus, Focus_FindCase), width - 35, width - 13),
        ("Regex", tab.regex, isinstance(focus, Focus_FindRegex), width - 13, width),
    ):
        w = right - left
        if left < 0 or w <= 0:
            continue
        for i in range(1, 4):
            while len(rows[i]) < left:
                rows[i].append((" ", blank))
        box = _bordered(_checkbox(label, on, focused), w, ThemeColor_Accent() if focused else ThemeColor_Background())
        for i in range(3):
            rows[i + 1].extend(box[i])

    for r in rows:
        while len(r) < width:
            r.append((" ", blank))
    screen_rows = CottList(values=[_to_row(r[:width]) for r in rows])
    if cursor_x >= 0:
        return FindDialogView(rows=screen_rows, cursor=Some(value=Cursor(x=cursor_x, y=2)))
    else:
        return FindDialogView(rows=screen_rows, cursor=Nothing())
