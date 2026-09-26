from typing import cast

import pygments.style
import pygments.styles
import pygments.token
import pygments.util
from cott_runtime import CottList, FrozenMap, Nothing, Some

from real.pgcli.cli_types import CliOptions, SetupEnvironment
from real.pgcli.config_types import PgcliConfig
from real.pgcli.output_types import OutputStyle
from real.pgcli.parseutils import parse_destructive_warning
from real.pgcli.session_types import SessionSettings


def _color(config: PgcliConfig, key: str) -> str:
    for entry in config.colors:
        if entry.name == key:
            return entry.value
    return ""


def _base_style(name: str) -> str:
    try:
        style_obj = cast(object, pygments.styles.get_style_by_name(name))
    except pygments.util.ClassNotFound:
        style_obj = cast(object, pygments.styles.get_style_by_name("native"))
    style_cls = cast(type[pygments.style.Style], style_obj)
    styles = cast(dict[object, object], cast(object, style_cls.styles))
    value = styles.get(cast(object, pygments.token.Token), "")
    return value if isinstance(value, str) else ""


def session_settings_from(options: CliOptions, config: PgcliConfig, environment: SetupEnvironment) -> SessionSettings:
    main = config.main
    warn = options.warn
    if isinstance(warn, Some):
        warn_value = warn.value
        if "," in warn_value:
            destructive = CottList(values=warn_value.split(","))
        else:
            destructive = parse_destructive_warning(CottList(values=[warn_value]))
    else:
        destructive = parse_destructive_warning(main.destructive_warning)
    log_option = options.log_file
    log_file: Some[str] | Nothing = Some(value=log_option.value) if isinstance(log_option, Some) else Nothing()
    row_option = options.row_limit
    row_limit = row_option.value if isinstance(row_option, Some) else main.row_limit
    prompt_option = options.prompt
    prompt_format = prompt_option.value if isinstance(prompt_option, Some) else main.prompt
    scripted = any(True for _ in options.commands) or any(True for _ in options.files)
    output_style = OutputStyle(
        base=_base_style(main.syntax_style),
        header=_color(config, "output.header"),
        odd_row=_color(config, "output.odd-row"),
        even_row=_color(config, "output.even-row"),
        null=_color(config, "output.null"),
        table_separator=_color(config, "Token.Output.TableSeparator"),
        true_color="truecolor" in environment.colorterm.lower(),
    )
    return SessionSettings(
        table_format=main.table_format,
        expanded_output=main.expand,
        auto_expand=options.auto_vertical_output or main.auto_expand,
        multi_line=main.multi_line,
        multiline_mode=main.multi_line_mode,
        vi_mode=main.vi,
        explain_mode=False,
        smart_completion=main.smart_completion,
        hide_named_query_text=main.hide_named_query_text,
        verbose_errors=main.verbose_errors,
        output_file=Nothing(),
        log_file=log_file,
        row_limit=row_limit,
        max_field_width=main.max_field_width,
        null_string=main.null_string,
        on_error=main.on_error,
        destructive_warning=destructive,
        destructive_warning_restarts_connection=main.destructive_warning_restarts_connection,
        destructive_statements_require_transaction=main.destructive_statements_require_transaction,
        force_destructive=options.force_destructive,
        auto_retry_closed_connection=main.auto_retry_closed_connection,
        tuples_only=options.tuples_only,
        less_chatty=options.less_chatty or main.less_chatty,
        decimal_format=config.decimal_format,
        float_format=config.float_format,
        column_date_formats=FrozenMap(values={entry.name: entry.value for entry in config.column_date_formats}),
        case_column_headers=main.case_column_headers,
        output_style=Some(value=output_style),
        prompt_format=prompt_format,
        prompt_dsn_format=options.prompt_dsn,
        dsn_alias=Nothing(),
        scripted=scripted,
        completion_refreshing=False,
    )
