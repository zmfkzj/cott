from cott_runtime import CottList


def parse_function_defaults(defaults: str) -> CottList[str]:
    result: list[str] = []
    if not defaults:
        return CottList(values=result)
    current = ""
    quote: str | None = None
    for char in defaults:
        if current == "" and char == " ":
            continue
        if char == '"' or char == "'":
            if quote is not None and char == quote:
                quote = None
            elif quote is None:
                quote = char
            current += char
        elif char == "," and quote is None:
            result.append(current)
            current = ""
        else:
            current += char
    result.append(current)
    return CottList(values=result)
