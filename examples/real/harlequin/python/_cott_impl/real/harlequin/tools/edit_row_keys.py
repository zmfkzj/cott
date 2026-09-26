from cott_runtime import CottList, Nothing, Some
from real.harlequin.tools_types import KeyRow


def edit_row_keys(row: KeyRow, keys: CottList[str], key_display: str) -> KeyRow:
    return KeyRow(
        action=row.action,
        title=row.title,
        keys=CottList(values=sorted({key for key in keys if key != ""})),
        key_display=Some(value=key_display) if key_display != "" else Nothing(),
    )
