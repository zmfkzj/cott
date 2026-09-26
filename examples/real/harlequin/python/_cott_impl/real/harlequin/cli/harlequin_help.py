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
        ("--version", "Show the version and exit."),
        ("--help", "Show this message and exit."),
    ]


def _write_dl(rows: list[tuple[str, str]]) -> list[str]:
    first_col = min(max((len(first) for first, _ in rows), default=0), _COL_MAX) + _COL_SPACING
    text_width = max(_WIDTH - first_col - _INDENT, 10)
    out: list[str] = []
    for first, second in rows:
        head = " " * _INDENT + first
        if second == "":
            out.append(head)
            continue
        lines = textwrap.wrap(second, text_width) or [""]
        if len(first) <= first_col - _COL_SPACING:
            out.append(head + " " * (first_col - len(first)) + lines[0])
        else:
            out.append(head)
            out.append(" " * (first_col + _INDENT) + lines[0])
        for line in lines[1:]:
            out.append(" " * (first_col + _INDENT) + line)
    return out


def _option_row(option: AdapterOption) -> tuple[str, str]:
    shorts = [str(decl) for decl in option.short_decls]
    decls = [d for d in shorts if not d.startswith("--")] + ["--" + option.name] + [d for d in shorts if d.startswith("--")]
    kind = option.kind
    if isinstance(kind, OptionKind_Flag):
        metavar = ""
    elif isinstance(kind, OptionKind_Choice):
        metavar = " [" + "|".join(str(choice) for choice in kind.choices) + "]"
    elif isinstance(kind, OptionKind_FilePath):
        metavar = " PATH"
    else:
        metavar = " TEXT"
    help_text = option.description
    if option.secret:
        help_text += " (secret)"
    default = option.default
    if isinstance(default, Some):
        help_text += "  [default: " + default.value + "]"
    return (", ".join(decls) + metavar, help_text)


def harlequin_help(descriptors: CottList[AdapterDescriptor]) -> str:
    out: list[str] = ["Usage: harlequin [OPTIONS] [CONN_STR]...", ""]
    out.extend(textwrap.wrap(_DESCRIPTION, _WIDTH, initial_indent="  ", subsequent_indent="  "))
    out.append("")
    out.append("Options:")
    out.extend(_write_dl(_core_rows()))
    for descriptor in descriptors:
        out.append("")
        out.append(descriptor.display_name + " Adapter Options:")
        rows = [_option_row(option) for option in adapter_options(descriptor.kind)]
        if rows:
            out.extend(_write_dl(rows))
    return "\n".join(out) + "\n"
