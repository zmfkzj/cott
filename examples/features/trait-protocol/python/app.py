from __future__ import annotations

from curriculum.trait_protocol import Dyn, SimpleTask, TaskView, format_summary, inspect_dyn, inspect_task

task = SimpleTask("Write Documentation", 2)
task_view = Dyn(value=task, trait=TaskView)
print(format_summary(task))
print(inspect_task(task))
print(f"Dyn: {inspect_dyn(task_view)}")
print(f"Priority: {task.priority_level()}")
print(f"Completed: {task.complete()}")
