import re

from cott_runtime import Some
from real.toolong.keys_types import InputEdit, KeyEvent, TextInput


def _last_word_start(text: str) -> int:
    position = 0
    for match in re.finditer("(?<=\\W)\\w", text):
        position = match.start()
    return position


def edit_input(input: TextInput, key: KeyEvent, suggestion: str, integer_only: bool) -> InputEdit:
    value = input.value
    cursor = min(max(int(input.cursor), 0), len(value))
    submitted = False
    bell = False
    name = key.key
    character = key.character
    if isinstance(character, Some) and character.value.isprintable():
        text = character.value
        candidate = value[:cursor] + text + value[cursor:]
        if integer_only and re.fullmatch("[-+]?\\d*", candidate) is None:
            bell = True
        else:
            value = candidate
            cursor += len(text)
    elif name == "left":
        cursor = max(cursor - 1, 0)
    elif name == "right":
        if cursor == len(value) and suggestion != "":
            value = suggestion
            cursor = len(value)
        else:
            cursor = min(cursor + 1, len(value))
    elif name == "ctrl+left":
        cursor = _last_word_start(value[:cursor])
    elif name == "ctrl+right":
        hit = re.search("(?<=\\W)\\w", value[cursor:])
        if hit is None:
            cursor = len(value)
        else:
            cursor += hit.start()
    elif name in ("home", "ctrl+a"):
        cursor = 0
    elif name in ("end", "ctrl+e"):
        cursor = len(value)
    elif name == "backspace":
        if cursor > 0:
            value = value[: cursor - 1] + value[cursor:]
            cursor -= 1
    elif name in ("delete", "ctrl+d"):
        value = value[:cursor] + value[cursor + 1 :]
    elif name == "ctrl+w":
        if cursor > 0:
            start = _last_word_start(value[:cursor])
            value = value[:start] + value[cursor:]
            cursor = start
    elif name == "ctrl+u":
        value = value[cursor:]
        cursor = 0
    elif name == "ctrl+f":
        after = value[cursor:]
        hit = re.search("(?<=\\W)\\w", after)
        if hit is None:
            value = value[:cursor]
        else:
            value = value[:cursor] + after[hit.end() - 1 :]
    elif name == "ctrl+k":
        value = value[:cursor]
    elif name == "enter":
        submitted = True
    else:
        return InputEdit(input=input, handled=False, changed=False, submitted=False, bell=False)
    return InputEdit(
        input=TextInput(value=value, cursor=cursor),
        handled=True,
        changed=value != input.value,
        submitted=submitted,
        bell=bell,
    )
