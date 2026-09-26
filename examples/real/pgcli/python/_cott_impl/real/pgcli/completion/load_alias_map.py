import json
import pathlib
from typing import cast

from cott_runtime import Err, FrozenMap, Ok, Result

from real.pgcli.completion_types import AliasMapError, AliasMapError_InvalidMapFile


def _fail(message: str) -> Result[FrozenMap[str, str], AliasMapError]:
    return Err(error=AliasMapError_InvalidMapFile(message=message))


def load_alias_map(path: pathlib.Path) -> Result[FrozenMap[str, str], AliasMapError]:
    prefix = "Cannot read alias_map_file - " + str(path)
    invalid = prefix + " is not valid json"
    try:
        with open(path, encoding="utf-8") as handle:
            data = cast(object, json.load(handle))
    except FileNotFoundError:
        return _fail(prefix + " does not exist")
    except ValueError:
        return _fail(invalid)
    except OSError as error:
        return _fail(prefix + ": " + str(error.strerror))
    if not isinstance(data, dict):
        return _fail(invalid)
    aliases: dict[str, str] = {}
    for key, value in cast(dict[object, object], data).items():
        if not isinstance(key, str) or not isinstance(value, str):
            return _fail(invalid)
        aliases[key] = value
    return Ok(value=FrozenMap(values=aliases))
