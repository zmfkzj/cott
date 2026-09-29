from os import O_WRONLY, devnull, dup2
from os import open as os_open
from sys import argv, stderr, stdout

from cott_runtime import CottList, Err
from real.posting.client import execute


def main() -> int:
    arguments = tuple(argv[1:])
    for argument in arguments:
        try:
            argument.encode("utf-8")
        except UnicodeEncodeError:
            # Invalid UTF-8 on the command line arrives surrogate-escaped.
            print("arguments must be valid UTF-8", file=stderr)
            return 2
    result = execute(CottList(values=arguments))
    if isinstance(result, Err):
        print(result.error, file=stderr)
        return 2
    try:
        print(result.value)
        stdout.flush()
    except BrokenPipeError:
        # The reader closed stdout early (for example `| head`). Point stdout
        # at devnull so the interpreter's exit-time flush stays silent, and
        # exit with the conventional SIGPIPE status 141.
        dup2(os_open(devnull, O_WRONLY), stdout.fileno())
        return 141
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
