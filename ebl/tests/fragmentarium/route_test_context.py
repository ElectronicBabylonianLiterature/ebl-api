import json
from typing import Any

import attr
from falcon import testing
from pymongo.database import Database

from ebl.fragmentarium.application.fragmentarium import Fragmentarium
from ebl.fragmentarium.domain.fragment import Fragment
from ebl.tests.fragmentarium.transliterations_route_test_helpers import (
    find_changelog_entry,
    simulate_post_with_retry,
)
from ebl.users.domain.user import User


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
