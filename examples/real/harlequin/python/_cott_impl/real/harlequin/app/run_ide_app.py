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


def run_ide_app(session: IdeSession) -> I64:
    state: dict[str, object] = {}
    try:
        handle = session.handle
        if handle.tag != _TAG:
            raise TypeError(_MALFORMED)
        raw = handle.unwrap()
        if not isinstance(raw, dict):
            raise TypeError(_MALFORMED)
        state = cast(dict[str, object], raw)
        app_raw = state.get("app")
        if not isinstance(app_raw, Application):
            raise TypeError("The IDE session has no prompt_toolkit Application.")
        app = cast(Application[object], app_raw)
        result = app.run()
        if not isinstance(result, int) or isinstance(result, bool):
            raise TypeError("The IDE application did not return an exit status.")
        for raw_hook in _hooks(state, "on_exit"):
            try:
                cast(Callable[[], None], raw_hook)()
            except BaseException as error:
                print(str(error), file=sys.stderr)
        return result
    except BaseException as error:
        _restore_terminal()
        for raw_hook in _hooks(state, "on_crash"):
            try:
                cast(Callable[[], None], raw_hook)()
            except BaseException as hook_error:
                print(str(hook_error), file=sys.stderr)
        print(_CRASH, file=sys.stderr)
        print(str(error), file=sys.stderr)
        return 1
    finally:
        _close_tunnel(state)
