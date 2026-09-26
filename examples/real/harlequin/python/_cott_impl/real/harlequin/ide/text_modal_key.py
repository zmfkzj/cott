from cott_runtime import U64
from real.harlequin.ide_types import TextModal, TextModalOutcome_Close, TextModalOutcome_Copy, TextModalOutcome_Stay, TextModalStep


def _scrolled(modal: TextModal, scroll: int) -> TextModalStep:
    return TextModalStep(modal=TextModal(title=modal.title, header=modal.header, lines=modal.lines, footer=modal.footer, scroll=scroll, copyable=modal.copyable, copy_text=modal.copy_text, copy_notice=modal.copy_notice, close_on_any_key=modal.close_on_any_key), outcome=TextModalOutcome_Stay())


def text_modal_key(modal: TextModal, key: str, visible_lines: U64) -> TextModalStep:
    count = len([line for line in modal.lines])
    max_scroll = max(count - visible_lines, 0)
    page = max(visible_lines - 1, 1)
    scroll = min(modal.scroll, max_scroll)
    if key == "up":
        return _scrolled(modal, max(scroll - 1, 0))
    if key == "down":
        return _scrolled(modal, min(scroll + 1, max_scroll))
    if key == "pageup":
        return _scrolled(modal, max(scroll - page, 0))
    if key == "pagedown":
        return _scrolled(modal, min(scroll + page, max_scroll))
    if key == "home":
        return _scrolled(modal, 0)
    if key == "end":
        return _scrolled(modal, max_scroll)
    if key == "c" and modal.copyable:
        return TextModalStep(modal=modal, outcome=TextModalOutcome_Copy(text=modal.copy_text, notice=modal.copy_notice))
    if key == "escape" or modal.close_on_any_key:
        return TextModalStep(modal=modal, outcome=TextModalOutcome_Close())
    return TextModalStep(modal=modal, outcome=TextModalOutcome_Stay())
