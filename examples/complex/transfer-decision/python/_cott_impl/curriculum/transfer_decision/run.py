from cott_runtime import Ok, Result
from curriculum.transfer_decision_types import TransferDecision, TransferDecision_Accepted, TransferError


def run() -> Result[TransferDecision, TransferError]:
    return Ok(value=TransferDecision_Accepted())
