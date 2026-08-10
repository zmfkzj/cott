from cott_runtime import I64


def spell_under_thousand(value: I64) -> str:
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

    words: list[str] = []
    hundreds: int = value // 100
    remainder: int = value % 100
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
