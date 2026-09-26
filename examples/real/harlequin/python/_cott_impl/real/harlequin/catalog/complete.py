from typing import Final, cast

from cott_runtime import CottList, Nothing, Some, U64
from real.harlequin.catalog_types import Completion, CompletionSet

_QUOTES: Final[str] = "'\"`"
_TAG: Final[str] = "harlequin.completions"


def _fuzzy_span(label: str, text: str) -> tuple[int, int] | None:
    best: tuple[int, int] | None = None
    for start in range(len(label)):
        if label[start] != text[0] or (start > 0 and label[start - 1] != "_"):
            continue
        pos = start + 1
        ok = True
        for ch in text[1:]:
            found = label.find(ch, pos)
            if found < 0:
                ok = False
                break
            pos = found + 1
        if not ok:
            continue
        span = pos - start
        if best is None or span < best[0]:
            best = (span, start)
    return best


def _rank_key(c: Completion) -> tuple[int, str]:
    return (c.priority, c.label.casefold())


def complete(candidates: CompletionSet, identifiers: CottList[str], prefix: str, limit: U64) -> CottList[Completion]:
    if candidates.tag != _TAG:
        return CottList(values=[])
    pool: list[Completion] = list(cast(tuple[Completion, ...], candidates.unwrap()))
    for ident in identifiers:
        pool.append(Completion(label=ident, value=ident, type_label="buf", priority=400, context=Nothing()))
    sep_end = -1
    for i, ch in enumerate(prefix):
        if ch in ".:":
            sep_end = i + 1
    head = ""
    member_mode = sep_end >= 0
    lead_quote = ""
    if member_mode:
        head = prefix[:sep_end]
        sep_start = sep_end - 2 if head.endswith("::") else sep_end - 1
        context = prefix[:sep_start].strip(_QUOTES).casefold()
        raw = prefix[sep_end:]
        if raw and raw[0] in _QUOTES:
            lead_quote = raw[0]
            raw = raw[1:]
        elif raw and raw[0].isdigit():
            return CottList(values=[])
        text = raw.casefold()
        pool = [c for c in pool if isinstance(c.context, Some) and c.context.value == context]
    else:
        if not prefix or prefix[0].isdigit():
            return CottList(values=[])
        text = prefix.casefold()
    typed = prefix.casefold()
    pool = [c for c in pool if not (c.type_label == "buf" and c.label.casefold() == typed)]
    exact: list[Completion] = []
    pref: list[Completion] = []
    rest: list[Completion] = []
    for c in pool:
        lab = c.label.casefold()
        if lab == text:
            exact.append(c)
        elif lab.startswith(text):
            pref.append(c)
        else:
            rest.append(c)
    exact.sort(key=lambda c: _rank_key(c))
    pref.sort(key=lambda c: _rank_key(c))
    ranked: list[Completion] = exact + pref
    if len(ranked) < 20 and len(text) >= 2:
        fuzzy: list[tuple[int, int, int, int, Completion]] = []
        for idx, c in enumerate(rest):
            m = _fuzzy_span(c.label.casefold(), text)
            if m is not None:
                fuzzy.append((m[0], m[1], len(c.label), idx, c))
        fuzzy.sort(key=lambda t: (t[0], t[1], t[2], t[3]))
        ranked.extend(t[4] for t in fuzzy)
    ordered = [c for c in ranked if c.type_label == "buf"] + [c for c in ranked if c.type_label != "buf"]
    seen: set[tuple[str, str]] = set()
    out: list[Completion] = []
    for c in ordered:
        key = (c.label, c.type_label)
        if key in seen:
            continue
        seen.add(key)
        if len(out) >= limit:
            break
        if member_mode:
            full = head + lead_quote + c.label
            out.append(Completion(label=full, value=full, type_label=c.type_label, priority=c.priority, context=c.context))
        else:
            out.append(c)
    return CottList(values=out)
