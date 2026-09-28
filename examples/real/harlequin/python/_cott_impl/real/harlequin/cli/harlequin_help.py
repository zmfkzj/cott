import textwrap
from typing import Final

from cott_runtime import CottList, Some
from real.harlequin.adapters import adapter_options
from real.harlequin.adapters_types import AdapterDescriptor, AdapterOption, OptionKind_Choice, OptionKind_FilePath, OptionKind_Flag

_WIDTH: Final[int] = 79
_COL_MAX: Final[int] = 30
_COL_SPACING: Final[int] = 2
_INDENT: Final[int] = 2
_DESCRIPTION: Final[str] = "The Harlequin IDE: a SQL IDE for your terminal. CONN_STR is zero or more connection strings or database file paths for the selected adapter."


def _core_rows() -> list[tuple[str, str]]:
    return [
        ("-P, --profile TEXT", "The name of a profile in the config file to use. Defaults to the config's default profile."),
        ("--config-path PATH", "The path to a Harlequin config file. Defaults to searching the standard config locations."),
        ("-t, --theme TEXT", "The name of a color theme to use. Defaults to the configured theme."),
        ("--viewer-max-rows INTEGER", "The maximum number of rows to load into the Results Viewer. Defaults to the configured value.  [x>=-1]"),
        ("--limit INTEGER", "The row limit applied by the Limit checkbox. Defaults to the configured value.  [x>=-1]"),
        ("-o, --output PATH", "Write results to this file. Defaults to none."),
        ("-a, --adapter NAME", "The database adapter to use. Defaults to the configured adapter."),
        ("--no-write-history", "Do not write query history to disk. Defaults to off."),
        ("-r, --read-only", "Open the database in read-only mode. Defaults to off."),
        ("-f, --show-files DIRECTORY", "Show this directory in the Data Catalog. Defaults to none."),
        ("--show-s3, --s3 TEXT", "Show S3 objects in the Data Catalog. Defaults to none."),
        ("--keymap-name TEXT", "The name of a keymap to load; may be repeated. Defaults to the configured keymaps."),
        ("--ssh-host TEXT", "Connect through this SSH host. Defaults to none."),
        ("--ssh-forward TEXT", "An SSH port forward; may be repeated. Defaults to none."),
        ("--ssh-batch-mode", "Never prompt during SSH connection. Defaults to off."),
        ("--ssh-allow-reuse", "Reuse an existing SSH connection. Defaults to off."),
        ("--ssh-timeout FLOAT", "Seconds to wait for the SSH connection. Defaults to the configured value.  [x>0]"),
        ("--locale TEXT", "The locale used to format numbers and dates. Defaults to the system locale."),
        ("--no-download-tzdata", "Do not download timezone data. Defaults to off."),
        ("--config", "Run the configuration wizard and exit. Defaults to off."),
        ("--keys", "Run the keymap editor and exit. Defaults to off."),
        ("--version", "Show the version and exit. Defaults to off."),
        ("--help", "Show this message and exit. Defaults to off."),
    ]


def _write_dl(rows: list[tuple[str, str]]) -> list[str]:
    first_col = min(max((len(decl) for decl, _ in rows), default=0), _COL_MAX) + _COL_SPACING
    text_width = _WIDTH - _INDENT - first_col
    help_indent = " " * (_INDENT + first_col)
    out: list[str] = []
    for decl, description in rows:
        if not description:
            out.extend(textwrap.wrap(decl, _WIDTH, initial_indent=" " * _INDENT, subsequent_indent=" " * (_INDENT + 2), break_on_hyphens=False))
            continue
        help_lines = textwrap.wrap(description, text_width, break_on_hyphens=False)
        if len(decl) <= first_col - _COL_SPACING:
            out.append(" " * _INDENT + decl + " " * (first_col - len(decl)) + help_lines[0])
        else:
            out.extend(textwrap.wrap(decl, _WIDTH, initial_indent=" " * _INDENT, subsequent_indent=" " * (_INDENT + 2), break_on_hyphens=False))
            out.append(help_indent + help_lines[0])
        for line in help_lines[1:]:
            out.append(help_indent + line)
    return out


def _option_row(option: AdapterOption) -> tuple[str, str]:
    shorts = [decl for decl in option.short_decls]
    decls = [decl for decl in shorts if not decl.startswith("--")]
    decls.append("--" + option.name)
    decls.extend(decl for decl in shorts if decl.startswith("--"))
    kind = option.kind
    if isinstance(kind, OptionKind_Flag):
        metavar = ""
    elif isinstance(kind, OptionKind_Choice):
        metavar = " [" + "|".join(kind.choices) + "]"
    elif isinstance(kind, OptionKind_FilePath):
        metavar = " PATH"
    else:
        metavar = " TEXT"
    description = option.description
    if option.secret:
        description += " (secret)"
    default = option.default
    if isinstance(default, Some):
        description += "  [default: " + default.value + "]"
    return ", ".join(decls) + metavar, description


def harlequin_help(descriptors: CottList[AdapterDescriptor]) -> str:
    lines = ["Usage: harlequin [OPTIONS] [CONN_STR]...", ""]
    lines.extend(textwrap.wrap(_DESCRIPTION, _WIDTH, initial_indent="  ", subsequent_indent="  "))
    lines.extend(["", "Options:"])
    lines.extend(_write_dl(_core_rows()))
    for descriptor in descriptors:
        lines.extend(["", descriptor.display_name + " Adapter Options:"])
        lines.extend(_write_dl([_option_row(option) for option in adapter_options(descriptor.kind)]))
    return "\n".join(lines) + "\n"
