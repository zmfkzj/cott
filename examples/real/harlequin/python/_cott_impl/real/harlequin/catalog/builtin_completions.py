from typing import Final

from cott_runtime import CottList, Nothing

from real.harlequin.catalog_types import Completion

_KEYWORDS: Final[str] = "alter and as between by cascade case column copy create cross current database delete distinct drop end except exclude exists false filter following from full function grant group having if ilike inner insert intersect join lateral left like limit merge natural not offset on or order outer over owner partition preceding qualify range rename replace restrict revoke right row rows schema select sequence set similar table temp temporary then to top true truncate unbounded union update using view when where with"
_FUNCTIONS: Final[str] = "abs ceil concat floor left lower ltrim regexp_extract regexp_replace replace right round rtrim sqrt"
_AGGREGATES: Final[str] = "avg bool_and bool_or count max min sum"


def builtin_completions() -> CottList[Completion]:
    out: list[Completion] = []
    for words, type_label, priority in ((_KEYWORDS, "kw", 100), (_FUNCTIONS, "fn", 200), (_AGGREGATES, "agg", 200)):
        for word in words.split():
            out.append(Completion(label=word, value=word, type_label=type_label, priority=priority, context=Nothing()))
    return CottList(values=out)
