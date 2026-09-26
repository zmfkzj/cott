from real.pgcli.session_types import StatementChanges


def classify_statement(sql: str, status: str) -> StatementChanges:
    status_parts = status.split()
    sql_parts = sql.split()
    status_word = status_parts[0].lower() if status_parts else ""
    sql_word = sql_parts[0].lower() if sql_parts else ""
    return StatementChanges(
        mutated=status_word in ("insert", "update", "delete"),
        meta_changed=sql_word in ("alter", "create", "drop", "commit", "rollback"),
        db_changed=sql_word in ("use", "\\c", "\\connect"),
        path_changed="set search_path" in sql.lower(),
    )
