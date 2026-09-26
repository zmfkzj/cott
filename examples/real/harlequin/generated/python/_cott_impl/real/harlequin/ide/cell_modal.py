from cott_runtime import CottList
from real.harlequin.ide_types import TextModal


def cell_modal(column: str, value: str) -> TextModal:
    title = column if column != "" else "Cell Contents"
    return TextModal(
        title=title,
        header="",
        lines=CottList(values=value.split("\n")),
        footer="Arrows/PgUp/PgDn scroll. Click text or press c to copy. Any other key closes.",
        scroll=0,
        copyable=True,
        copy_text=value,
        copy_notice="Cell value copied to clipboard.",
        close_on_any_key=True,
    )
