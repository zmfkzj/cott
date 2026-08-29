from __future__ import annotations

from curriculum.effects_selection import (
    clock_ns,
    copy_result_is_ok,
    copy_text,
    fetch_local,
    text_result_is_ok,
    text_result_text,
)


def main() -> None:
    facades = (
        copy_text,
        fetch_local,
        clock_ns,
        copy_result_is_ok,
        text_result_is_ok,
        text_result_text,
    )
    print("Compiler-owned fixture scenarios exercise: " + ", ".join(facade.__name__ for facade in facades))


if __name__ == "__main__":
    main()
