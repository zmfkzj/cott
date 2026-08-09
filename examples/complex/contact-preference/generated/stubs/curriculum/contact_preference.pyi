from __future__ import annotations

from typing import TypeAlias, Union

from curriculum.contact_preference_types import ContactPreference, Email, Sms
ContactPreference: TypeAlias = Union[Email, Sms]

def run() -> ContactPreference: ...
