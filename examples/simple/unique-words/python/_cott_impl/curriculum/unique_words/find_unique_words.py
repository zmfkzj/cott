import unicodedata

from cott_runtime import CottList


def find_unique_words(text: str) -> CottList[str]:
    normalized: str = unicodedata.normalize("NFKC", text)
    normalized = unicodedata.normalize("NFKC", normalized.casefold())
    current: list[str] = []
    counts: dict[str, int] = {}
    for character in normalized:
        if character.isalnum() or character == "_":
            current.append(character)
        elif current:
            word: str = "".join(current)
            counts[word] = counts.get(word, 0) + 1
            current.clear()
    if current:
        word = "".join(current)
        counts[word] = counts.get(word, 0) + 1

    return CottList(values=sorted(word for word, count in counts.items() if count == 1))
