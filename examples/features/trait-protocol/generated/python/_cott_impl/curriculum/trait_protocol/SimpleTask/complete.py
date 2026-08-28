from curriculum.trait_protocol import SimpleTask
from curriculum.trait_protocol_types import TaskLifecycle_Completed


def _cott_impl_SimpleTask_complete(self: SimpleTask) -> bool:
    self.lifecycle = TaskLifecycle_Completed()
    return True
