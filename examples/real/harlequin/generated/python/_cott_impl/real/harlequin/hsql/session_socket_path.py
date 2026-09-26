from pathlib import Path

from cott_runtime import I64, FrozenMap


def session_socket_path(name: str, environment: FrozenMap[str, str], uid: I64) -> Path:
    runtime_dir = environment.get("XDG_RUNTIME_DIR", "")
    if runtime_dir != "":
        return Path(runtime_dir) / "hsql" / f"{name}.sock"
    tmp_dir = environment.get("TMPDIR", "")
    base = tmp_dir if tmp_dir != "" else "/tmp"
    return Path(base) / f"hsql-{uid}" / f"{name}.sock"
