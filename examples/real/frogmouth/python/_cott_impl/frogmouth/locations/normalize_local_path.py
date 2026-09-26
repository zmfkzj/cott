def normalize_local_path(directory: str, path: str) -> str:
    if path.startswith("/"):
        combined = path
    elif path == "":
        combined = directory
    else:
        combined = directory + "/" + path
    kept: list[str] = []
    for segment in combined.split("/"):
        if segment == "" or segment == ".":
            continue
        if segment == "..":
            if kept:
                kept.pop()
            continue
        kept.append(segment)
    absolute = combined.startswith("/")
    if not kept:
        return "/" if absolute else "."
    joined = "/".join(kept)
    return "/" + joined if absolute else joined
