import re


def is_id_column(name: str) -> bool:
    if re.search(r"(\b|_)id\b", name, re.IGNORECASE) is not None:
        return True
    return re.search(r"[a-z]I[dD]\b", name) is not None
