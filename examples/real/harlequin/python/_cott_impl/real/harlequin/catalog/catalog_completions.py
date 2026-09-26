from cott_runtime import CottList, Nothing, Option, Some

from real.harlequin.catalog_types import CatalogEntry, CatalogKind_Column, CatalogKind_Database, CatalogKind_Schema, CatalogKind_Table, CatalogKind_TemporaryTable, CatalogKind_View, Completion


def catalog_completions(catalog: CottList[CatalogEntry]) -> CottList[Completion]:
    labels: dict[str, str] = {}
    for entry in catalog:
        labels[entry.id] = entry.label
    out: list[Completion] = []
    for entry in catalog:
        kind = entry.kind
        if not isinstance(kind, (CatalogKind_Database, CatalogKind_Schema, CatalogKind_Table, CatalogKind_View, CatalogKind_TemporaryTable, CatalogKind_Column)):
            continue
        context: Option[str] = Nothing()
        parent = entry.parent
        if isinstance(parent, Some):
            parent_label = labels.get(parent.value)
            if parent_label is not None:
                context = Some(value=parent_label.casefold())
        out.append(Completion(label=entry.label, value=entry.label, type_label=entry.type_label, priority=500 + entry.depth, context=context))
    return CottList(values=out)
