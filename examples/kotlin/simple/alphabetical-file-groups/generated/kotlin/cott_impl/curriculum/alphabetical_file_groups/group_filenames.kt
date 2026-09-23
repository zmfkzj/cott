package cott_impl.curriculum.alphabetical_file_groups

internal fun group_filenames(filenames: cott_runtime.CottList<kotlin.String>): cott_runtime.CottResult<cott_runtime.CottList<curriculum.alphabetical_file_groups.FileMove>, curriculum.alphabetical_file_groups.FileGroupError> {
    val moves = kotlin.collections.ArrayList<curriculum.alphabetical_file_groups.FileMove>(filenames.size)
    for (filename in filenames) {
        when (val result = curriculum.alphabetical_file_groups.classify_filename(filename)) {
            is cott_runtime.Ok -> moves.add(result.value)
            is cott_runtime.Err -> return result
        }
    }
    return cott_runtime.Ok(cott_runtime.CottList(moves))
}
