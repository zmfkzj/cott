def _name_label(name: str) -> str:
    match name:
        case "enter":
            return "⏎"
        case "escape":
            return "esc"
        case "backspace":
            return "⌫"
        case "delete":
            return "del"
        case "pageup":
            return "pgup"
        case "pagedown":
            return "pgdn"
        case "space":
            return "space"
        case "full_stop":
            return "."
        case "underscore":
            return "_"
        case "up":
            return "↑"
        case "down":
            return "↓"
        case "left":
            return "←"
        case "right":
            return "→"
        case _:
            return name


def key_label(key: str) -> str:
    prefix = ""
    rest = key
    while True:
        if rest.startswith("ctrl+") and len(rest) > 5:
            prefix += "^"
            rest = rest[5:]
        elif rest.startswith("shift+") and len(rest) > 6:
            prefix += "⇧"
            rest = rest[6:]
        elif rest.startswith("alt+") and len(rest) > 4:
            prefix += "⌥"
            rest = rest[4:]
        else:
            break
    return prefix + _name_label(rest)
