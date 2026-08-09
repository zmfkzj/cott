from cott_runtime import Err, I32, Result
from curriculum.result_division_guard_types import DivideError, DivideError_ZeroDivisor


def run() -> Result[I32, DivideError]:
    return Err(error=DivideError_ZeroDivisor())
