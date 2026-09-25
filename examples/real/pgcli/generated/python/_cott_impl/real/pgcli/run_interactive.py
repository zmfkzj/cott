import os
import sys
import time
from typing import Final

from cott_runtime import CottList, Err, Ok, Result, Some, UNIT, Unit
from real.pgcli import edit_multiline, load_history, page_output, parse_meta_command, plan_query, refresh_catalog, remember_history, run_meta_command, save_history
from real.pgcli_types import Catalog, CatalogRefreshRequest, ClientError, ClientError_CatalogFailed, ClientError_ConnectionFailed, ClientError_EditorFailed, ClientError_ExportFailed, ClientError_FavoriteFailed, ClientError_HistoryFailed, ClientError_ImportFailed, ClientError_InvalidArguments, ClientError_InvalidCommand, ClientError_InvalidSql, ClientError_NotificationFailed, ClientError_PagerFailed, ClientError_QueryFailed, ClientError_TerminalFailed, ClientError_TransactionFailed, ClientError_TunnelUnsupported, CommandInvocation, CommandResult, HistoryEntry, InputBuffer, InteractiveRequest, MetaCommand_ExecuteBuffer, PagerRequest, SessionMode_Interactive, SessionOptions, SessionReport

_DEFAULT_PAGER: Final[str] = "less -SRXF"
_DEFAULT_HEIGHT: Final[int] = 24
_MAX_HEIGHT: Final[int] = 65535


def _is_command(text: str) -> bool:
    return text.lstrip().startswith("\\") or text.strip() in ("quit", "exit")


def _empty_buffer(multiline: bool) -> InputBuffer:
    return InputBuffer(text="", cursor=0, multiline=multiline)


def _terminal_height() -> int:
    try:
        lines = os.get_terminal_size(sys.stdout.fileno()).lines
    except (OSError, ValueError, AttributeError):
        return _DEFAULT_HEIGHT
    if lines <= 0:
        return _DEFAULT_HEIGHT
    return min(lines, _MAX_HEIGHT)


def _show(output: str, options: SessionOptions) -> Result[Unit, ClientError]:
    if output == "":
        return Ok(value=UNIT)
    pager = os.environ.get("PAGER", "") or _DEFAULT_PAGER
    return page_output(PagerRequest(text=output, pager=pager, enabled=options.pager, terminal_height=_terminal_height()))


def _write(to_stderr: bool, text: str) -> Result[Unit, ClientError]:
    stream = sys.stderr if to_stderr else sys.stdout
    try:
        stream.write(text)
        stream.flush()
    except (OSError, ValueError):
        return Err(error=ClientError_TerminalFailed(message="terminal write failed"))
    return Ok(value=UNIT)


def _category(error: ClientError) -> str:
    if isinstance(error, ClientError_InvalidArguments):
        return "error: invalid arguments\n"
    if isinstance(error, ClientError_InvalidCommand):
        return "error: invalid command\n"
    if isinstance(error, ClientError_InvalidSql):
        return "error: invalid SQL\n"
    if isinstance(error, ClientError_ConnectionFailed):
        return "error: connection failed\n"
    if isinstance(error, ClientError_TunnelUnsupported):
        return "error: SSH tunnel unsupported for this operation\n"
    if isinstance(error, ClientError_CatalogFailed):
        return "error: catalog refresh failed\n"
    if isinstance(error, ClientError_QueryFailed):
        return "error: query failed\n"
    if isinstance(error, ClientError_TransactionFailed):
        return "error: transaction failed\n"
    if isinstance(error, ClientError_ImportFailed):
        return "error: import failed\n"
    if isinstance(error, ClientError_ExportFailed):
        return "error: export failed\n"
    if isinstance(error, ClientError_HistoryFailed):
        return "error: history failed\n"
    if isinstance(error, ClientError_FavoriteFailed):
        return "error: favorite failed\n"
    if isinstance(error, ClientError_EditorFailed):
        return "error: editor failed\n"
    if isinstance(error, ClientError_PagerFailed):
        return "error: pager failed\n"
    if isinstance(error, ClientError_NotificationFailed):
        return "error: notification failed\n"
    if isinstance(error, ClientError_TerminalFailed):
        return "error: terminal failed\n"
    return "error: unsupported format\n"


