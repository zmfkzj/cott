from cott_runtime import CottList
from real.harlequin.ide_types import InputModal, InputPurpose, InputPurpose_Find, InputPurpose_GoToLine, InputPurpose_OpenFile


def input_modal(purpose: InputPurpose, value: str) -> InputModal:
    title: str
    placeholder: str
    if isinstance(purpose, InputPurpose_Find):
        title = "Find"
        placeholder = "Search text"
    elif isinstance(purpose, InputPurpose_GoToLine):
        title = "Go To Line"
        placeholder = "Line number"
    elif isinstance(purpose, InputPurpose_OpenFile):
        title = "Open Query"
        placeholder = "/path/to/file.sql (tab autocompletes, enter opens, esc cancels)"
    else:
        title = "Save Query"
        placeholder = "/path/to/file.sql (tab autocompletes, enter saves, esc cancels)"
    return InputModal(purpose=purpose, title=title, placeholder=placeholder, value=value, cursor=len(value), message="", completions=CottList(values=[]))
