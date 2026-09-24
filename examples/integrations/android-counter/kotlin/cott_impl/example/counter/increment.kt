package cott_impl.example.counter

internal fun increment(current: kotlin.Int): kotlin.Int {
    require(current >= 0) { "precondition violated: current >= 0" }
    require(current < 100) { "precondition violated: current < 100" }
    return current + 1
}
