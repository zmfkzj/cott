from cott_runtime import Err, Ok, Result
from curriculum.color_quantization import rank_palette_colors
from curriculum.color_quantization_types import ColorQuantizationError, ColorQuantizationError_EmptyPixels, ColorQuantizationError_ZeroMaxColors, Palette, QuantizeRequest


def quantize_colors(request: QuantizeRequest) -> Result[Palette, ColorQuantizationError]:
    if len(request.pixels) == 0:
        return Err(error=ColorQuantizationError_EmptyPixels())
    if request.max_colors == 0:
        return Err(error=ColorQuantizationError_ZeroMaxColors())
    return Ok(value=Palette(colors=rank_palette_colors(request.pixels, request.max_colors)))
