from curriculum.invoice_decision_types import InvoiceDecision, InvoiceDecision_Rejected


def run() -> InvoiceDecision:
    return InvoiceDecision_Rejected(reason="missing tax id")
