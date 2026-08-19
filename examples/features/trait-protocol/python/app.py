from __future__ import annotations

from curriculum.trait_protocol import SimpleTask, format_summary, inspect_task

task = SimpleTask("Write Documentation", 2)
print(format_summary(task))
print(inspect_task(task))
print(f"Priority: {task.priority_level()}")
print(f"Completed: {task.complete()}")
