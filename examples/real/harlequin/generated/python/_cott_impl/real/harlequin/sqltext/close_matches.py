from typing import Final

from cott_runtime import U64, CottList

_CUTOFF: Final[float] = 0.6


def _longest(a: str, b: str, alo: int, ahi: int, blo: int, bhi: int) -> tuple[int, int, int]:
    best_i = alo
    best_j = blo
    best_k = 0
    for i in range(alo, ahi):
        for j in range(blo, bhi):
            k = 0
            while i + k < ahi and j + k < bhi and a[i + k] == b[j + k]:
                k += 1
            if k > best_k:
                best_i, best_j, best_k = i, j, k
    return best_i, best_j, best_k


def _matched(a: str, b: str) -> int:
    total = 0
    stack: list[tuple[int, int, int, int]] = [(0, len(a), 0, len(b))]
    while stack:
        alo, ahi, blo, bhi = stack.pop()
        i, j, k = _longest(a, b, alo, ahi, blo, bhi)
        if k == 0:
            continue
        total += k
        stack.append((alo, i, blo, j))
        stack.append((i + k, ahi, j + k, bhi))
    return total


def _ratio(a: str, b: str) -> float:
    length = len(a) + len(b)
    if length == 0:
        return 1.0
    return 2.0 * _matched(a, b) / length


def close_matches(word: str, candidates: CottList[str], limit: U64) -> CottList[str]:
    scored: list[tuple[float, str]] = []
    for candidate in candidates:
        score = _ratio(word, candidate)
        if score >= _CUTOFF:
            scored.append((score, candidate))
    scored.sort(reverse=True)
    return CottList(values=[candidate for _, candidate in scored[:limit]])
