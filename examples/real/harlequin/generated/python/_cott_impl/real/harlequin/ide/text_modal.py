from cott_runtime import CottList

from real.harlequin.ide_types import TextModal


def text_modal(title: str, header: str, body: str, footer: str, copy_notice: str) -> TextModal:
    return TextModal(
        title=title,
        header=header,
        lines=CottList(values=body.split("\n")),
        footer=footer,
        scroll=0,
        copyable=True,
        copy_text=body,
        copy_notice=copy_notice,
        close_on_any_key=True,
    )
