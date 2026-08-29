from __future__ import annotations

import asyncio

from cott_runtime import Dyn
from curriculum.trait_protocol import SimpleTask, TaskView, inspect_dyn, task_factory


async def main() -> None:
    factory = task_factory()
    print(f"Factory exact: {factory is SimpleTask}")
    task = factory("Write Documentation", 2)
    task_view = Dyn(value=task, trait=TaskView[str])
    print(f"Explicit: {await task.summary()}")
    print(f"Specialized: {await task.display()}")
    print(f"Default: {await task.category()}")
    print(f"Dyn: {await inspect_dyn(task_view)}")
    print(f"Priority: {await task.priority_level()}")
    print(f"Completed: {await task.complete()}")
    print(f"Completion count: {task.completion_count}")


if __name__ == "__main__":
    asyncio.run(main())
