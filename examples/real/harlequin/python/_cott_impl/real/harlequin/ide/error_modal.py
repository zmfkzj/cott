from typing import Final

from cott_runtime import CottList

from real.harlequin.ide_types import TextModal

_FOOTER: Final[str] = "Arrows/PgUp/PgDn scroll. Click text or press c to copy. Any other key closes."
_COPY_NOTICE: Final[str] = "Error copied to clipboard."


def error_modal(title: str, header: str, message: str) -> TextModal:
    return TextModal(
        title=title,
        header=header,
        lines=CottList(values=message.split("\n")),
        footer=_FOOTER,
        scroll=0,
        copyable=True,
        copy_text=message,
        copy_notice=_COPY_NOTICE,
        close_on_any_key=True,
    )
