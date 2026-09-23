package cott_impl.curriculum.effects_selection

internal fun sample_index(limit: kotlin.UByte, seed: kotlin.ULong): kotlin.UByte {
    require(limit > 0u) { "limit must be greater than zero" }
    return java.util.SplittableRandom(seed.toLong()).nextInt(limit.toInt()).toUByte()
}
