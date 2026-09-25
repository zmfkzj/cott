package cott_impl.curriculum.trait_protocol.SimpleTask

internal suspend fun complete(self: curriculum.trait_protocol.SimpleTask): kotlin.Boolean {
    self.lifecycle = curriculum.trait_protocol.TaskLifecycle.Completed
    self.completion_count = self.completion_count + 1
    return true
}
