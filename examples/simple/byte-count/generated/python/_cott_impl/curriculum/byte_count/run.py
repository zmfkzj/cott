from curriculum.byte_count_types import ByteCount


def run() -> ByteCount:
    data = b"abc"
    return ByteCount(data=data, count=len(data))
