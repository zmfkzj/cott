from frogmouth.locations import normalize_local_path


def resolve_local_path(text: str, home: str, working_directory: str) -> str:
    if text == "~":
        expanded = home
    elif text.startswith("~/"):
        expanded = home + "/" + text[2:]
    else:
        expanded = text
    return normalize_local_path(working_directory, expanded)
