package examples.features.trait_protocol

import cott_runtime.CottTrait
import cott_runtime.CottTrait_585c5815b17627c90fc83801
import cott_runtime.Dyn
import curriculum.trait_protocol.SimpleTask
import curriculum.trait_protocol.TaskView
import curriculum.trait_protocol.inspect_dyn
import curriculum.trait_protocol.task_factory
import kotlinx.coroutines.runBlocking

public fun main(): Unit = runBlocking {
    val factory = task_factory()
    check(factory.type === SimpleTask::class.java)
    println("Factory exact: true")

    val task = SimpleTask("Write Documentation", 2)
    val taskView: TaskView<String, *> = task
    @Suppress("UNCHECKED_CAST")
    val dynamic = Dyn.of(
        taskView,
        CottTrait_585c5815b17627c90fc83801 as CottTrait<TaskView<String, *>>,
    )

    println("Explicit: ${task.summary()}")
    println("Specialized: ${task.display()}")
    println("Default: ${task.category()}")
    println("Dyn: ${inspect_dyn(dynamic)}")
    println("Priority: ${task.priority_level()}")
    println("Completed: ${task.complete()}")
    println("Completion count: ${task.completion_count}")
}
