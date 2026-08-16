from __future__ import annotations

import os

def format_env_variable(var_name: str, fallback: str) -> str:
    val = os.getenv(var_name)
    if val is None or len(val) == 0:
        return fallback
    return val if len(val) >= len(fallback) else fallback
