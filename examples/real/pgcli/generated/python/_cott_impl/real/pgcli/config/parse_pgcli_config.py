from typing import Any, cast

import configobj
from cott_runtime import CottList, Err, I64, Nothing, Ok, Option, Result, Some, U32

from real.pgcli.config_types import CommandEntry, ConfigEntry, ConfigError, ConfigError_Invalid, MainSettings, PGCLI_DEFAULT_CONFIG, PgcliConfig


def _text(value: object) -> str:
    if isinstance(value, list):
        return ", ".join(str(item) for item in cast(list[object], value))
    return str(value)


def _section(cfg: Any, name: str) -> Any:
    if name in cfg:
        return cfg[name]
    return {}


def _scalar_keys(section: Any) -> list[str]:
    if isinstance(section, dict) and not isinstance(section, configobj.Section):
        return []
    return [str(key) for key in cast(list[object], section.scalars)]


def _entries(cfg: Any, name: str) -> CottList[ConfigEntry]:
    section: Any = _section(cfg, name)
    return CottList(values=[ConfigEntry(name=key, value=_text(cast(object, section[key]))) for key in _scalar_keys(section)])


def _commands(cfg: Any, name: str) -> CottList[CommandEntry]:
    section: Any = _section(cfg, name)
    result: list[CommandEntry] = []
    for key in _scalar_keys(section):
        raw = cast(object, section[key])
        if isinstance(raw, list):
            items = [str(item) for item in cast(list[object], raw)]
        elif str(raw) == "":
            items = []
        else:
            items = [str(raw)]
        result.append(CommandEntry(name=key, commands=CottList(values=items)))
    return CottList(values=result)


def _bool(main: Any, key: str, default: bool) -> bool:
    if key not in main:
        return default
    return bool(cast(object, main.as_bool(key)))


def _int(main: Any, key: str) -> int:
    return int(_text(cast(object, main[key])))


def _str(main: Any, key: str, default: str) -> str:
    if key not in main:
        return default
    return _text(cast(object, main[key]))


def _list(main: Any, key: str) -> CottList[str]:
    raw = cast(object, main[key])
    if isinstance(raw, list):
        return CottList(values=[str(item) for item in cast(list[object], raw)])
    return CottList(values=[str(raw)])


def _width(main: Any) -> Option[U32]:
    if "max_field_width" not in main:
        return Some(value=500)
    raw = _text(cast(object, main["max_field_width"]))
    if raw and raw.lower() != "none":
        return Some(value=max(3, abs(int(raw))))
    return Nothing()


