from collections.abc import MutableMapping
from pathlib import Path
from typing import Final, cast

import tomlkit
from tomlkit.exceptions import TOMLKitError
from tomlkit.items import AoT

from cott_runtime import Err, Ok, Result, Some
from real.harlequin.config_types import ConfigError, ConfigError_Invalid
from real.harlequin.keymap_types import KeyMap

_LOAD_TITLE: Final[str] = "Harlequin could not load the config file."
_CREATE_TITLE: Final[str] = "Harlequin could not create your configuration."


def _invalid(title: str, message: str) -> Result[Path, ConfigError]:
    return Err(error=ConfigError_Invalid(title=title, message=message))


def _load_error(path: Path, error: Exception) -> Result[Path, ConfigError]:
    return _invalid(_LOAD_TITLE, f"Attempted to load the config file at {path}, but encountered an error:\n\n{error}")


def _subtable(parent: MutableMapping[str, object], key: str, super_table: bool) -> MutableMapping[str, object] | None:
    existing: object = parent.get(key)
    if existing is None:
        created = tomlkit.table(is_super_table=super_table)
        parent[key] = created
        return cast(MutableMapping[str, object], created)
    if isinstance(existing, MutableMapping):
        return cast(MutableMapping[str, object], existing)
    return None


def _bindings_aot(keymap: KeyMap) -> AoT:
    bindings = tomlkit.aot()
    for binding in keymap.bindings:
        entry = tomlkit.table()
        entry.add("keys", binding.keys)
        entry.add("action", binding.action)
        display = binding.key_display
        if isinstance(display, Some):
            entry.add("key_display", display.value)
        bindings.append(entry)
    return bindings


def write_keymap(path: Path, keymap: KeyMap) -> Result[Path, ConfigError]:
    text: str | None = None
    try:
        if path.exists():
            text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        return _load_error(path, error)
    except OSError as error:
        return _invalid(_CREATE_TITLE, str(error))
    try:
        document = tomlkit.parse(text) if text is not None else tomlkit.document()
    except TOMLKitError as error:
        return _load_error(path, error)
    root = cast(MutableMapping[str, object], document)
    target: MutableMapping[str, object] = root
    if path.name == "pyproject.toml":
        tool = _subtable(root, "tool", True)
        if tool is None:
            return _invalid(_CREATE_TITLE, f"Expected `table` at tool in {path}.")
        harlequin = _subtable(tool, "harlequin", False)
        if harlequin is None:
            return _invalid(_CREATE_TITLE, f"Expected `table` at tool.harlequin in {path}.")
        target = harlequin
    keymaps = _subtable(target, "keymaps", True)
    if keymaps is None:
        return _invalid(_CREATE_TITLE, f"Expected `table` at keymaps in {path}.")
    if keymap.name in keymaps:
        del keymaps[keymap.name]
    keymaps[keymap.name] = _bindings_aot(keymap)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(tomlkit.dumps(document).encode("utf-8"))
    except OSError as error:
        return _invalid(_CREATE_TITLE, str(error))
    return Ok(value=path)
