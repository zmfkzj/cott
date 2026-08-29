from cott_runtime import CottList, Nothing, Option, Some


def parse_initial_location(arguments: CottList[str]) -> Option[str]:
    if not arguments:
        return Nothing()
    if len(arguments) == 1:
        return Some(value=arguments[0])
    if len(arguments) == 2 and arguments[0] in {"gh", "cb", "codeberg"}:
        return Some(value=f"{arguments[0]} {arguments[1]}")
    return Some(value=f"gh / {' '.join(arguments)}")
