from sys import argv, stderr

from cott_runtime import CottList, Err
from real.posting.client import execute


def main() -> int:
    result = execute(CottList(values=tuple(argv[1:])))
    if isinstance(result, Err):
        print(result.error, file=stderr)
        return 2
    print(result.value)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
