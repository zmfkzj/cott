from typing import Any, Literal, cast

from cott_runtime import I64, Opaque

from real.pgcli.session_types import SpecialState


def _flag(value: object) -> bool:
    return bool(value)


def _pager(value: object) -> I64:
    if isinstance(value, int):
        return int(value)
    raise TypeError("PGSpecial.pager_config is not an integer")


def special_display_state(special: Opaque[Literal["pgcli.pgspecial"]]) -> SpecialState:
    obj: Any = special.unwrap()
    return SpecialState(
        expanded_output=_flag(cast(object, obj.expanded_output)),
        auto_expand=_flag(cast(object, obj.auto_expand)),
        timing_enabled=_flag(cast(object, obj.timing_enabled)),
        pager_config=_pager(cast(object, obj.pager_config)),
    )
