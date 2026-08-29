from cott_runtime import CottList, U64


def add_history(history: CottList[str], location: str, history_limit: U64) -> CottList[str]:
    if not location:
        return history

    updated: list[str] = [location]
    for entry in history:
        if entry == location:
            continue
        if len(updated) >= history_limit:
            break
        updated.append(entry)
    return CottList(values=updated)
