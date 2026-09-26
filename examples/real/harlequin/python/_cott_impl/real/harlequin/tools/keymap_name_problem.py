from cott_runtime import CottList, Nothing, Some


def keymap_name_problem(name: str, builtin_names: CottList[str]) -> Some[str] | Nothing:
    for candidate in builtin_names:
        if name == candidate:
            return Some(value="Cannot use the name of an existing keymap plug-in")
    if not name.strip():
        return Some(value="Cannot be empty")
    return Nothing()
