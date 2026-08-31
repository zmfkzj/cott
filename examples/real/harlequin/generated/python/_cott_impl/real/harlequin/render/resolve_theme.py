from cott_runtime import CottList, Nothing, Option, Some
from real.harlequin.render_types import Theme


def resolve_theme(themes: CottList[Theme], name: str) -> Option[Theme]:
    for theme in themes:
        if theme.name == name:
            return Some(value=theme)
    return Nothing()
