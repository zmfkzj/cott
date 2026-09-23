package cott_impl.curriculum.effects_selection

internal fun read_text(source: java.nio.file.Path): cott_runtime.CottResult<kotlin.String, curriculum.effects_selection.EffectError> {
    return try {
        cott_runtime.Ok(java.nio.file.Files.readString(source, java.nio.charset.StandardCharsets.UTF_8))
    } catch (error: java.nio.file.NoSuchFileException) {
        cott_runtime.Err(curriculum.effects_selection.EffectError.InputMissing(source))
    } catch (error: java.io.IOException) {
        cott_runtime.Err(curriculum.effects_selection.EffectError.OperationFailed(error.message ?: error.toString()))
    } catch (error: SecurityException) {
        cott_runtime.Err(curriculum.effects_selection.EffectError.OperationFailed(error.message ?: error.toString()))
    }
}
