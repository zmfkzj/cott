from __future__ import annotations

from cott_runtime import _cott_load

from curriculum.validated_user_card_types import UserId, UserName, UserCard, CardError, InvalidId

run = _cott_load("_cott_impl/curriculum/validated_user_card/run.py", "e1c7a89d8217cd191455755d959717602865e7297c652101bcc055970e79375d", "run")

__all__ = ["UserId", "UserName", "UserCard", "CardError", "InvalidId", "run"]

if __name__ == "__main__":
    from cott_runtime import _cott_display
    print(_cott_display(run()))