def _submit(text: str, buffer: InputBuffer, options: SessionOptions, catalog: Catalog, entries: CottList[HistoryEntry]) -> Result[tuple[Result[Unit, ClientError], bool, InputBuffer, SessionOptions, Catalog, CottList[HistoryEntry]], ClientError_HistoryFailed]:
    is_sql = not _is_command(text)
    if is_sql:
        invocation = CommandInvocation(command=MetaCommand_ExecuteBuffer(), buffer=InputBuffer(text=text, cursor=len(text), multiline=options.multiline))
    else:
        invocation = CommandInvocation(command=parse_meta_command(text), buffer=buffer)
    submitted_ms = time.time_ns() // 1_000_000
    ran: Result[CommandResult, ClientError] = run_meta_command(invocation, options, catalog)
    outcome: Result[Unit, ClientError] = Ok(value=UNIT)
    quit_now = False
    new_buffer = _empty_buffer(options.multiline) if is_sql else buffer
    new_options, new_catalog = options, catalog
    if isinstance(ran, Err):
        outcome = Err(error=ran.error)
    else:
        step = ran.value
        new_buffer, new_options, new_catalog, quit_now = step.buffer, step.options, step.catalog, step.quit
        outcome = _show(step.output, new_options)
    history = options.history
    if is_sql and isinstance(history, Some):
        entry = HistoryEntry(sql=text, executed_at_ms=submitted_ms, database=options.connection.settings.database, success=not isinstance(ran, Err))
        entries = remember_history(history.value, entries, entry)
        saved = save_history(history.value, entries)
        if isinstance(saved, Err):
            if isinstance(saved.error, ClientError_HistoryFailed):
                return Err(error=saved.error)
            return Err(error=ClientError_HistoryFailed(path=history.value.path, message="save history failed"))
    return Ok(value=(outcome, quit_now, new_buffer, new_options, new_catalog, entries))


def run_interactive(request: InteractiveRequest) -> Result[SessionReport, ClientError]:
    options = request.options
    entries: CottList[HistoryEntry] = CottList(values=[])
    policy_opt = options.history
    if isinstance(policy_opt, Some):
        loaded = load_history(policy_opt.value)
        if isinstance(loaded, Err):
            return Err(error=loaded.error)
        entries = loaded.value
    interactive = isinstance(request.mode, SessionMode_Interactive)
    catalog = Catalog(databases=CottList(values=[]), schemas=CottList(values=[]), relations=CottList(values=[]), routines=CottList(values=[]), roles=CottList(values=[]), extensions=CottList(values=[]), publications=CottList(values=[]), subscriptions=CottList(values=[]), refreshed_at_ms=0, limit=0)
    if interactive or request.initial_sql.lstrip().startswith("\\"):
        refreshed = refresh_catalog(CatalogRefreshRequest(connection=options.connection, include_system=False, limit=options.catalog_limit))
        if isinstance(refreshed, Err):
            return Err(error=refreshed.error)
        catalog = refreshed.value
    buffer = _empty_buffer(options.multiline)

    if not interactive:
        once = _submit(request.initial_sql, buffer, options, catalog, entries)
        if isinstance(once, Err):
            return Err(error=once.error)
        first = once.value[0]
        if isinstance(first, Err):
            return Err(error=first.error)
        return Ok(value=SessionReport(submissions=1, failures=0))

    submissions = 0
    failures = 0
    pending_text = request.initial_sql
    try:
        tty = sys.stdin.isatty()
    except (OSError, ValueError, AttributeError):
        return Err(error=ClientError_TerminalFailed(message="terminal unavailable"))
    at_end = False
    while True:
        text = ""
        if pending_text != "":
            text, pending_text = pending_text, ""
        elif at_end:
            break
        else:
            if tty:
                prompted = _write(False, "....> " if buffer.text != "" else "pgcli> ")
                if isinstance(prompted, Err):
                    return Err(error=prompted.error)
            try:
                raw = sys.stdin.readline()
            except (OSError, ValueError):
                return Err(error=ClientError_TerminalFailed(message="terminal read failed"))
            if raw == "":
                at_end = True
                if buffer.text.strip() == "":
                    break
                text = buffer.text
                buffer = _empty_buffer(options.multiline)
            else:
                line = raw.removesuffix("\n")
                if _is_command(line):
                    text = line
                else:
                    buffer = edit_multiline(buffer, ("\n" + line) if buffer.text != "" else line)
                    if buffer.text.strip() == "":
                        buffer = _empty_buffer(options.multiline)
                        continue
                    if options.multiline:
                        planned = plan_query(buffer)
                        if not isinstance(planned, Err) and planned.value.requires_terminator:
                            continue
                    text = buffer.text
                    buffer = _empty_buffer(options.multiline)
        submitted = _submit(text, buffer, options, catalog, entries)
        if isinstance(submitted, Err):
            return Err(error=submitted.error)
        outcome, quit_now, buffer, options, catalog, entries = submitted.value
        submissions += 1
        if isinstance(outcome, Err):
            wrote = _write(True, _category(outcome.error))
            if isinstance(wrote, Err):
                return Err(error=wrote.error)
            failures += 1
        if quit_now:
            break
    return Ok(value=SessionReport(submissions=submissions, failures=failures))
