from curriculum.trait_protocol import SimpleTask


async def specialized_display(receiver: SimpleTask) -> str:
    return "specialized: " + receiver.title
