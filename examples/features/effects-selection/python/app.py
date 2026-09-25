from __future__ import annotations

from curriculum.effects_selection import (
    clock_ns,
    copy_text,
    fetch_local,
    read_text,
)


def main() -> None:
    facades = (
        read_text,
        copy_text,
        fetch_local,
        clock_ns,
    )
    print("Compiler-owned fixture scenarios exercise: " + ", ".join(facade.__name__ for facade in facades))


if __name__ == "__main__":
    main()
