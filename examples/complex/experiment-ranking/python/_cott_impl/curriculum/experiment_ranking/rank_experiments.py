from cott_runtime import Err, Ok, Result
from curriculum.experiment_ranking import order_run_ids
from curriculum.experiment_ranking_types import ExperimentRankingError, Ranking, RankingRequest


def rank_experiments(request: RankingRequest) -> Result[Ranking, ExperimentRankingError]:
    ordered_ids_result = order_run_ids(request.runs, request.higher_is_better)
    if isinstance(ordered_ids_result, Err):
        return Err(error=ordered_ids_result.error)

    ordered_ids = ordered_ids_result.value
    return Ok(value=Ranking(ordered_run_ids=ordered_ids, best_run_id=ordered_ids[0]))
