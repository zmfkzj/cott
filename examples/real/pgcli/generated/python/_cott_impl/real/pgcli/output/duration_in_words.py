from cott_runtime import F64


def duration_in_words(seconds: F64) -> str:
    if not seconds:
        return "0 seconds"
    components: list[str] = []
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)
    if hours > 1:
        components.append(f"{int(hours)} hours")
    elif hours == 1:
        components.append("1 hour")
    if minutes > 1:
        components.append(f"{int(minutes)} minutes")
    elif minutes == 1:
        components.append("1 minute")
    if secs >= 2:
        components.append(f"{int(secs)} seconds")
    elif secs >= 1:
        components.append("1 second")
    elif secs:
        components.append(f"{round(secs, 3)} second")
    return " ".join(components)
