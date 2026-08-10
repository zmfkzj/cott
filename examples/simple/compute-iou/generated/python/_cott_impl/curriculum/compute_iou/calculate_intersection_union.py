from cott_runtime import Err, Ok, Result
from curriculum.compute_iou_types import Box, IntersectionUnion, IouError, IouError_AreaOverflow, IouError_InvalidGroundTruthBox, IouError_InvalidPredictedBox, IouError_ZeroUnion


def calculate_intersection_union(ground_truth: Box, predicted: Box) -> Result[IntersectionUnion, IouError]:
    maximum_i64 = 9_223_372_036_854_775_807

    if ground_truth.xmin > ground_truth.xmax or ground_truth.ymin > ground_truth.ymax:
        return Err(error=IouError_InvalidGroundTruthBox())
    if predicted.xmin > predicted.xmax or predicted.ymin > predicted.ymax:
        return Err(error=IouError_InvalidPredictedBox())

    ground_truth_width = ground_truth.xmax - ground_truth.xmin + 1
    ground_truth_height = ground_truth.ymax - ground_truth.ymin + 1
    if ground_truth_width > maximum_i64 // ground_truth_height:
        return Err(error=IouError_AreaOverflow())
    ground_truth_area = ground_truth_width * ground_truth_height

    predicted_width = predicted.xmax - predicted.xmin + 1
    predicted_height = predicted.ymax - predicted.ymin + 1
    if predicted_width > maximum_i64 // predicted_height:
        return Err(error=IouError_AreaOverflow())
    predicted_area = predicted_width * predicted_height

    overlap_xmin = max(ground_truth.xmin, predicted.xmin)
    overlap_ymin = max(ground_truth.ymin, predicted.ymin)
    overlap_xmax = min(ground_truth.xmax, predicted.xmax)
    overlap_ymax = min(ground_truth.ymax, predicted.ymax)
    overlap_width = max(0, overlap_xmax - overlap_xmin + 1)
    overlap_height = max(0, overlap_ymax - overlap_ymin + 1)
    intersection = overlap_width * overlap_height

    if ground_truth_area > maximum_i64 - predicted_area + intersection:
        return Err(error=IouError_AreaOverflow())
    union = ground_truth_area + predicted_area - intersection
    if union == 0:
        return Err(error=IouError_ZeroUnion())

    return Ok(value=IntersectionUnion(intersection=intersection, union=union))
