from cott_runtime import U64, Option, Some

from real.harlequin.ide_types import RunBar


def new_run_bar(limit: Option[U64]) -> RunBar:
    if isinstance(limit, Some):
        text = str(limit.value)
        return RunBar(limit_enabled=True, limit_text=text, limit_cursor=len(text), running=False)
    return RunBar(limit_enabled=False, limit_text="500", limit_cursor=3, running=False)
