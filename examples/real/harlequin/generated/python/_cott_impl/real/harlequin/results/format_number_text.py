from real.harlequin.results_types import NumberFormat


def _group_digits(integer: str, number_format: NumberFormat) -> str:
    sizes: list[int] = [int(size) for size in number_format.grouping]
    if not sizes:
        return integer
    groups: list[str] = []
    remaining = integer
    index = 0
    size = sizes[0]
    while remaining:
        if index < len(sizes):
            entry = sizes[index]
            if entry != 0:
                size = entry
            index += 1
        if size >= 127 or size <= 0 or len(remaining) <= size:
            groups.append(remaining)
            break
        groups.append(remaining[-size:])
        remaining = remaining[:-size]
    groups.reverse()
    return number_format.thousands_separator.join(groups)


def format_number_text(digits: str, number_format: NumberFormat) -> str:
    sign = ""
    body = digits
    if body.startswith("-"):
        sign = "-"
        body = body[1:]
    end = 0
    while end < len(body) and body[end].isdigit():
        end += 1
    integer = body[:end]
    rest = body[end:]
    if rest.startswith("."):
        rest = number_format.decimal_point + rest[1:]
    return sign + _group_digits(integer, number_format) + rest
