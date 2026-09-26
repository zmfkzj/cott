import json
import re
from collections.abc import Iterable
from typing import Literal, cast

import sqlparse
import sqlparse.engine.grouping
import sqlparse.tokens
from cott_runtime import Opaque
from sqlparse.sql import Token

from real.pgcli.completion_types import PGLITERALS_JSON


def _copy_counts(raw: object) -> dict[str, int]:
    if not isinstance(raw, dict):
        raise TypeError("Invalid prevalence counts")
    counts: dict[str, int] = {}
    for key, value in cast(dict[object, object], raw).items():
        if not isinstance(key, str) or not isinstance(value, int):
            raise TypeError("Invalid prevalence count")
        counts[key] = value
    return counts


def update_prevalence(prevalence: Opaque[Literal["pgcli.prevalence"]], text: str, keywords_only: bool) -> Opaque[Literal["pgcli.prevalence"]]:
    state = prevalence.unwrap()
    if not isinstance(state, dict):
        raise TypeError("Invalid prevalence state")
    entries = cast(dict[object, object], state)
    keyword_counts = _copy_counts(entries["keywords"])
    name_counts = _copy_counts(entries["names"])

    literals = cast(object, json.loads(PGLITERALS_JSON))
    if not isinstance(literals, dict):
        raise TypeError("Invalid keyword literals")
    keywords = cast(dict[object, object], literals)["keywords"]
    if not isinstance(keywords, dict):
        raise TypeError("Invalid keyword tree")
    for keyword in cast(dict[object, object], keywords):
        if not isinstance(keyword, str):
            raise TypeError("Invalid keyword")
        pattern = r"\b" + re.sub(r"\s+", r"\\s+", keyword) + r"\b"
        count = sum(1 for _ in re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE))
        if count:
            keyword_counts[keyword] = keyword_counts.get(keyword, 0) + count

    if not keywords_only:
        sqlparse.engine.grouping.MAX_GROUPING_DEPTH = None
        sqlparse.engine.grouping.MAX_GROUPING_TOKENS = None
        for statement in sqlparse.parse(text):
            tokens = cast(Iterable[Token], statement.flatten())
            for token in tokens:
                if token.ttype in sqlparse.tokens.Name:
                    name = str(cast(object, token.value))
                    name_counts[name] = name_counts.get(name, 0) + 1

    return Opaque(tag="pgcli.prevalence", value={"keywords": keyword_counts, "names": name_counts})
