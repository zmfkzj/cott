from real.toolong.model_types import TermColor, TermColor_Rgb
from real.toolong.screen_types import ThemeColor, ThemeColor_Accent, ThemeColor_AccentDark, ThemeColor_Background, ThemeColor_Black, ThemeColor_Error, ThemeColor_ErrorDark, ThemeColor_LineNumber, ThemeColor_Muted, ThemeColor_Panel, ThemeColor_Primary, ThemeColor_Success, ThemeColor_SuccessDark, ThemeColor_Surface, ThemeColor_TailBackground, ThemeColor_Text, ThemeColor_Thumb, ThemeColor_Track, ThemeColor_Underline, ThemeColor_Warning


def theme_color(color: ThemeColor) -> TermColor:
    if isinstance(color, ThemeColor_Surface):
        return TermColor_Rgb(red=30, green=30, blue=30)
    if isinstance(color, ThemeColor_Background):
        return TermColor_Rgb(red=18, green=18, blue=18)
    if isinstance(color, ThemeColor_Text):
        return TermColor_Rgb(red=225, green=225, blue=225)
    if isinstance(color, ThemeColor_Muted):
        return TermColor_Rgb(red=115, green=115, blue=115)
    if isinstance(color, ThemeColor_Accent):
        return TermColor_Rgb(red=1, green=120, blue=212)
    if isinstance(color, ThemeColor_AccentDark):
        return TermColor_Rgb(red=0, green=83, blue=170)
    if isinstance(color, ThemeColor_Panel):
        return TermColor_Rgb(red=36, green=41, blue=47)
    if isinstance(color, ThemeColor_Primary):
        return TermColor_Rgb(red=0, green=69, blue=120)
    if isinstance(color, ThemeColor_Warning):
        return TermColor_Rgb(red=254, green=166, blue=43)
    if isinstance(color, ThemeColor_Success):
        return TermColor_Rgb(red=78, green=191, blue=113)
    if isinstance(color, ThemeColor_Error):
        return TermColor_Rgb(red=185, green=60, blue=91)
    if isinstance(color, ThemeColor_LineNumber):
        return TermColor_Rgb(red=186, green=125, blue=39)
    if isinstance(color, ThemeColor_TailBackground):
        return TermColor_Rgb(red=37, green=54, blue=42)
    if isinstance(color, ThemeColor_Track):
        return TermColor_Rgb(red=20, green=25, blue=31)
    if isinstance(color, ThemeColor_Thumb):
        return TermColor_Rgb(red=35, green=86, blue=139)
    if isinstance(color, ThemeColor_Underline):
        return TermColor_Rgb(red=51, green=51, blue=51)
    if isinstance(color, ThemeColor_Black):
        return TermColor_Rgb(red=0, green=0, blue=0)
    if isinstance(color, ThemeColor_SuccessDark):
        return TermColor_Rgb(red=54, green=170, blue=94)
    if isinstance(color, ThemeColor_ErrorDark):
        return TermColor_Rgb(red=163, green=37, blue=73)
    else:
        return TermColor_Rgb(red=231, green=146, blue=13)
