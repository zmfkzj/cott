from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from real.harlequin.support_types import BufferCache as BufferCache, BufferState as BufferState, CacheError as CacheError, CacheError_Unreadable as CacheError_Unreadable, CacheError_Unwritable as CacheError_Unwritable, ClipboardError as ClipboardError, ClipboardError_Unavailable as ClipboardError_Unavailable, CrashContext as CrashContext, ExternalEdit as ExternalEdit, ExternalEditorError as ExternalEditorError, ExternalEditorError_Failed as ExternalEditorError_Failed, ExternalEditorError_NoEditor as ExternalEditorError_NoEditor, LocaleError as LocaleError, LocaleError_Unavailable as LocaleError_Unavailable, LocaleOutcome as LocaleOutcome, SshError as SshError, SshError_Failed as SshError_Failed, SshError_Invalid as SshError_Invalid, SshTunnel as SshTunnel
from real.harlequin.cli_types import SshSettings
"""Read the buffer cache JSON file at path: {"version": 1, "focus_index": int,
"buffers": [{"text": str, "selection": [anchor, cursor]}, ...]}. A missing
file is Ok(Nothing); a file of another version or shape is Ok(Nothing) (an
old or foreign cache is ignored, as Harlequin ignores unreadable caches); a
file that exists but cannot be read is Unreadable(path, message). Offsets are
clamped to the text length and focus_index to the buffers."""
def load_buffer_cache(path: Path) -> Result[Option[BufferCache], CacheError]: ...

"""Write cache to path in load_buffer_cache's JSON format through a temporary
file in the same directory that is flushed, fsynced and atomically renamed over
path, creating missing parent directories. Failures are Unwritable(path,
message) and leave any previous file unchanged. Name the parent-path local
`parent`, not `dir`: the audit reserves the identifier dir for reflection."""
def save_buffer_cache(path: Path, cache: BufferCache) -> Result[Unit, CacheError]: ...

"""Find buffers a previous session left behind when it ended unexpectedly, the
way Harlequin adopts them: candidates in cache_dir are recovered-*.json files
(newest modification time first), then recovery-*.json files whose
modification time is more than 180 seconds before now_epoch_seconds (newest
first). The first candidate is renamed to "<name>.replayed" before it is read
(so a corrupt file is never replayed twice) and read like load_buffer_cache;
a candidate with no nonblank buffer yields Nothing. No candidate: Ok(Nothing).
Rename or read failures are Unreadable(path, message)."""
def adopt_recovery(cache_dir: Path, now_epoch_seconds: F64) -> Result[Option[BufferCache], CacheError]: ...

"""Delete the file at path; a missing file is not an error. Other failures are
Unwritable(path, message)."""
def remove_file(path: Path) -> Result[Unit, CacheError]: ...

"""The external editor command: the first of VISUAL and EDITOR that is set and
not blank after stripping, split with shlex.split (POSIX rules). Neither set:
NoEditor. A value shlex cannot split (for example an unclosed quote) is
Failed("Harlequin could not run your editor. The editor command {value!r}
could not be parsed: {error}")."""
def resolve_editor(environment: FrozenMap[str, str]) -> Result[CottList[str], ExternalEditorError]: ...

"""Round-trip text through the user's editor while it owns the terminal (the
caller suspends the full-screen application first): write text as UTF-8 to a
new temporary file with suffix ".sql", close it, run command plus the file's
path as the last argument with subprocess.run (inheriting stdin, stdout and
stderr) and wait. A nonzero exit status returns ExternalEdit(Nothing, status).
Otherwise read the file back as UTF-8 with universal newlines and return
ExternalEdit(Some(text), 0). The temporary file is always deleted. Failure to
start the editor or to write or read the file is Failed("Harlequin could not
run your editor. {reason}")."""
def edit_externally(text: str, command: CottList[str]) -> Result[ExternalEdit, ExternalEditorError]: ...

"""The OSC 52 escape sequence that asks the terminal to put text on the system
clipboard: ESC "]52;c;" + base64(UTF-8 text) + BEL ("\\u001b]52;c;...\\u0007")."""
def osc52_sequence(text: str) -> str: ...

"""Put text on the system clipboard with pyperclip.copy. A pyperclip
PyperclipException (no clipboard mechanism) is Unavailable(message)."""
def copy_to_clipboard(text: str) -> Result[Unit, ClipboardError]: ...

"""The system clipboard's text via pyperclip.paste; failures are
Unavailable(message)."""
def paste_from_clipboard() -> Result[str, ClipboardError]: ...

"""Choose the locale for number formatting as Harlequin's --locale does and
report its numeric conventions, using the babel distribution's CLDR data
instead of the process C library (the locale module is unavailable to
implementations). The name is requested, else the first non-empty of the
environment variables LC_ALL, LC_NUMERIC, LANG (os.environ), else "C". A name
that is "C" or "POSIX" or whose part before the first "." is "C" or "POSIX"
means the C conventions: thousands_separator "", decimal_point ".",
grouping empty. Any other name drops its ".encoding" and "@modifier"
suffixes and is parsed with babel.Locale.parse(name, sep="_"); a parse
failure (ValueError or babel.UnknownLocaleError) is Unavailable("unsupported
locale setting: You likely need to install the locale {name} on your OS.")
when requested, while an unparseable environment locale falls back to the
C conventions. A parsed locale gives thousands_separator
babel.numbers.get_group_symbol(locale), decimal_point
babel.numbers.get_decimal_symbol(locale) and grouping [primary, secondary]
from locale.decimal_formats[None].grouping (just [primary] when both are
equal). When nothing was requested and the environment locale is C, use
"en_US": on success the warning is "Harlequin uses the locale of your
device to format numbers. Your device's locale is set to {name}, which is a
POSIX locale for computers, not humans. We assume you are a human and want to
see thousands separators, so we set your locale to en_US.UTF-8. To configure a
different locale or to suppress this warning, set your system locale, or pass
a locale string to Harlequin using the --locale option. To use Harlequin with
the C locale, run Harlequin with the --locale C option. See also
https://harlequin.sh/docs/troubleshooting/locale"; on failure a warning that
thousands separators are unavailable, advising --locale and noting that
--locale C suppresses it, with the same URL."""
def apply_locale(requested: Option[str]) -> Result[LocaleOutcome, LocaleError]: ...

