import base64


def osc52_sequence(text: str) -> str:
    return "\x1b]52;c;" + base64.b64encode(text.encode("utf-8")).decode("ascii") + "\x07"
