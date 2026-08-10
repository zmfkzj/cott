from cott_runtime import I64


def spell_cardinal(value: I64) -> str:
    ones: tuple[str, ...] = (
        "zero",
        "one",
        "two",
        "three",
        "four",
        "five",
        "six",
        "seven",
        "eight",
        "nine",
        "ten",
        "eleven",
        "twelve",
        "thirteen",
        "fourteen",
        "fifteen",
        "sixteen",
        "seventeen",
        "eighteen",
        "nineteen",
    )
    tens: tuple[str, ...] = (
        "",
        "",
        "twenty",
        "thirty",
        "forty",
        "fifty",
        "sixty",
        "seventy",
        "eighty",
        "ninety",
    )
    scales: tuple[str, ...] = (
        "",
        "thousand",
        "million",
        "billion",
        "trillion",
        "quadrillion",
        "quintillion",
    )

    def render_group(group: int) -> str:
        words: list[str] = []
        hundreds: int = group // 100
        remainder: int = group % 100
        if hundreds != 0:
            words.append(ones[hundreds])
            words.append("hundred")
            if remainder != 0:
                words.append("and")
        if remainder >= 20:
            words.append(tens[remainder // 10])
            unit: int = remainder % 10
            if unit != 0:
                words.append(ones[unit])
        elif remainder != 0 or not words:
            words.append(ones[remainder])
        return " ".join(words)

    if value == 0:
        return "Zero"

    negative: bool = value < 0
    magnitude: int = -(value + 1) + 1 if negative else value
    groups: list[int] = []
    while magnitude != 0:
        groups.append(magnitude % 1000)
        magnitude //= 1000

    fragments: list[str] = []
    for scale_index in range(len(groups) - 1, -1, -1):
        group: int = groups[scale_index]
        if group == 0:
            continue
        if scale_index == 0 and group < 100 and fragments:
            fragments.append("and")
        fragment: str = render_group(group)
        if scale_index != 0:
            fragment = f"{fragment} {scales[scale_index]}"
        fragments.append(fragment)

    rendered: str = " ".join(fragments)
    result: str = rendered[0].upper() + rendered[1:]
    return f"(negative) {result}" if negative else result
