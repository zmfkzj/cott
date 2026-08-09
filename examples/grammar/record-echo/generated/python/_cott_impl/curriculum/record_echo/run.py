from curriculum.record_echo_types import Message


def run() -> Message:
    return Message(text="hello", sequence=7)
