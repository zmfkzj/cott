from cott_runtime import CottList, Option, Some

from real.harlequin.hsql import spell_catalog_label
from real.harlequin.sqltext import close_matches


def missing_label_message(segment: str, parent: Option[str], siblings: CottList[str]) -> str:
    if isinstance(parent, Some):
        where = f"'{parent.value}'"
    else:
        where = "the top level of the catalog"
    message = f"There is no '{segment}' under {where}."
    names: list[str] = [name for name in siblings]
    suggestions = [spell_catalog_label(name) for name in close_matches(segment, CottList(values=names), 3)]
    if suggestions:
        return f"{message} Did you mean: {', '.join(suggestions[:3])}?"
    if names:
        shown = ", ".join(spell_catalog_label(name) for name in names[:5])
        extra = len(names) - 5
        if extra > 0:
            return f"{message} It contains: {shown}, and {extra} more"
        return f"{message} It contains: {shown}"
    return f"{message} That level is empty."
