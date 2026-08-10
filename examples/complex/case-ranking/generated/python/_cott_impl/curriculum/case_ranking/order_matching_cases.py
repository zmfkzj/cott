from cott_runtime import CottList, CottSet
from curriculum.case_ranking_types import CaseRanking, CaseRecord


def order_matching_cases(query_terms: CottSet[str], cases: CottList[CaseRecord]) -> CaseRanking:
    matches: list[tuple[int, int, str]] = []
    for case in cases:
        score: int = 0
        for term in case.terms:
            if term in query_terms:
                score += 1
        if score > 0:
            matches.append((-score, -case.cited_by_count, case.case_id))
    matches.sort()
    case_ids: list[str] = [match[2] for match in matches]
    return CaseRanking(case_ids=CottList(values=case_ids))
