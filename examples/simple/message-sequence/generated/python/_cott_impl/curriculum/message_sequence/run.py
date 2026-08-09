from curriculum.message_sequence_types import Message


def run() -> Message:
    return Message(text="x", sequence=4 + 1)
