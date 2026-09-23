from cott_runtime import CottList
from real.pgcli_types import CompletionRequest, CompletionResult


def complete_sql(request: CompletionRequest) -> CompletionResult:
    return CompletionResult(candidates=CottList(values=[]), replace_start=request.cursor)
