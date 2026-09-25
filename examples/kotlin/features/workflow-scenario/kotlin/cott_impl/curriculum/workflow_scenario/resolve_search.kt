package cott_impl.curriculum.workflow_scenario

import kotlin.coroutines.intrinsics.COROUTINE_SUSPENDED
import kotlin.coroutines.intrinsics.intercepted
import kotlin.coroutines.intrinsics.suspendCoroutineUninterceptedOrReturn

internal suspend fun resolve_search(request_id: kotlin.ULong, query: kotlin.String): curriculum.workflow_scenario.SearchResult {
    require(request_id > 0uL)
    return suspendCoroutineUninterceptedOrReturn { continuation ->
        continuation.intercepted().resumeWith(
            kotlin.Result.success(curriculum.workflow_scenario.SearchResult(request_id, query, query + " result"))
        )
        COROUTINE_SUSPENDED
    }
}
