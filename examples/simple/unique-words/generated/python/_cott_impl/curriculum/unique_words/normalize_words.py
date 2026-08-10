import unicodedata

from cott_runtime import CottList


def normalize_words(text: str) -> CottList[str]:
    """Normalize text and return its Unicode words in source order."""
    normalized: str = unicodedata.normalize("NFKC", text)
    normalized = unicodedata.normalize("NFKC", normalized.casefold())
    words: list[str] = []
    current: list[str] = []

    for character in normalized:
        if character.isalnum() or character == "_":
            current.append(character)
        elif current:
            words.append("".join(current))
            current.clear()

    if current:
        words.append("".join(current))

    return CottList(values=words)
