package cott_impl.curriculum.effects_selection

internal fun read_text(source: java.nio.file.Path): cott_runtime.CottResult<curriculum.effects_selection.FileText, curriculum.effects_selection.EffectError> {
    val bytes: ByteArray = try {
        java.nio.file.Files.readAllBytes(source)
    } catch (error: java.nio.file.NoSuchFileException) {
        return cott_runtime.Err(curriculum.effects_selection.EffectError.InputMissing(source))
    } catch (error: java.io.IOException) {
        return cott_runtime.Err(curriculum.effects_selection.EffectError.OperationFailed(error.message ?: error.toString()))
    } catch (error: SecurityException) {
        return cott_runtime.Err(curriculum.effects_selection.EffectError.OperationFailed(error.message ?: error.toString()))
    }
    val decoder = java.nio.charset.StandardCharsets.UTF_8.newDecoder()
        .onMalformedInput(java.nio.charset.CodingErrorAction.REPORT)
        .onUnmappableCharacter(java.nio.charset.CodingErrorAction.REPORT)
    val text: String = try {
        decoder.decode(java.nio.ByteBuffer.wrap(bytes)).toString()
    } catch (error: java.nio.charset.CharacterCodingException) {
        return cott_runtime.Err(curriculum.effects_selection.EffectError.OperationFailed("invalid UTF-8: " + (error.message ?: error.toString())))
    }
    return cott_runtime.Ok(curriculum.effects_selection.FileText(source, text))
}
