import json

import falcon
import pytest

from ebl.common.domain.scopes import Scope
from ebl.schemas import ScopeField
from ebl.fragmentarium.web.dtos import create_response_dto
from ebl.tests.factories.fragment import FragmentFactory


@pytest.mark.parametrize(
    "parameters",
    [
        {
            "currentScopes": [],
            "newScopes": [Scope.READ_CAIC_FRAGMENTS],
        },
        {
            "currentScopes": [Scope.READ_CAIC_FRAGMENTS],
            "newScopes": [
                Scope.READ_ITALIANNINEVEH_FRAGMENTS,
                Scope.READ_CAIC_FRAGMENTS,
            ],
        },
        {
            "currentScopes": [Scope.READ_CAIC_FRAGMENTS],
            "newScopes": [],
        },
    ],
)
def test_update_scopes(client, fragmentarium, user, parameters):
    fragment = FragmentFactory.build(authorized_scopes=parameters["currentScopes"])
    fragment_number = fragmentarium.create(fragment)
    updates = {"authorized_scopes": parameters["newScopes"]}
    json_updates = {
        "authorized_scopes": [
            ScopeField()._serialize_enum(scope) for scope in parameters["newScopes"]
        ]
    }
    post_result = client.simulate_post(
        f"/fragments/{fragment_number}/scopes", body=json.dumps(json_updates)
    )
    expected_json = {
        **create_response_dto(
            fragment.set_scopes(updates["authorized_scopes"]),
            user,
            fragment.number == "K.1",
        )
    }
    assert post_result.status == falcon.HTTP_OK
    assert post_result.json == expected_json

    get_result = client.simulate_get(f"/fragments/{fragment_number}")
    assert get_result.json == expected_json