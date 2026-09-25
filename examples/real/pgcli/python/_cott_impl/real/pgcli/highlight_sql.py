from real.pgcli_types import HighlightRequest, HighlightedSql, SQL_KEYWORDS


def _is_word_char(ch: str) -> bool:
    return ch == "_" or "a" <= ch <= "z" or "A" <= ch <= "Z"


def _dollar_tag(source: str, start: int) -> str | None:
    end = start + 1
    if end < len(source) and source[end] == "$":
        return "$$"
    if end >= len(source) or not _is_word_char(source[end]):
        return None
    end += 1
    while end < len(source) and (_is_word_char(source[end]) or "0" <= source[end] <= "9"):
        end += 1
    if end < len(source) and source[end] == "$":
        return source[start : end + 1]
    return None


def _quoted_end(source: str, start: int, quote: str) -> int:
    end = start + 1
    while end < len(source):
        if source[end] != quote:
            end += 1
        elif end + 1 < len(source) and source[end + 1] == quote:
            end += 2
        else:
            return end + 1
    return -1


def highlight_sql(request: HighlightRequest) -> HighlightedSql:
    source = request.source
    color = request.color
    output: list[str] = []
    keywords: set[str] = set(SQL_KEYWORDS.split()) if color else set()
    index = 0
    contains_error = False

    while index < len(source):
        ch = source[index]
        if ch == "'" or ch == '"':
            end = _quoted_end(source, index, ch)
            if end < 0:
                contains_error = True
                if color:
                    output.append(source[index:])
                break
            if color:
                quoted = source[index:end]
                output.append("\x1b[32m" + quoted + "\x1b[0m" if ch == "'" else quoted)
            index = end
        elif ch == "-" and index + 1 < len(source) and source[index + 1] == "-":
            end = source.find("\n", index + 2)
            end = len(source) if end < 0 else end
            if color:
                output.append(source[index:end])
            index = end
        elif ch == "/" and index + 1 < len(source) and source[index + 1] == "*":
            end = source.find("*/", index + 2)
            if end < 0:
                contains_error = True
                end = len(source)
            else:
                end += 2
            if color:
                output.append(source[index:end])
            index = end
        elif ch == "$":
            tag = _dollar_tag(source, index)
            if tag is None:
                if color:
                    output.append(ch)
                index += 1
            else:
                end = source.find(tag, index + len(tag))
                if end < 0:
                    contains_error = True
                    end = len(source)
                else:
                    end += len(tag)
                if color:
                    output.append(source[index:end])
                index = end
        elif _is_word_char(ch):
            end = index + 1
            while end < len(source) and _is_word_char(source[end]):
                end += 1
            if color:
                word = source[index:end]
                if word.upper() in keywords:
                    output.append("\x1b[1m" + word + "\x1b[0m")
                else:
                    output.append(word)
            index = end
        else:
            if color:
                output.append(ch)
            index += 1

    return HighlightedSql(
        text="".join(output) if color else source,
        contains_error=contains_error,
    )
