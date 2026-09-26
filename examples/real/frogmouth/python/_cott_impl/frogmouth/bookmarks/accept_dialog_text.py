from cott_runtime import Nothing, Option, Some


def accept_dialog_text(value: str) -> Option[str]:
    text = value.strip()
    if not text:
        return Nothing()
    return Some(value=text)
