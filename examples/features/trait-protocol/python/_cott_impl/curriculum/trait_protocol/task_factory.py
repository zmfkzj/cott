from curriculum.trait_protocol import SimpleTask


def task_factory() -> type[SimpleTask]:
    return SimpleTask
