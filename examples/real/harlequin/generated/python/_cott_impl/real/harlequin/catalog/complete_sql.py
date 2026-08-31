from cott_runtime import CottList
from real.harlequin.catalog_types import CatalogSnapshot, CompletionRequest, CompletionResult


def complete_sql(request: CompletionRequest, snapshot: CatalogSnapshot) -> CompletionResult:
    cursor = min(request.cursor, len(request.source))
    replace_start = cursor
    while replace_start > 0:
        character = request.source[replace_start - 1]
        if not (character.isalnum() or character == "_" or character == "$"):
            break
        replace_start -= 1

    replace_end = cursor
    while replace_end < len(request.source):
        character = request.source[replace_end]
        if not (character.isalnum() or character == "_" or character == "$"):
            break
        replace_end += 1

    candidates: list[str] = []
    if request.scope == snapshot.scope and request.maximum_candidates > 0:
        prefix = request.source[replace_start:cursor].casefold()
        for relation in snapshot.relations:
            if relation.name.casefold().startswith(prefix):
                candidates.append(relation.name)
                if len(candidates) >= request.maximum_candidates:
                    break

    return CompletionResult(
        candidates=CottList(values=candidates),
        replace_start=replace_start,
        replace_end=replace_end,
    )
