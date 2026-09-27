from pathlib import Path

from cott_runtime import CottContractViolation, CottList, Err, Ok, Result, U64, _cott_fixture_replace
from real.toolong.files import read_lines
from real.toolong.files_types import SaveError, SaveError_WriteFailed
from real.toolong.index import line_location
from real.toolong.model_types import LogSource, TabIndex


def _line_text(sources: CottList[LogSource], index: TabIndex, line: U64) -> str:
    location = line_location(index, line)
    position = 0
    for source in sources:
        if position == location.file:
            for text in read_lines(source, CottList(values=[location.span])):
                return text
            return ""
        position += 1
    return ""


def _failure_message(error: CottContractViolation) -> str:
    cause = error.__cause__
    if isinstance(cause, OSError):
        return str(cause)
    return error.message


def save_lines(sources: CottList[LogSource], index: TabIndex, line_count: U64, path: Path) -> Result[U64, SaveError]:
    lines: list[str] = []
    for line in range(line_count):
        text = _line_text(sources, index, line)
        if text:
            lines.append(text + "\n")
    content = "".join(lines)
    try:
        _cott_fixture_replace(path, content.encode("utf-8"))
    except CottContractViolation as error:
        if error.message != "fixture adapters are inactive":
            return Err(error=SaveError_WriteFailed(message=_failure_message(error)))
        try:
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(content)
        except (OSError, UnicodeError) as host_error:
            return Err(error=SaveError_WriteFailed(message=str(host_error)))
    except (OSError, UnicodeError) as error:
        return Err(error=SaveError_WriteFailed(message=str(error)))
    return Ok(value=len(lines))
