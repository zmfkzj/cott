from __future__ import annotations

from pathlib import Path
from cott_runtime import Ok
from curriculum.system_effects import format_env_variable, inspect_file_path

res = inspect_file_path(Path("/etc/hosts"))
if isinstance(res, Ok):
    print(f"Inspected path: {res.value}")

val = format_env_variable("APP_NAME", "CottApplication")
print(f"Env or fallback: {val}")
