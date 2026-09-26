import re

from cott_runtime import CottList
from real.toolong.text_types import SEARCH_SPLIT_PATTERN, SearchWord


def search_words(plain: str) -> CottList[SearchWord]:
    words: list[SearchWord] = []
    for piece in re.split(SEARCH_SPLIT_PATTERN, plain):
        if len(piece) > 1:
            for offset in range(1, len(piece) - 1):
                words.append(SearchWord(prefix=piece[:offset], word=piece))
    return CottList(values=words)
