from cott_runtime import CottList

from real.pgcli.repl_types import StyledText, ToolbarState


def toolbar_fragments(toolbar: ToolbarState) -> CottList[StyledText]:
    base = "class:bottom-toolbar"
    out: list[StyledText] = [StyledText(style=base, text=" ")]
    if toolbar.smart_completion:
        out.append(StyledText(style="class:bottom-toolbar.on", text="[F2] Smart Completion: ON  "))
    else:
        out.append(StyledText(style="class:bottom-toolbar.off", text="[F2] Smart Completion: OFF  "))
    if toolbar.multi_line:
        out.append(StyledText(style="class:bottom-toolbar.on", text="[F3] Multiline: ON  "))
        if toolbar.multiline_mode == "safe":
            out.append(StyledText(style=base, text=" ([Esc] [Enter] to execute]) "))
        else:
            out.append(StyledText(style=base, text=" (Semi-colon [;] will end the line) "))
    else:
        out.append(StyledText(style="class:bottom-toolbar.off", text="[F3] Multiline: OFF  "))
    if toolbar.vi_mode:
        out.append(StyledText(style=base, text="[F4] Vi-mode (" + toolbar.vi_input_mode + ")  "))
    else:
        out.append(StyledText(style=base, text="[F4] Emacs-mode  "))
    if toolbar.explain_mode:
        out.append(StyledText(style=base, text="[F5] Explain: ON "))
    else:
        out.append(StyledText(style=base, text="[F5] Explain: OFF "))
    if toolbar.failed_transaction:
        out.append(StyledText(style="class:bottom-toolbar.transaction.failed", text="     Failed transaction"))
    if toolbar.valid_transaction:
        out.append(StyledText(style="class:bottom-toolbar.transaction.valid", text="     Transaction"))
    if toolbar.refreshing:
        out.append(StyledText(style=base, text="     Refreshing completions..."))
    return CottList(values=out)
