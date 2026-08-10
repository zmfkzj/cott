from cott_runtime import CottList, U8
from curriculum.color_quantization_types import Rgb


def rank_palette_colors(pixels: CottList[Rgb], max_colors: U8) -> CottList[Rgb]:
    if max_colors == 0:
        return CottList(values=())

    counts: dict[tuple[int, int, int], int] = {}
    for pixel in pixels:
        key: tuple[int, int, int] = (pixel.red, pixel.green, pixel.blue)
        counts[key] = counts.get(key, 0) + 1

    colors: list[Rgb] = []
    for (red, green, blue), _count in sorted(
        counts.items(), key=lambda entry: (-entry[1], entry[0][0], entry[0][1], entry[0][2])
    ):
        if len(colors) == max_colors:
            break
        colors.append(Rgb(red=red, green=green, blue=blue))

    return CottList(values=colors)
