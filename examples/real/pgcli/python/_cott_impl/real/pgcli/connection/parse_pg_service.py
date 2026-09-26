import re
from typing import Any, cast

import configobj

from cott_runtime import CottList, Err, Nothing, Ok, Option, Result, Some
from real.pgcli.connection_types import ConnectError, ConnectError_Failed, ConnectionParam


def _value_text(value: object) -> str:
    if isinstance(value, list):
        return ",".join(str(item) for item in cast(list[object], value))
    return str(value)


def parse_pg_service(text: str, service: str) -> Result[Option[CottList[ConnectionParam]], ConnectError]:
    lines = text.splitlines()
    first = len(lines)
    for index, line in enumerate(lines):
        if re.match(r"\s*\[", line):
            first = index
            break
    # Blank skipped lines so configobj error line numbers still count them.
    kept = [""] * first + lines[first:]
    try:
        config: Any = configobj.ConfigObj(kept)
    except configobj.ConfigObjError as error:
        return Err(error=ConnectError_Failed(message=str(error)))
    if not bool(cast(object, service in config)):
        return Ok(value=Nothing())
    section: Any = config[service]
    params: list[ConnectionParam] = []
    for key in cast(list[object], list(section.keys())):
        params.append(ConnectionParam(name=str(key), value=_value_text(cast(object, section[key]))))
    return Ok(value=Some(value=CottList(values=params)))
