from cott_runtime import Some
from real.pgcli.repl_types import PromptInfo


def render_prompt(template: str, info: PromptInfo) -> str:
    port_text = info.port.value if isinstance(info.port, Some) else "5432"
    text = template.replace("\\dsn_alias", info.dsn_alias)
    text = text.replace("\\t", info.now_text)
    text = text.replace("\\u", info.user or "(none)")
    text = text.replace("\\H", info.host or "(none)")
    text = text.replace("\\h", info.short_host or "(none)")
    text = text.replace("\\d", info.dbname or "(none)")
    text = text.replace("\\p", port_text)
    text = text.replace("\\i", str(info.pid))
    text = text.replace("\\#", "#" if info.superuser else ">")
    text = text.replace("\\n", "\n")
    return text.replace("\\T", info.transaction_indicator)
