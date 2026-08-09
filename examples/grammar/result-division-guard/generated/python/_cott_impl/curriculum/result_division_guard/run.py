from cott_runtime import Err
from curriculum.result_division_guard_types import ZeroDivisor


def run() -> Err[ZeroDivisor]:
    return Err(error=ZeroDivisor())
