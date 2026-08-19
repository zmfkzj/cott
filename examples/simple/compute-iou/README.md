# compute-iou

## Purpose
Calculate the intersection-over-union (IoU) of two inclusive-pixel bounding boxes.

## Key points
- It separates `Box` coordinates from `IntersectionUnion` areas to make the boundary between integer area calculation and F64 ratio calculation explicit.
- Width and height are `max - min + 1`; non-overlapping boxes clamp intersection dimensions to 0, so IoU is 0.0.
- The Python implementation validates the ground-truth box, predicted box, area overflow, and zero union in order, then confirms that a successful IoU is finite.
