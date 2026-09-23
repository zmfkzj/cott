from cott_runtime import CottList
from real.harlequin.catalog_types import CatalogSnapshot, CompletionRequest, CompletionResult


def complete_sql(request: CompletionRequest, snapshot: CatalogSnapshot) -> CompletionResult:
    return CompletionResult(
        candidates=CottList(values=[]),
        replace_start=request.cursor,
        replace_end=request.cursor,
    )
