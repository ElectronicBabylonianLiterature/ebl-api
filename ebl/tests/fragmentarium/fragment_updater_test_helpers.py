from typing import cast

from ebl.fragmentarium.application.fragment_schema import FragmentSchema

SCHEMA = FragmentSchema()
FROZEN_TIME = "2018-09-07 15:41:24.032"


def entry(number, fragment) -> dict:
    return {"_id": str(number), **cast(dict, SCHEMA.dump(fragment))}


def expect_changelog(when, changelog, user, number, before, after) -> None:
    when(changelog).create(
        "fragments",
        user.profile,
        entry(number, before),
        entry(number, after),
    ).thenReturn()
