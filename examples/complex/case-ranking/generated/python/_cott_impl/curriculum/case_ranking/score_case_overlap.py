from cott_runtime import CottSet, U64
from curriculum.case_ranking_types import CaseRecord


def score_case_overlap(query_terms: CottSet[str], case: CaseRecord) -> U64:
    score: int = 0
    for term in case.terms:
        if term in query_terms:
            score += 1
    return score
