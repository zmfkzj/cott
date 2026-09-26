from functools import cmp_to_key

from cott_runtime import CottList


def _tokens(path: str) -> list[int | str]:
    name = path.split("/")[-1]
    result: list[int | str] = []
    for part in name.split("."):
        if part.isdigit():
            result.append(int(part))
        else:
            result.append(part.lower())
    return result


def _token_less(a: int | str, b: int | str) -> bool:
    if isinstance(a, int) and isinstance(b, int):
        return a < b
    if isinstance(a, str) and isinstance(b, str):
        return a < b
    return str(a) < str(b)


def _compare(a: str, b: str) -> int:
    tokens_a = _tokens(a)
    tokens_b = _tokens(b)
    for token_a, token_b in zip(tokens_a, tokens_b):
        if _token_less(token_a, token_b):
            return -1
    if len(tokens_a) < len(tokens_b):
        return -1
    return 0


def sort_paths(paths: CottList[str]) -> CottList[str]:
    items: list[str] = []
    for path in paths:
        items.append(path)
    ordered = sorted(items, key=cmp_to_key(lambda a, b: _compare(a, b)))
    return CottList(values=ordered)
