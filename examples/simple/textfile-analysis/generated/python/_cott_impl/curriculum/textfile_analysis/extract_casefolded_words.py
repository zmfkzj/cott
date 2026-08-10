from cott_runtime import CottList


def extract_casefolded_words(text: str) -> CottList[str]:
    words: list[str] = []
    current_word: list[str] = []
    for character in text.casefold():
        if character.isalnum():
            current_word.append(character)
        elif current_word:
            words.append("".join(current_word))
            current_word = []
    if current_word:
        words.append("".join(current_word))
    return CottList(values=words)
