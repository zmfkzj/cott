from curriculum.trait_protocol import SimpleTask


def _cott_impl_SimpleTask_complete(self: SimpleTask) -> bool:
    self.completed = True
    return self.completed