def _main(main: Any) -> MainSettings:
    smart_completion = _bool(main, "smart_completion", True)
    auto_suggest = _bool(main, "auto_suggest", True)
    wider_completion_menu = _bool(main, "wider_completion_menu", False)
    always_use_single_connection = _bool(main, "always_use_single_connection", False)
    multi_line = _bool(main, "multi_line", False)
    multi_line_mode = _str(main, "multi_line_mode", "psql")
    destructive_warning = _list(main, "destructive_warning")
    destructive_warning_restarts_connection = _bool(main, "destructive_warning_restarts_connection", False)
    destructive_statements_require_transaction = _bool(main, "destructive_statements_require_transaction", False)
    expand = _bool(main, "expand", False)
    auto_expand = _bool(main, "auto_expand", False)
    auto_retry_closed_connection = _bool(main, "auto_retry_closed_connection", True)
    generate_aliases = _bool(main, "generate_aliases", False)
    alias_map_file = _str(main, "alias_map_file", "")
    log_file = _str(main, "log_file", "default")
    keyword_casing = _str(main, "keyword_casing", "auto")
    casing_file = _str(main, "casing_file", "default")
    generate_casing_file = _bool(main, "generate_casing_file", False)
    case_column_headers = _bool(main, "case_column_headers", True)
    history_file = _str(main, "history_file", "default")
    log_level = _str(main, "log_level", "INFO")
    asterisk_column_order = _str(main, "asterisk_column_order", "table_order")
    qualify_columns = _str(main, "qualify_columns", "if_more_than_one_table")
    search_path_filter = _bool(main, "search_path_filter", False)
    pager = _str(main, "pager", "")
    timing = _bool(main, "timing", True)
    hide_named_query_text = _bool(main, "hide_named_query_text", False)
    show_bottom_toolbar = _bool(main, "show_bottom_toolbar", True)
    table_format = _str(main, "table_format", "psql")
    syntax_style = _str(main, "syntax_style", "default")
    vi = _bool(main, "vi", False)
    connect_timeout: I64 = _int(main, "connect_timeout")
    on_error = _str(main, "on_error", "STOP").upper()
    row_limit: I64 = _int(main, "row_limit")
    max_field_width = _width(main)
    less_chatty = _bool(main, "less_chatty", False)
    verbose_errors = _bool(main, "verbose_errors", False)
    prompt = _str(main, "prompt", "\\u@\\h:\\d> ")
    min_num_menu_lines: I64 = _int(main, "min_num_menu_lines")
    multiline_continuation_char = _str(main, "multiline_continuation_char", "")
    null_string = _str(main, "null_string", "<null>")
    enable_pager = _bool(main, "enable_pager", True)
    keyring = _bool(main, "keyring", True)
    use_local_timezone = _bool(main, "use_local_timezone", True)
    return MainSettings(
        smart_completion=smart_completion,
        auto_suggest=auto_suggest,
        wider_completion_menu=wider_completion_menu,
        always_use_single_connection=always_use_single_connection,
        multi_line=multi_line,
        multi_line_mode=multi_line_mode,
        destructive_warning=destructive_warning,
        destructive_warning_restarts_connection=destructive_warning_restarts_connection,
        destructive_statements_require_transaction=destructive_statements_require_transaction,
        expand=expand,
        auto_expand=auto_expand,
        auto_retry_closed_connection=auto_retry_closed_connection,
        generate_aliases=generate_aliases,
        alias_map_file=alias_map_file,
        log_file=log_file,
        keyword_casing=keyword_casing,
        casing_file=casing_file,
        generate_casing_file=generate_casing_file,
        case_column_headers=case_column_headers,
        history_file=history_file,
        log_level=log_level,
        asterisk_column_order=asterisk_column_order,
        qualify_columns=qualify_columns,
        search_path_filter=search_path_filter,
        pager=pager,
        timing=timing,
        hide_named_query_text=hide_named_query_text,
        show_bottom_toolbar=show_bottom_toolbar,
        table_format=table_format,
        syntax_style=syntax_style,
        vi=vi,
        connect_timeout=connect_timeout,
        on_error=on_error,
        row_limit=row_limit,
        max_field_width=max_field_width,
        less_chatty=less_chatty,
        verbose_errors=verbose_errors,
        prompt=prompt,
        min_num_menu_lines=min_num_menu_lines,
        multiline_continuation_char=multiline_continuation_char,
        null_string=null_string,
        enable_pager=enable_pager,
        keyring=keyring,
        use_local_timezone=use_local_timezone,
    )


def parse_pgcli_config(user_text: str) -> Result[PgcliConfig, ConfigError]:
    try:
        default: Any = configobj.ConfigObj(PGCLI_DEFAULT_CONFIG.splitlines(), interpolation=False)
        user: Any = configobj.ConfigObj(user_text.splitlines(), interpolation=False)
        cfg: Any = configobj.ConfigObj()
        cfg.merge(default)
        cfg.merge(user)
        main = _main(_section(cfg, "main"))
    except (configobj.ConfigObjError, ValueError) as error:
        return Err(error=ConfigError_Invalid(message=str(error)))
    formats: Any = _section(cfg, "data_formats")
    return Ok(
        value=PgcliConfig(
            main=main,
            colors=_entries(cfg, "colors"),
            named_queries=_entries(cfg, "named queries"),
            alias_dsn=_entries(cfg, "alias_dsn"),
            init_commands=_commands(cfg, "init-commands"),
            alias_dsn_init_commands=_commands(cfg, "alias_dsn.init-commands"),
            decimal_format=_str(formats, "decimal", ""),
            float_format=_str(formats, "float", ""),
            column_date_formats=_entries(cfg, "column_date_formats"),
            ssh_tunnels=_entries(cfg, "ssh tunnels"),
            dsn_ssh_tunnels=_entries(cfg, "dsn ssh tunnels"),
        )
    )