"""The ssh command line for a tunnel: ["ssh", "-N", "-o",
"ExitOnForwardFailure=yes"], then "-o", "BatchMode=yes" when batch_mode,
then "-L", forward for each forward in order, then the host. host and each
forward are passed verbatim but must not be empty, start with "-", or contain
whitespace, control characters or any of ;&|`$<>(){}'"\\\\; otherwise
Invalid("Refusing to pass {value!r} to ssh: it contains characters ssh would
not take as a {host|forward}.")."""
def ssh_command(settings: SshSettings) -> Result[CottList[str], SshError]: ...

"""Start the tunnel Harlequin opens before connecting: resolve the forwards'
local ports with "ssh -G {host}" (plus the -L options), bounded to 10
seconds, taking LocalForward lines; when a local port is already bound,
allow_reuse gives a warning "Port {port} is already in use; connecting through
the listener that has it." and reuses it, otherwise Failed("Harlequin could not
open the SSH tunnel. Local port {port} is already in use. Pass
--ssh-allow-reuse to connect through it."). Start ssh_command(settings) with
subprocess.Popen (stdin inherited so ssh can prompt unless batch_mode, stderr
captured up to 8192 bytes), adding "-o ServerAliveInterval=30 -o
ServerAliveCountMax=3" when the resolved interval is 0. Wait until every local
port accepts a TCP connection (probe every 0.05 s, each connect bounded to 0.5
s) or timeout_seconds pass (1 s when there are no ports). If ssh exits first or
the deadline passes, terminate it (2 s grace, then kill) and return
Failed("Harlequin could not open the SSH tunnel. {ssh stderr or 'Timed out
waiting for the forwards.'}")."""
def open_ssh_tunnel(settings: SshSettings) -> Result[SshTunnel, SshError]: ...

"""Whether the tunnel's ssh process is still running (a reused tunnel owns no
process and is alive while its ports accept connections)."""
def ssh_tunnel_alive(tunnel: SshTunnel) -> bool: ...

"""Stop the tunnel's ssh process: terminate, wait up to 2 seconds, then kill.
Does nothing for a reused tunnel or a process that already exited."""
def close_ssh_tunnel(tunnel: SshTunnel) -> Unit: ...

"""The plain-text crash report Harlequin writes: a header "Harlequin crash report,
{reported_at}" and the paragraph "Review and redact as necessary before
sharing this file. It includes your configuration (with passwords masked)
and, if a buffer was open, the SQL in it.", then sections separated by blank
lines, each a title line followed by its lines: "ENVIRONMENT" (the
environment_lines), "CONTEXT" (one "key: value" line per CrashContext field
except active_sql, keys as the field names), "TRACEBACK" (error_summary then
traceback_text) and, when active_sql is Some, "SQL IN THE ACTIVE BUFFER" with
that SQL passed through real.harlequin.sqltext.redact_sql. Prose lines wrap
at 72 characters."""
def crash_report_text(context: CrashContext, error_summary: str, traceback_text: str, reported_at: str, environment_lines: CottList[str]) -> str: ...

"""Write text to directory/crash-{stamp}-{pid}.log (stamp is the UTC time as
YYYYMMDDTHHMMSSZ), creating directory, then delete the oldest crash-*.log
files so at most 10 remain. Returns the report path; failures are
Unwritable(path, message)."""
def write_crash_report(directory: Path, text: str, stamp: str, pid: I64) -> Result[Path, CacheError]: ...

"""What the terminal shows after a crash instead of a traceback: "Harlequin
encountered an unexpected error and had to quit.\\n\\n{error_summary}\\n\\n",
then when buffers_saved "Your buffers have been saved, and Harlequin will offer
them back the next time you start it.\\n\\n", then "Please report this bug at
https://github.com/tconbeer/harlequin/issues/new?template=crash_report.md",
then, when report_path is Some, " and attach the crash report written to
{path}", then "."."""
def crash_message(error_summary: str, buffers_saved: bool, report_path: Option[Path]) -> str: ...

__all__ = ["BufferCache", "BufferState", "CacheError", "CacheError_Unreadable", "CacheError_Unwritable", "ClipboardError", "ClipboardError_Unavailable", "CrashContext", "ExternalEdit", "ExternalEditorError", "ExternalEditorError_Failed", "ExternalEditorError_NoEditor", "LocaleError", "LocaleError_Unavailable", "LocaleOutcome", "SshError", "SshError_Failed", "SshError_Invalid", "SshTunnel", "adopt_recovery", "apply_locale", "close_ssh_tunnel", "copy_to_clipboard", "crash_message", "crash_report_text", "edit_externally", "load_buffer_cache", "open_ssh_tunnel", "osc52_sequence", "paste_from_clipboard", "remove_file", "resolve_editor", "save_buffer_cache", "ssh_command", "ssh_tunnel_alive", "write_crash_report"]
