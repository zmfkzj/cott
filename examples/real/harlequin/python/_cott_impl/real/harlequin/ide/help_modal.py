from cott_runtime import CottList

from real.harlequin.ide import help_markdown
from real.harlequin.ide_types import TextModal


def help_modal(key_lines: CottList[str]) -> TextModal:
    lines: list[str] = [line for line in key_lines]
    lines.append("")
    lines.extend(help_markdown().splitlines())
    return TextModal(
        title="Harlequin Help",
        header=(
            "Welcome to Harlequin! This screen contains a small subset of the online docs, "
            "available at https://harlequin.sh/docs/getting-started"
        ),
        lines=CottList(values=lines),
        footer="Scroll with arrows. Press any other key to continue.",
        scroll=0,
        copyable=False,
        copy_text="",
        copy_notice="",
        close_on_any_key=True,
    )
