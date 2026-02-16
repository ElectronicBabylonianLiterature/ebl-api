import falcon
import pytest
import json
from ebl.common.domain.period import Period, PeriodModifier
from ebl.fragmentarium.application.fragment_fields_schemas import ScriptSchema

from ebl.fragmentarium.web.dtos import create_response_dto
from ebl.tests.factories.fragment import FragmentFactory, ScriptFactory


@pytest.mark.parametrize(
    "currentScript,updatedScript",
    [
        (
            ScriptFactory.build(
                period=Period.FARA, period_modifier=PeriodModifier.NONE, uncertain=False
            ),
            ScriptFactory.build(
                period=Period.ED_I_II,
                period_modifier=PeriodModifier.NONE,
                uncertain=False,
            ),
        ),
        (
            ScriptFactory.build(
                period=Period.NONE, period_modifier=PeriodModifier.NONE, uncertain=False
            ),
            ScriptFactory.build(
                period=Period.NEO_ASSYRIAN,
                period_modifier=PeriodModifier.EARLY,
                uncertain=True,
            ),
        ),
        (
            ScriptFactory.build(
                period=Period.HITTITE,
                period_modifier=PeriodModifier.EARLY,
            ),
            ScriptFactory.build(
                period=Period.NONE, period_modifier=PeriodModifier.NONE
            ),
        ),
    ],
)
def test_update_script(client, fragmentarium, user, currentScript, updatedScript):
    fragment = FragmentFactory.build(script=currentScript)
    fragment_number = fragmentarium.create(fragment)
    update = {"script": ScriptSchema().dump(updatedScript)}
    post_result = client.simulate_post(
        f"/fragments/{fragment_number}/script",
        body=json.dumps(update),
    )
    expected_json = create_response_dto(
        fragment.set_script(updatedScript), user, fragment.number == "K.1"
    )

    assert post_result.status == falcon.HTTP_OK
    assert post_result.json == expected_json

    get_result = client.simulate_get(f"/fragments/{fragment_number}")
    assert get_result.json == expected_json


def test_update_invalid_script(client, fragmentarium, user, database):
    fragment = FragmentFactory.build(script=ScriptFactory(period=Period.NONE))
    fragment_number = fragmentarium.create(fragment)
    updates = {"script": "nonsense script"}

    post_result = client.simulate_post(
        f"/fragments/{fragment_number}/script", body=json.dumps(updates)
    )

    expected_json = {
        "title": "422 Unprocessable Entity",
        "description": "Invalid script data: 'nonsense script'",
    }

    assert post_result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert post_result.json == expected_json
