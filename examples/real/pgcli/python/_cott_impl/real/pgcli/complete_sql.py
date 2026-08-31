from real.pgcli import complete_catalog_sql
from real.pgcli_types import CompletionPolicy, CompletionRequest, CompletionResult


def complete_sql(request: CompletionRequest) -> CompletionResult:
    return complete_catalog_sql(request, CompletionPolicy(max_candidates=100, include_keywords=True))
