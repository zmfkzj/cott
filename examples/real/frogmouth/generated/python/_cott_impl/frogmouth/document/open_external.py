import subprocess
import sys


def open_external(target: str) -> bool:
    opener = "open" if sys.platform == "darwin" else "xdg-open"
    try:
        subprocess.Popen(
            [opener, target],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError:
        return False
    return True
