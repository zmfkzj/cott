from __future__ import annotations

from typing import cast

from cott_runtime import U64
from curriculum.opaque_resource_types import HandleBundle

def extract_handle_id(bundle: HandleBundle) -> U64:
    return cast(U64, bundle.handle.unwrap())
