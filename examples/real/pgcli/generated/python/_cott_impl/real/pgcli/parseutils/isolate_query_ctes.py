from cott_runtime import CottList, Nothing, Option, Some
from real.pgcli.parseutils import extract_ctes
from real.pgcli.parseutils_types import CteTable, IsolatedQuery


def isolate_query_ctes(full_text: str, text_before_cursor: str) -> Option[IsolatedQuery]:
    if not full_text or not full_text.strip():
        return Some(value=IsolatedQuery(full_text=full_text, text_before_cursor=text_before_cursor, local_tables=CottList(values=[])))

    result = extract_ctes(full_text)
    if not isinstance(result, Some):
        return Nothing()

    current = len(text_before_cursor)
    tables: list[CteTable] = []
    last_stop = 0
    for cte in result.value.ctes:
        if cte.start < current < cte.stop:
            return Some(value=IsolatedQuery(
                full_text=full_text[cte.start:cte.stop],
                text_before_cursor=full_text[cte.start:current],
                local_tables=CottList(values=tables),
            ))
        tables.append(CteTable(name=cte.name, columns=cte.columns))
        last_stop = cte.stop

    if not tables:
        return Some(value=IsolatedQuery(full_text=full_text, text_before_cursor=text_before_cursor, local_tables=CottList(values=[])))
    return Some(value=IsolatedQuery(
        full_text=full_text[last_stop:],
        text_before_cursor=text_before_cursor[last_stop:current],
        local_tables=CottList(values=tables),
    ))
