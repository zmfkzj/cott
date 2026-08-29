from __future__ import annotations

from typing import Never

from cott_runtime import U8


def exit_with_code(code: U8) -> Never:
    raise SystemExit(code)
