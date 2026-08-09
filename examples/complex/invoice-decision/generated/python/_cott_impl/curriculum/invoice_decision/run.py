from curriculum.invoice_decision_types import Rejected


def run() -> Rejected:
    return Rejected(reason="missing tax id")
