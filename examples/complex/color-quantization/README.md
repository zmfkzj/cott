# color-quantization

## Purpose
Build a limited palette using only exact RGB colors that occur most frequently in a pixel set.

## Key points
- Reject empty pixels before a color limit of 0; a successful palette contains at least one color.
- Count occurrences per RGB tuple, sort by descending frequency and then ascending red, green, and blue, and select at most `max_colors` colors.
