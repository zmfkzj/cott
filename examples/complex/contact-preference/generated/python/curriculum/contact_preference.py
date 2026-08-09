from __future__ import annotations

from cott_runtime import _cott_load

from curriculum.contact_preference_types import ContactPreference, Email, Sms

run = _cott_load("_cott_impl/curriculum/contact_preference/run.py", "e798462cb4c0d23a8d91f05086f88ba672fe577abffe6cc16a51d8da453dc800", "run")

__all__ = ["ContactPreference", "Email", "Sms", "run"]

if __name__ == "__main__":
    from cott_runtime import _cott_display
    print(_cott_display(run()))
