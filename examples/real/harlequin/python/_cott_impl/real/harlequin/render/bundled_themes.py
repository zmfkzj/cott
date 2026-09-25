from cott_runtime import CottList

from real.harlequin.render_types import Theme


def bundled_themes() -> CottList[Theme]:
    return CottList(
        values=[
            Theme(name="harlequin", foreground="#DDDDDD", background="#0C0C0C", accent="#FEFFAC"),
            Theme(name="monokai", foreground="#F8F8F2", background="#272822", accent="#F92672"),
            Theme(name="dracula", foreground="#F8F8F2", background="#282A36", accent="#BD93F9"),
            Theme(name="nord", foreground="#D8DEE9", background="#2E3440", accent="#88C0D0"),
        ]
    )
