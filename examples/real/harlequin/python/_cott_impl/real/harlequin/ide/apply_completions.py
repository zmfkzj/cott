import os

from cott_runtime import CottList
from real.harlequin.ide_types import InputModal


def apply_completions(modal: InputModal, completions: CottList[str]) -> InputModal:
    items: list[str] = [item for item in completions]
    if len(items) == 0:
        return InputModal(purpose=modal.purpose, title=modal.title, placeholder=modal.placeholder, value=modal.value, cursor=modal.cursor, message="No matching files.", completions=CottList(values=[]))
    if len(items) == 1:
        only = items[0]
        return InputModal(purpose=modal.purpose, title=modal.title, placeholder=modal.placeholder, value=only, cursor=len(only), message="", completions=CottList(values=[]))
    prefix = os.path.commonprefix(items)
    value = modal.value
    cursor = modal.cursor
    if len(prefix) > len(value):
        value = prefix
        cursor = len(prefix)
    return InputModal(purpose=modal.purpose, title=modal.title, placeholder=modal.placeholder, value=value, cursor=cursor, message="", completions=CottList(values=items))
