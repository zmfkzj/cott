from math import isfinite

from cott_runtime import CottList, Err, Ok, Result
from curriculum.experiment_ranking_types import ExperimentRankingError, ExperimentRankingError_BlankRunId, ExperimentRankingError_DuplicateRunId, ExperimentRankingError_EmptyRuns, ExperimentRankingError_NonFiniteScore, RunMetric


def order_run_ids(runs: CottList[RunMetric], higher_is_better: bool) -> Result[CottList[str], ExperimentRankingError]:
    if len(runs) == 0:
        return Err(error=ExperimentRankingError_EmptyRuns())

    seen: set[str] = set()
    for run in runs:
        if run.run_id.strip() == "":
            return Err(error=ExperimentRankingError_BlankRunId())
        if not isfinite(run.score):
            return Err(error=ExperimentRankingError_NonFiniteScore())
        if run.run_id in seen:
            return Err(error=ExperimentRankingError_DuplicateRunId())
        seen.add(run.run_id)

    if higher_is_better:
        ordered_ids: list[str] = [run.run_id for run in sorted(runs, key=lambda run: (-run.score, run.run_id))]
    else:
        ordered_ids = [run.run_id for run in sorted(runs, key=lambda run: (run.score, run.run_id))]
    return Ok(value=CottList(values=ordered_ids))
