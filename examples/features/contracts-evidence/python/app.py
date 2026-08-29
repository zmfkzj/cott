from __future__ import annotations

from cott_runtime import Err, Nothing, Some
from curriculum.contracts_evidence import LabelRequest, assess_label

for request in (
    LabelRequest(label=Nothing(), minimum_length=3),
    LabelRequest(label=Some(value="ok"), minimum_length=3),
    LabelRequest(label=Some(value="evidence"), minimum_length=3),
):
    result = assess_label(request)
    if isinstance(result, Err):
        print(result.error)
    else:
        print(result.value.text)
