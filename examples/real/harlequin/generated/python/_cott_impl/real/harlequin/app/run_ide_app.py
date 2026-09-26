import sys
from collections.abc import Callable
from typing import Final, cast

from cott_runtime import I64, Some
from prompt_toolkit.application import Application

from real.harlequin.app_types import IdeContext, IdeSession
from real.harlequin.support import close_ssh_tunnel

_TAG: Final[str] = "harlequin.ide"
_CRASH: Final[str] = "Harlequin encountered an unexpected error and had to quit."
_MALFORMED: Final[str] = "The IDE session handle is malformed."


def _hooks(state: dict[str, object], key: str) -> list[object]:
    raw = state.get(key)
    if isinstance(raw, list):
        return list(cast(list[object], raw))
    return []


def _restore_terminal() -> None:
    try:
        if sys.stdout.isatty():
            sys.stdout.write("\x1b[?1049l\x1b[?25h\x1b[0m")
            sys.stdout.flush()
    except Exception as error:
        print(str(error), file=sys.stderr)


def _close_tunnel(state: dict[str, object]) -> None:
    context = state.get("context")
    if not isinstance(context, IdeContext):
        return
    tunnel = context.tunnel
    if isinstance(tunnel, Some):
        try:
            close_ssh_tunnel(tunnel.value)
        except Exception as error:
            print(str(error), file=sys.stderr)


def _run(state: dict[str, object]) -> int:
    app_raw = state.get("app")
    if not isinstance(app_raw, Application):
        raise TypeError("The IDE session has no prompt_toolkit Application.")
    app = cast(Application[object], app_raw)
    result = app.run()
    status = 0
    if isinstance(result, int) and not isinstance(result, bool):
        status = result
    for raw_hook in _hooks(state, "on_exit"):
        try:
            cast(Callable[[], None], raw_hook)()
        except Exception as error:
            print(str(error), file=sys.stderr)
    return status


def run_ide_app(session: IdeSession) -> I64:
    handle = session.handle
    if handle.tag != _TAG:
        print(_CRASH, file=sys.stderr)
        print(_MALFORMED, file=sys.stderr)
        return 1
    raw = handle.unwrap()
    if not isinstance(raw, dict):
        print(_CRASH, file=sys.stderr)
        print(_MALFORMED, file=sys.stderr)
        return 1
    state = cast(dict[str, object], raw)
    try:
        status = _run(state)
    except Exception as error:
        _restore_terminal()
        for raw_hook in _hooks(state, "on_crash"):
            try:
                cast(Callable[[], None], raw_hook)()
            except Exception as hook_error:
                print(str(hook_error), file=sys.stderr)
        print(_CRASH, file=sys.stderr)
        print(str(error), file=sys.stderr)
        status = 1
    _close_tunnel(state)
    return status
