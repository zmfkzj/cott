from cott_runtime import FrozenMap


def generate_table_alias(table_name: str, alias_map: FrozenMap[str, str]) -> str:
    if table_name in alias_map:
        return alias_map[table_name]
    upper = "".join(c for c in table_name if c.isupper())
    if upper:
        return upper
    return "".join(c for i, c in enumerate(table_name) if c != "_" and (i == 0 or table_name[i - 1] == "_"))
