from cott_runtime import CottList, Nothing, Option, Some
from real.harlequin.render_types import Keymap


def resolve_keymap(keymaps: CottList[Keymap], name: str) -> Option[Keymap]:
    for keymap in keymaps:
        if keymap.name == name:
            return Some(value=keymap)
    return Nothing()
