package cott_impl.curriculum.workflow_scenario

import kotlin.coroutines.intrinsics.intercepted

internal suspend fun resolve_search(request_id: kotlin.ULong, query: kotlin.String): curriculum.workflow_scenario.SearchResult {
    require(request_id > 0uL)
    return kotlin.coroutines.intrinsics.suspendCoroutineUninterceptedOrReturn { continuation ->
        continuation.intercepted().resumeWith(
            kotlin.Result.success(curriculum.workflow_scenario.SearchResult(request_id, query, query + " result"))
        )
        kotlin.coroutines.intrinsics.COROUTINE_SUSPENDED
    }
}
