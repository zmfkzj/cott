from cott_runtime import Ok


def run() -> Ok[int]:
    return Ok(value=9 - 4)
