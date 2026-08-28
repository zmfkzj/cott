from __future__ import annotations

import asyncio

from cott_runtime import Ok, Some
from curriculum.json_transform import (
    JsonChain_End,
    JsonChain_Link,
    extract_string_field,
    wrap_scalar_json,
)


async def main() -> None:
    payload = await wrap_scalar_json("greeting", "Hello Cott")
    extracted = extract_string_field(payload, "greeting")
    if isinstance(extracted, Ok):
        print(f"Extracted JSON field: {extracted.value}")

    chain = JsonChain_Link(value="first", next=Some(value=JsonChain_End()))
    print(f"Recursive JSON chain: {chain.value}")


asyncio.run(main())
