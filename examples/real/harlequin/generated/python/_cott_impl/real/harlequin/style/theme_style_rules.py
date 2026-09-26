from cott_runtime import CottList

from real.harlequin.style_types import StyleRule, ThemePalette


def theme_style_rules(palette: ThemePalette) -> CottList[StyleRule]:
    p = palette.primary
    s = palette.secondary
    a = palette.accent
    f = palette.foreground
    b = palette.background
    u = palette.surface
    n = palette.panel
    w = palette.warning
    e = palette.error_color
    g = palette.success
    muted = f"fg:{n} bg:{b}" if n != b else f"fg:{f} bg:{b} italic"
    pairs: list[tuple[str, str]] = [
        ("", f"fg:{f} bg:{b}"),
        ("hq.text", f"fg:{f} bg:{b}"),
        ("hq.muted", muted),
        ("hq.border", f"fg:{n} bg:{b}"),
        ("hq.border.focused", f"fg:{p} bg:{b}"),
        ("hq.title", f"fg:{n} bg:{b} bold"),
        ("hq.title.focused", f"fg:{p} bg:{b} bold"),
        ("hq.tab", f"fg:{f} bg:{u}"),
        ("hq.tab.active", f"fg:{b} bg:{p} bold"),
        ("hq.header", f"fg:{p} bg:{u} bold"),
        ("hq.cell", f"fg:{f} bg:{b}"),
        ("hq.cell.null", f"fg:{n} bg:{b} italic"),
        ("hq.cell.number", f"fg:{s} bg:{b}"),
        ("hq.cursor", f"fg:{b} bg:{a} bold"),
        ("hq.selection", f"fg:{b} bg:{s}"),
        ("hq.rownumber", f"fg:{n} bg:{b}"),
        ("hq.tree.label", f"fg:{f} bg:{b}"),
        ("hq.tree.type", f"fg:{n} bg:{b} italic"),
        ("hq.tree.guide", f"fg:{n} bg:{b}"),
        ("hq.footer", f"fg:{f} bg:{u}"),
        ("hq.footer.key", f"fg:{p} bg:{u} bold"),
        ("hq.footer.description", f"fg:{f} bg:{u}"),
        ("hq.status", f"fg:{f} bg:{u}"),
        ("hq.error", f"fg:{e} bg:{b} bold"),
        ("hq.warning", f"fg:{w} bg:{b} bold"),
        ("hq.success", f"fg:{g} bg:{b} bold"),
        ("hq.notification", f"fg:{f} bg:{n}"),
        ("hq.notification.error", f"fg:{b} bg:{e} bold"),
        ("hq.dialog", f"fg:{f} bg:{u}"),
        ("hq.dialog.title", f"fg:{p} bg:{u} bold"),
        ("hq.input", f"fg:{f} bg:{b}"),
        ("hq.button", f"fg:{f} bg:{n}"),
        ("hq.button.focused", f"fg:{b} bg:{p} bold"),
        ("hq.match", f"fg:{a} bg:{b} bold underline"),
        ("hq.loading", f"fg:{a} bg:{b} bold"),
        ("line-number", f"fg:{n} bg:{b}"),
        ("line-number.current", f"fg:{p} bg:{b} bold"),
        ("selected", f"fg:{b} bg:{s}"),
        ("search", f"fg:{b} bg:{w}"),
        ("search.current", f"fg:{b} bg:{a}"),
        ("completion-menu", f"fg:{f} bg:{n}"),
        ("completion-menu.completion.current", f"fg:{b} bg:{p} bold"),
        ("completion-menu.meta.completion", f"fg:{f} bg:{u}"),
        ("completion-menu.meta.completion.current", f"fg:{b} bg:{p}"),
        ("scrollbar.background", f"bg:{u}"),
        ("scrollbar.button", f"bg:{n}"),
        ("frame.border", f"fg:{n}"),
        ("frame.label", f"fg:{p} bold"),
        ("dialog", f"fg:{f} bg:{b}"),
        ("dialog.body", f"fg:{f} bg:{u}"),
        ("dialog frame.label", f"fg:{p} bold"),
        ("button", f"fg:{f} bg:{n}"),
        ("button.focused", f"fg:{b} bg:{p} bold"),
        ("text-area", f"fg:{f} bg:{b}"),
        ("pygments.keyword", f"fg:{p} bold"),
        ("pygments.name.builtin", f"fg:{s}"),
        ("pygments.name.function", f"fg:{s}"),
        ("pygments.literal.string", f"fg:{g}"),
        ("pygments.literal.number", f"fg:{a}"),
        ("pygments.comment", f"fg:{n} italic"),
        ("pygments.operator", f"fg:{a}"),
        ("pygments.punctuation", f"fg:{f}"),
        ("pygments.name", f"fg:{f}"),
    ]
    return CottList(values=[StyleRule(selector=sel, style=sty) for sel, sty in pairs])
