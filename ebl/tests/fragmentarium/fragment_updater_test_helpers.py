from typing import Any, Callable, cast

import attr

from ebl.changelog import Changelog
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.application.fragment_schema import FragmentSchema
from ebl.fragmentarium.domain.fragment import Fragment
from ebl.transliteration.application.parallel_line_injector import ParallelLineInjector
from ebl.users.domain.user import User

SCHEMA = FragmentSchema()
FROZEN_TIME = "2018-09-07 15:41:24.032"


def entry(number, fragment) -> dict:
    return {"_id": str(number), **cast(dict, SCHEMA.dump(fragment))}


@attr.s(auto_attribs=True, frozen=True)
class UpdaterContext:
    user: User
    repository: FragmentRepository
    injector: ParallelLineInjector
    changelog: Changelog
    when: Callable[..., Any]

    def expect_query(self, number, *fragments: Fragment) -> None:
        stub = self.when(self.repository).query_by_museum_number(number)
        for fragment in fragments:
            stub = stub.thenReturn(fragment)

    def expect_changelog(self, number, before: Fragment, after: Fragment) -> None:
        self.when(self.changelog).create(
            "fragments",
            self.user.profile,
            entry(number, before),
            entry(number, after),
        ).thenReturn()

    def expect_update_field(self, field: str, fragment: Fragment) -> None:
        self.when(self.repository).update_field(field, fragment).thenReturn()

    def inject(self, fragment: Fragment) -> Fragment:
        return fragment.set_text(self.injector.inject_transliteration(fragment.text))
