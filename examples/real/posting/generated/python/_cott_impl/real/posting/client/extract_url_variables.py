from cott_runtime import CottList


def extract_url_variables(url: str) -> CottList[str]:
    variables: list[str] = []
    index: int = 0
    length: int = len(url)
    while index < length:
        if url[index] != ":":
            index += 1
            continue
        if index + 1 < length and url[index + 1] == ":":
            index += 2
            continue

        start: int = index + 1
        if start >= length or not ("A" <= url[start] <= "Z" or "a" <= url[start] <= "z" or url[start] == "_"):
            index += 1
            continue

        end: int = start + 1
        while end < length and ("A" <= url[end] <= "Z" or "a" <= url[end] <= "z" or "0" <= url[end] <= "9" or url[end] == "_"):
            end += 1
        variables.append(url[start:end])
        index = end

    return CottList(values=tuple(variables))
