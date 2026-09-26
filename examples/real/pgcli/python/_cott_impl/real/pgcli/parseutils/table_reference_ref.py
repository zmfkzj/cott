from cott_runtime import Some

from real.pgcli.parseutils_types import TableReference


def table_reference_ref(table: TableReference) -> str:
    alias = table.alias_name
    if isinstance(alias, Some) and alias.value:
        return alias.value
    name = table.name
    if name.islower() or name.startswith('"'):
        return name
    return '"' + name + '"'
