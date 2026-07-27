import json
from typing import Any

import attr
import falcon
from falcon import testing
from pymongo.database import Database

from ebl.fragmentarium.application.fragmentarium import Fragmentarium
from ebl.fragmentarium.domain.fragment import Fragment
from ebl.fragmentarium.web.dtos import create_response_dto
from ebl.tests.factories.fragment import FragmentFactory
from ebl.tests.fragmentarium.transliterations_route_test_helpers import (
    find_changelog_entry,
    simulate_post_with_retry,
)
from ebl.users.domain.user import User

INVALID_MARKUP = "@i{syntax error"


@attr.s(auto_attribs=True, frozen=True)
class RouteContext:
    client: testing.TestClient
    fragmentarium: Fragmentarium
    user: User
    database: Database

    def create(self, fragment: Fragment) -> str:
        return self.fragmentarium.create(fragment)

    def post_edition(self, number: str, update: dict) -> Any:
        return simulate_post_with_retry(
            self.client, f"/fragments/{number}/edition", json.dumps(update)
        )

    def get_fragment(self, number: str) -> Any:
        return self.client.simulate_get(f"/fragments/{number}")

    def has_changelog_entry(self, number: str) -> bool:
        return bool(
            find_changelog_entry(
                self.database,
                {
                    "resource_id": number,
                    "resource_type": "fragments",
                    "user_profile.name": self.user.profile["name"],
                },
            )
        )

    def expect_dto(self, fragment: Fragment) -> dict:
        return create_response_dto(fragment, self.user, fragment.number == "K.1", [])


def assert_edition_field_updated(
    context: RouteContext, field: str, old_value, new_value
) -> None:
    fragment: Fragment = FragmentFactory.build(**{field: old_value})
    number = context.create(fragment)

    post_result = context.post_edition(number, {field: new_value.text})
    expected_json = context.expect_dto(
        getattr(fragment, f"set_{field}")(new_value.text)
    )

    assert post_result.status == falcon.HTTP_OK
    assert post_result.json == expected_json
    assert context.get_fragment(number).json == {**expected_json, "realiaInfo": []}
    assert context.has_changelog_entry(number)


def assert_invalid_edition_field(context: RouteContext, field: str) -> None:
    number = context.create(FragmentFactory.build())

    result = context.client.simulate_post(
        f"/fragments/{number}/edition", body=json.dumps({field: INVALID_MARKUP})
    )

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
