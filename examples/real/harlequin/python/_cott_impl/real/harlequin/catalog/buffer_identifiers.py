from typing import Final

from cott_runtime import CottList

_KEYWORDS: Final[str] = "alter and as between by cascade case column copy create cross current database delete distinct drop end except exclude exists false filter following from full function grant group having if ilike inner insert intersect join lateral left like limit merge natural not offset on or order outer over owner partition preceding qualify range rename replace restrict revoke right row rows schema select sequence set similar table temp temporary then to top true truncate unbounded union update using view when where with"


def _is_word_char(ch: str) -> bool:
    return ch.isalnum() or ch == "_" or ch == "$"


def _add(names: list[str], seen: set[str], name: str) -> None:
    key = name.casefold()
    if key not in seen:
        seen.add(key)
        names.append(name)


def _quoted_end(text: str, start: int, closer: str) -> int:
    n = len(text)
    i = start
    while True:
        end = text.find(closer, i)
        if end < 0:
            return -1
        if end + 1 < n and text[end + 1] == closer:
            i = end + 2
            continue
        return end


def buffer_identifiers(text: str) -> CottList[str]:
    keywords: set[str] = set(_KEYWORDS.split())
    names: list[str] = []
    seen: set[str] = set()
    n = len(text)
    i = 0
    while i < n:
        ch = text[i]
        if ch == "-" and text.startswith("--", i):
            end = text.find("\n", i)
            i = n if end < 0 else end + 1
        elif ch == "/" and text.startswith("/*", i):
            end = text.find("*/", i + 2)
            i = n if end < 0 else end + 2
        elif ch == "'":
            end = _quoted_end(text, i + 1, "'")
            i = n if end < 0 else end + 1
        elif ch == '"' or ch == "`" or ch == "[":
            closer = "]" if ch == "[" else ch
            end = _quoted_end(text, i + 1, closer)
            stop = n if end < 0 else end
            name = text[i + 1 : stop].replace(closer + closer, closer)
            if name:
                _add(names, seen, name)
            i = n if end < 0 else end + 1
        elif _is_word_char(ch):
            start = i
            while i < n and _is_word_char(text[i]):
                i += 1
            word = text[start:i]
            if not word[0].isdigit() and word.casefold() not in keywords:
                _add(names, seen, word)
        else:
            i += 1
    return CottList(values=names)
