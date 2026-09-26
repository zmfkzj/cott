from cott_runtime import CottList
from real.harlequin.ide_types import InputModal, InputOutcome_Cancel, InputOutcome_Complete, InputOutcome_Stay, InputOutcome_Submit, InputPurpose_GoToLine, InputPurpose_OpenFile, InputPurpose_SaveFile, InputStep


def _edited(modal: InputModal, value: str, cursor: int) -> InputStep:
    return InputStep(modal=InputModal(purpose=modal.purpose, title=modal.title, placeholder=modal.placeholder, value=value, cursor=cursor, message="", completions=CottList(values=[])), outcome=InputOutcome_Stay())


def _with_message(modal: InputModal, message: str) -> InputStep:
    return InputStep(modal=InputModal(purpose=modal.purpose, title=modal.title, placeholder=modal.placeholder, value=modal.value, cursor=modal.cursor, message=message, completions=modal.completions), outcome=InputOutcome_Stay())


def input_key(modal: InputModal, key: str, text: str) -> InputStep:
    value = modal.value
    cursor = min(modal.cursor, len(value))
    if key == "escape":
        return InputStep(modal=modal, outcome=InputOutcome_Cancel())
    if key == "tab":
        if isinstance(modal.purpose, (InputPurpose_OpenFile, InputPurpose_SaveFile)):
            return InputStep(modal=modal, outcome=InputOutcome_Complete(value=value))
        return InputStep(modal=modal, outcome=InputOutcome_Stay())
    if key == "enter":
        if value == "":
            return _with_message(modal, "Please enter a value.")
        if isinstance(modal.purpose, InputPurpose_GoToLine) and not (value.isascii() and value.isdigit() and int(value) >= 1):
            return _with_message(modal, "Please enter a line number.")
        return InputStep(modal=modal, outcome=InputOutcome_Submit(value=value))
    if key == "backspace":
        if cursor > 0:
            return _edited(modal, value[: cursor - 1] + value[cursor:], cursor - 1)
        return _edited(modal, value, cursor)
    if key == "delete":
        return _edited(modal, value[:cursor] + value[cursor + 1 :], cursor)
    if key == "left":
        return _edited(modal, value, max(cursor - 1, 0))
    if key == "right":
        return _edited(modal, value, min(cursor + 1, len(value)))
    if key == "home":
        return _edited(modal, value, 0)
    if key == "end":
        return _edited(modal, value, len(value))
    if text != "" and text.isprintable():
        return _edited(modal, value[:cursor] + text + value[cursor:], cursor + len(text))
    return InputStep(modal=modal, outcome=InputOutcome_Stay())
