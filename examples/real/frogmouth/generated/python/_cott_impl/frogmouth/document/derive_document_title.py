def derive_document_title(markdown: str, fallback: str) -> str:
    for line in markdown.splitlines():
        candidate = line.strip()
        if candidate.startswith("# "):
            title = candidate[2:].strip()
            if title:
                return title
    return fallback
