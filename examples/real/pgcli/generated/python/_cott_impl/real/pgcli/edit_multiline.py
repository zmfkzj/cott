from real.pgcli_types import InputBuffer


def edit_multiline(buffer: InputBuffer, input: str) -> InputBuffer:
    cursor = buffer.cursor
    text_length = len(buffer.text)
    if cursor > text_length:
        cursor = text_length
    text = buffer.text[:cursor] + input + buffer.text[cursor:]
    return InputBuffer(text=text, cursor=cursor + len(input), multiline=buffer.multiline)
