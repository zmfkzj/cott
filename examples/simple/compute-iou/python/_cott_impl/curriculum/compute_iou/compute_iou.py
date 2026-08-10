from math import isfinite

from cott_runtime import Err, F64, Ok, Result
from curriculum.compute_iou import calculate_intersection_union
from curriculum.compute_iou_types import Box, IouError, IouError_NonFiniteOutput


def compute_iou(ground_truth: Box, predicted: Box) -> Result[F64, IouError]:
    intersection_union_result = calculate_intersection_union(ground_truth, predicted)
    if isinstance(intersection_union_result, Err):
        return Err(error=intersection_union_result.error)

    intersection_union = intersection_union_result.value
    iou = intersection_union.intersection / intersection_union.union
    if not isfinite(iou):
        return Err(error=IouError_NonFiniteOutput())
    return Ok(value=iou)
