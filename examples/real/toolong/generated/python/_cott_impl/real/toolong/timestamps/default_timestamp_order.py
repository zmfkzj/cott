from cott_runtime import CottList, U8


def default_timestamp_order() -> CottList[U8]:
    return CottList(values=list(range(17)))
