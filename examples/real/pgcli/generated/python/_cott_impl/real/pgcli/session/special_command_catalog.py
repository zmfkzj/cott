from typing import Any, Literal, cast

from cott_runtime import CottList, Opaque

from real.pgcli.session_types import SpecialCommandEntry


def special_command_catalog(special: Opaque[Literal["pgcli.pgspecial"]]) -> CottList[SpecialCommandEntry]:
    registry: Any = cast(Any, special.unwrap())
    commands_obj = cast(object, registry.commands)
    entries: list[SpecialCommandEntry] = []
    if not isinstance(commands_obj, dict):
        return CottList(values=entries)
    commands = cast(dict[object, object], commands_obj)
    for key, value in commands.items():
        record: Any = value
        syntax = cast(object, record.syntax)
        description = cast(object, record.description)
        entries.append(
            SpecialCommandEntry(
                command=str(key),
                syntax=syntax if isinstance(syntax, str) else str(syntax),
                description=description if isinstance(description, str) else str(description),
            )
        )
    return CottList(values=entries)
