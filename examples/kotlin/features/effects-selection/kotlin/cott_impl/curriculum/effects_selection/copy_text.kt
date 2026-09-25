package cott_impl.curriculum.effects_selection

internal fun copy_text(source: java.nio.file.Path, destination: java.nio.file.Path): cott_runtime.CottResult<curriculum.effects_selection.CopyReceipt, curriculum.effects_selection.EffectError> {
    val file = when (val result = curriculum.effects_selection.read_text(source)) {
        is cott_runtime.Ok -> result.value
        is cott_runtime.Err -> return cott_runtime.Err(result.error)
    }
    return try {
        val bytes = file.text.toByteArray(kotlin.text.Charsets.UTF_8)
        val target = destination.toAbsolutePath()
        val temporary = java.nio.file.Files.createTempFile(target.parent, ".cott-copy-", ".tmp")
        try {
            java.nio.file.Files.write(temporary, bytes)
            java.nio.file.Files.move(
                temporary,
                target,
                java.nio.file.StandardCopyOption.ATOMIC_MOVE,
                java.nio.file.StandardCopyOption.REPLACE_EXISTING
            )
        } catch (failure: Exception) {
            try {
                java.nio.file.Files.deleteIfExists(temporary)
            } catch (cleanupFailure: Exception) {
                failure.addSuppressed(cleanupFailure)
            }
            throw failure
        }
        cott_runtime.Ok(curriculum.effects_selection.CopyReceipt(destination, bytes.size.toULong()))
    } catch (failure: Exception) {
        cott_runtime.Err(
            curriculum.effects_selection.EffectError.OperationFailed(
                failure.message ?: "Failed to copy text"
            )
        )
    }
}
