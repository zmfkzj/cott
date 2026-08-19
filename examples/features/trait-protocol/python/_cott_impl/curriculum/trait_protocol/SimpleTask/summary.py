from curriculum.trait_protocol import SimpleTask


def _cott_impl_SimpleTask_summary(self: SimpleTask) -> str:
    return f"{self.title} (urgency: {self.urgency})"
