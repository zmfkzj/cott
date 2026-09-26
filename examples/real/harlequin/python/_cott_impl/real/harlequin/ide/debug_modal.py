from cott_runtime import CottList

from real.harlequin.ide_types import DebugSection, TextModal


def debug_modal(sections: CottList[DebugSection]) -> TextModal:
    lines: list[str] = []
    for section in sections:
        lines.append(f"## {section.title}")
        for line in section.body:
            lines.append(line)
        lines.append("")
    return TextModal(
        title="Debug Information",
        header="Details about the current Harlequin session, environment, and adapter.",
        lines=CottList(values=lines),
        footer="Tab/Shift Tab to move focus, Enter to expand/collapse, Esc to close.",
        scroll=0,
        copyable=True,
        copy_text="\n".join(lines),
        copy_notice="Copied to clipboard.",
        close_on_any_key=False,
    )
