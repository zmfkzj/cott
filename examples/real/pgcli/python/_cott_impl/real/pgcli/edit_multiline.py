from real.pgcli_types import InputBuffer


def edit_multiline(buffer: InputBuffer, input: str) -> InputBuffer:
    text = buffer.text
    position = min(buffer.cursor, len(text))
    new_text = text[:position] + input + text[position:]
    return InputBuffer(text=new_text, cursor=position + len(input), multiline=buffer.multiline)
