from cott_runtime import Err, Ok, Result

from real.harlequin.style import theme_palettes
from real.harlequin.style_types import ThemeError, ThemeError_UnknownTheme, ThemePalette


def find_theme(name: str) -> Result[ThemePalette, ThemeError]:
    for palette in theme_palettes():
        if palette.name == name:
            return Ok(value=palette)
    return Err(error=ThemeError_UnknownTheme(name=name))
