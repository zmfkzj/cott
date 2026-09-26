from cott_runtime import CottList, Option, Some

from real.harlequin.adapters_types import AdapterDescriptor, AdapterOption, OptionKind_Choice, OptionKind_FilePath, OptionKind_Flag


def _hsql_rows() -> list[tuple[str, str]]:
    return [
        ("-a, --adapter NAME", "The database adapter to use.  [default: duckdb]"),
        ("-c, --command TEXT", "Run this SQL. Repeatable; sources run in order."),
        ("-f, --file PATH", "Run SQL from this file (\"-\" reads standard input). Repeatable."),
        ("-o, --output PATH", "Write results to this file instead of standard output."),
        ("--format NAME", "Output format: table, markdown, md, vertical, csv, tsv, json, jsonl, ndjson, parquet, orc, feather, arrow, none.  [default: table]"),
        ("--csv", "Shorthand for --format csv."),
        ("--json", "Shorthand for --format json."),
        ("--jsonl", "Shorthand for --format jsonl."),
        ("--markdown", "Shorthand for --format markdown."),
        ("-x, --vertical", "Shorthand for --format vertical."),
        ("-t, --tuples-only", "Print rows only, without header or footer."),
        ("-A, --no-align", "Do not pad table columns."),
        ("--no-header", "Omit the header row."),
        ("--no-footer", "Omit the row-count footer."),
        ("--null-string TEXT", "Text printed for NULL values."),
        ("-P, --profile NAME", "Use this config profile."),
        ("--config-path PATH", "Read config from this file."),
        ("-r, --read-only", "Open the connection read-only."),
        ("--timeout SECONDS", "Cancel a query after this many seconds."),
        ("--ssh-host TEXT", "Connect through this SSH host."),
        ("--ssh-forward TEXT", "An SSH port forward. Repeatable."),
        ("--ssh-batch-mode", "Never prompt for SSH credentials."),
        ("--ssh-allow-reuse", "Reuse an existing SSH connection."),
        ("--ssh-timeout SECONDS", "SSH connection timeout in seconds."),
        ("--catalog", "Print the database catalog and exit."),
        ("--catalog-search TERM", "Search the catalog for TERM and exit."),
        ("--path TEXT", "Restrict --catalog or --catalog-search to this path."),
        ("--history", "Print the query history and exit."),
        ("--history-search TERM", "Search the query history for TERM and exit."),
        ("--config MODE", "Config mode: show, list-profiles, validate, schema, init."),
        ("--spec", "Print the machine-readable CLI spec and exit."),
        ("--info", "Print adapter and environment information and exit."),
        ("--skill", "Print the agent skill document and exit."),
        ("--limit N", "Maximum rows fetched per result; -1 for unlimited.  [default: 500]"),
        ("--display-rows N", "Maximum rows displayed per result; -1 for unlimited."),
        ("--result all|last|N", "Which results to print.  [default: all]"),
        ("--on-error stop|continue", "What to do when a statement fails.  [default: stop]"),
        ("--no-write-history", "Do not record queries in the history."),
        ("--stats", "Print timing statistics."),
        ("--color auto|always|never", "When to color output.  [default: never]"),
        ("--serve NAME", "Serve a persistent session with this name."),
        ("--session NAME", "Send this request to the named session."),
        ("--session-reset", "Reset the named session and exit."),
        ("--session-status", "Print the named session's status and exit."),
        ("--queue-timeout SECONDS", "Maximum seconds to wait for a busy session."),
        ("--idle-timeout SECONDS", "Stop a served session after this many idle seconds.  [default: 1800]"),
        ("--max-lifetime SECONDS", "Stop a served session after this many seconds.  [default: 28800]"),
        ("--version", "Show the version and exit."),
        ("--help", "Show this message and exit."),
    ]


def _spellings(rows: list[tuple[str, str]]) -> set[str]:
    taken: set[str] = set()
    for term, _help in rows:
        for part in term.split(", "):
            taken.add(part.split(" ", 1)[0])
    return taken


def _format_rows(rows: list[tuple[str, str]]) -> list[str]:
    width = min(max((len(r[0]) for r in rows), default=0), 30)
    lines: list[str] = []
    for term, help_text in rows:
        if not help_text:
            lines.append(f"  {term}")
        elif len(term) <= width:
            lines.append(f"  {term.ljust(width)}  {help_text}")
        else:
            lines.append(f"  {term}")
            lines.append(f"  {' ' * width}  {help_text}")
    return lines


def _adapter_row(option: AdapterOption, taken: set[str]) -> tuple[str, str] | None:
    decls = [str(d) for d in option.short_decls if str(d).startswith("-")]
    spelled = [s for s in sorted(decls, key=len) + [f"--{option.name}"] if s not in taken]
    if not spelled:
        return None
    kind = option.kind
    if isinstance(kind, OptionKind_Flag):
        metavar = ""
    elif isinstance(kind, OptionKind_Choice):
        metavar = " [" + "|".join(str(c) for c in kind.choices) + "]"
    elif isinstance(kind, OptionKind_FilePath):
        metavar = " PATH"
    else:
        metavar = " TEXT"
    help_text = option.description
    default = option.default
    if isinstance(default, Some):
        help_text = f"{help_text}  [default: {default.value}]"
    return (", ".join(spelled) + metavar, help_text)


def hsql_help(descriptors: CottList[AdapterDescriptor], selected: Option[AdapterDescriptor], options: CottList[AdapterOption]) -> str:
    names = ", ".join(d.name for d in descriptors)
    lines = [
        "Usage: hsql [OPTIONS] [CONN_STR]...",
        "",
        "  Run SQL against a database and exit. hsql is Harlequin's headless CLI.",
        "",
        f"  Installed adapters: {names}",
        "",
        "Options:",
    ]
    rows = _hsql_rows()
    lines.extend(_format_rows(rows))
    if isinstance(selected, Some):
        descriptor: AdapterDescriptor = selected.value
        taken = _spellings(rows)
        adapter_rows: list[tuple[str, str]] = []
        for option in options:
            row = _adapter_row(option, taken)
            if row is not None:
                adapter_rows.append(row)
        lines.append("")
        lines.append(f"{descriptor.display_name} Adapter Options:")
        lines.extend(_format_rows(adapter_rows))
    return "\n".join(lines) + "\n"
