from cott_runtime import CottList, Some
from real.harlequin.keymap_types import KeyBinding, KeyMap
from real.harlequin.tools_types import KeyRow


def rows_to_keymap(name: str, rows: CottList[KeyRow]) -> KeyMap:
    return KeyMap(
        name=name,
        bindings=CottList(
            values=[
                KeyBinding(
                    keys=",".join(row.keys),
                    action=row.action,
                    key_display=row.key_display,
                )
                for row in rows
                if len(row.keys) > 0 or isinstance(row.key_display, Some)
            ]
        ),
    )
