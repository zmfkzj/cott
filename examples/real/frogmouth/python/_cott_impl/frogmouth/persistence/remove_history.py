from cott_runtime import CottList


def remove_history(history: CottList[str], location: str) -> CottList[str]:
    remaining: list[str] = []
    for entry in history:
        if entry != location:
            remaining.append(entry)
    return CottList(values=remaining)
