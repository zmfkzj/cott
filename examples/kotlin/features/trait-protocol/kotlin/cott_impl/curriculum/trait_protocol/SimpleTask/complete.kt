package cott_impl.curriculum.trait_protocol.SimpleTask

internal suspend fun complete(self: curriculum.trait_protocol.SimpleTask): kotlin.Boolean {
    val completionCount = java.lang.Math.addExact(self.completion_count, 1)
    self.lifecycle = curriculum.trait_protocol.TaskLifecycle.Completed
    self.completion_count = completionCount
    return true
}
