from __future__ import annotations

from curriculum.trait_protocol import format_summary, inspect_task

class SimpleTask:
    def __init__(self, title: str, urgency: int) -> None:
        self.title = title
        self.urgency = urgency

    def summary(self) -> str:
        return f"Task: {self.title}"

    def priority_level(self) -> int:
        return self.urgency

task = SimpleTask("Write Documentation", 2)
print(format_summary(task))
print(inspect_task(task))
