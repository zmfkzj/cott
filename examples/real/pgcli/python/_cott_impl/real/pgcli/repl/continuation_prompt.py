from cott_runtime import I64


def continuation_prompt(width: I64, continuation_char: str) -> str:
    return continuation_char * max(width - 1, 0) + " "
