from typing import Literal

from cott_runtime import Opaque


def empty_completion_catalog() -> Opaque[Literal["pgcli.completion-catalog"]]:
    return Opaque(
        tag="pgcli.completion-catalog",
        value={
            "schemata": [],
            "tables": [],
            "views": [],
            "functions": [],
            "datatypes": [],
            "foreign_keys": [],
            "databases": [],
            "search_path": [],
            "casing": [],
        },
    )
