from cott_runtime import CottList
from real.harlequin.render_types import KeyBinding, Keymap


def bundled_keymaps() -> CottList[Keymap]:
    return CottList(
        values=[
            Keymap(
                name="default",
                bindings=CottList(
                    values=[
                        KeyBinding(key="ctrl+enter", command="execute"),
                        KeyBinding(key="ctrl+s", command="save"),
                        KeyBinding(key="ctrl+q", command="quit"),
                    ]
                ),
            ),
            Keymap(
                name="vim",
                bindings=CottList(
                    values=[
                        KeyBinding(key="ctrl+enter", command="execute"),
                        KeyBinding(key=":w", command="save"),
                        KeyBinding(key=":q", command="quit"),
                    ]
                ),
            ),
        ]
    )
