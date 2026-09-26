from cott_runtime import CottList

from real.harlequin.style_types import ThemePalette


def theme_palettes() -> CottList[ThemePalette]:
    rows: list[tuple[str, bool, str, str, str, str, str, str, str, str, str, str]] = [
        ("harlequin", True, "#FEFFAC", "#45FFCA", "#FFB6D9", "#DDDDDD", "#0C0C0C", "#0C0C0C", "#555555", "#FEFFAC", "#FFB6D9", "#45FFCA"),
        ("textual-dark", True, "#0178D4", "#004578", "#FEA62B", "#E0E0E0", "#121212", "#1E1E1E", "#242F38", "#FEA62B", "#B93C5B", "#4EBF71"),
        ("textual-light", False, "#004578", "#0178D4", "#FEA62B", "#1F1F1F", "#E0E0E0", "#D8D8D8", "#D0D0D0", "#FEA62B", "#B93C5B", "#4EBF71"),
        ("nord", True, "#88C0D0", "#81A1C1", "#B48EAD", "#D8DEE9", "#2E3440", "#3B4252", "#434C5E", "#EACB8B", "#BE616A", "#A3BE8C"),
        ("gruvbox", True, "#85A598", "#A89A85", "#F9BD2F", "#FBF1C7", "#282828", "#3C3836", "#504945", "#FD8019", "#FA4934", "#B7BB26"),
        ("catppuccin-mocha", True, "#F5C2E7", "#CBA6F7", "#F9B387", "#CDD6F4", "#181825", "#313244", "#45475A", "#FAE3B0", "#F28FAD", "#ABE9B3"),
        ("dracula", True, "#BD93F9", "#6272A4", "#FF79C6", "#F8F8F2", "#282A36", "#2B2E3B", "#313442", "#FEB86C", "#FE5555", "#50FA7B"),
        ("tokyo-night", True, "#BB9AF7", "#7AA2F7", "#FE9E64", "#A9B1D6", "#1A1B26", "#24283B", "#414868", "#DFAF68", "#F6768E", "#9ECE6A"),
        ("monokai", True, "#AE81FF", "#F82672", "#66D9EF", "#D6D6D6", "#272822", "#2E2E2E", "#3E3D32", "#FC971F", "#F82672", "#A5E22E"),
        ("flexoki", True, "#205EA6", "#24837B", "#9B76C8", "#FFFCF0", "#100F0F", "#1C1B1A", "#282726", "#AC8301", "#AE3029", "#65800B"),
        ("catppuccin-latte", False, "#8839EF", "#DB8A78", "#FD640B", "#4C4F69", "#EFF1F5", "#E6E9EF", "#CCD0DA", "#DE8E1D", "#D10F39", "#40A02B"),
        ("catppuccin-frappe", True, "#CA9EE6", "#EE9F76", "#F4B8E4", "#C6D0F5", "#303446", "#414559", "#51576D", "#E4C890", "#E68284", "#A6D189"),
        ("catppuccin-macchiato", True, "#C6A0F6", "#F4A97F", "#F5BDE6", "#CAD3F5", "#24273A", "#363A4F", "#494D64", "#EED49F", "#ED8796", "#A6DA95"),
        ("solarized-light", False, "#268BD2", "#2AA198", "#6C71C4", "#586E75", "#FDF6E3", "#EEE8D5", "#EEE8D5", "#CA4B16", "#DB322F", "#849900"),
        ("solarized-dark", True, "#268BD2", "#2AA198", "#6C71C4", "#839496", "#002B36", "#073642", "#073642", "#CA4B16", "#DB322F", "#849900"),
        ("rose-pine", True, "#C4A7E7", "#31748F", "#EBBCBA", "#E0DEF4", "#191724", "#1F1D2E", "#26233A", "#F5C177", "#EA6F92", "#9CCFD8"),
        ("rose-pine-moon", True, "#C4A7E7", "#3E8FB0", "#EA9A97", "#E0DEF4", "#232136", "#2A273F", "#393552", "#F5C177", "#EA6F92", "#9CCFD8"),
        ("rose-pine-dawn", False, "#907AA9", "#286983", "#D6827E", "#575279", "#FAF4ED", "#FFFAF3", "#F2E9E1", "#E99D34", "#B4637A", "#56949F"),
        ("atom-one-dark", True, "#61AFEF", "#C678DD", "#A378C2", "#ABB2BF", "#282C34", "#3B414D", "#4F5666", "#DDB25B", "#EF6262", "#62F062"),
        ("atom-one-light", False, "#4078F2", "#A626A4", "#BE9232", "#383A42", "#FAFAFA", "#E0E0E0", "#CCCCCC", "#D7D938", "#F13F3F", "#6BF23F"),
    ]
    return CottList(
        values=[
            ThemePalette(
                name=n,
                dark=d,
                primary=p,
                secondary=s,
                accent=a,
                foreground=f,
                background=b,
                surface=u,
                panel=pn,
                warning=w,
                error_color=e,
                success=g,
            )
            for (n, d, p, s, a, f, b, u, pn, w, e, g) in rows
        ]
    )
