from real.pgcli_types import InputBuffer


def edit_multiline(buffer: InputBuffer, input: str) -> InputBuffer:
    text = buffer.text
    position = buffer.cursor
    return InputBuffer(text=text[:position] + input + text[position:], cursor=position + len(input), multiline=buffer.multiline)
