from real.harlequin.ide_types import ConfirmModal, ConfirmOutcome, ConfirmOutcome_No, ConfirmOutcome_Stay, ConfirmOutcome_Yes, ConfirmStep


def confirm_key(modal: ConfirmModal, key: str) -> ConfirmStep:
    if key in ("left", "right", "tab", "shift+tab"):
        return ConfirmStep(modal=ConfirmModal(prompt=modal.prompt, yes_selected=not modal.yes_selected), outcome=ConfirmOutcome_Stay())
    outcome: ConfirmOutcome
    if key == "enter":
        outcome = ConfirmOutcome_Yes() if modal.yes_selected else ConfirmOutcome_No()
    elif key == "y":
        outcome = ConfirmOutcome_Yes()
    elif key in ("n", "escape"):
        outcome = ConfirmOutcome_No()
    else:
        outcome = ConfirmOutcome_Stay()
    return ConfirmStep(modal=modal, outcome=outcome)
