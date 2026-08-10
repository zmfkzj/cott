from cott_runtime import Err, Ok, Result
from curriculum.case_ranking import order_matching_cases
from curriculum.case_ranking_types import CaseRanking, CaseRankingError, CaseRankingError_BlankCaseId, CaseRankingError_BlankTerm, CaseRankingError_DuplicateCaseId, CaseRankingError_EmptyQuery, CaseRankingRequest


def rank_cases(request: CaseRankingRequest) -> Result[CaseRanking, CaseRankingError]:
    if len(request.query_terms) == 0:
        return Err(error=CaseRankingError_EmptyQuery())

    for term in request.query_terms:
        if term.strip() == "":
            return Err(error=CaseRankingError_BlankTerm())

    seen: set[str] = set()
    for case in request.cases:
        if case.case_id.strip() == "":
            return Err(error=CaseRankingError_BlankCaseId())
        if case.case_id in seen:
            return Err(error=CaseRankingError_DuplicateCaseId())
        seen.add(case.case_id)

        for term in case.terms:
            if term.strip() == "":
                return Err(error=CaseRankingError_BlankTerm())

    return Ok(value=order_matching_cases(request.query_terms, request.cases))
