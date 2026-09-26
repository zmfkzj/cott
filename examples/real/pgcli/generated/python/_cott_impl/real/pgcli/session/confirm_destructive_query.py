import sys

import click
from cott_runtime import CottList, Nothing, Option, Some

from real.pgcli.parseutils import is_destructive


def confirm_destructive_query(queries: str, keywords: CottList[str], dsn_alias: Option[str], force: bool) -> Option[bool]:
    if not is_destructive(queries, keywords):
        return Nothing()
    if force:
        return Some(value=True)
    if not sys.stdin.isatty():
        return Nothing()
    prompt = "You're about to run a destructive command"
    if isinstance(dsn_alias, Some):
        prompt += " in " + click.style(dsn_alias.value, fg="red")
    prompt += ".\nDo you want to proceed?"
    try:
        answer = click.confirm(prompt)
    except click.Abort:
        return Some(value=False)
    return Some(value=bool(answer))
