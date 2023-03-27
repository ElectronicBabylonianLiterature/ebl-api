import json

import falcon
import pytest
from ebl.fragmentarium.domain.fragment import Notes, Fragment

from ebl.fragmentarium.web.dtos import create_response_dto
from ebl.tests.factories.fragment import FragmentFactory
from ebl.transliteration.domain.markup import StringPart, EmphasisPart


@pytest.mark.parametrize(
    "old_notes,new_notes",
    [
        [Notes(), Notes("Some notes", (StringPart("Some notes"),))],
        [Notes(), Notes()],
        [Notes("Different notes"), Notes()],
        [
            Notes("Different notes"),
            Notes(
                "Different notes @i{with emphasis}",
                (StringPart("Different notes "), EmphasisPart("with emphasis")),
            ),
        ],
    ],
)
def test_update_notes(client, fragmentarium, user, database, old_notes, new_notes):
    fragment: Fragment = FragmentFactory.build(notes=old_notes)
    fragment_number = fragmentarium.create(fragment)
    update = {"notes": new_notes.text}
    post_result = client.simulate_post(
        f"/fragments/{fragment_number}/notes", body=json.dumps(update)
    )
    expected_json = {
        **create_response_dto(
            fragment.set_notes(new_notes.text),
            user,
            fragment.number == "K.1",
        )
    }

    assert post_result.status == falcon.HTTP_OK
    assert post_result.json == expected_json

    get_result = client.simulate_get(f"/fragments/{fragment_number}")
    assert get_result.json == expected_json

    assert database["changelog"].find_one(
        {
            "resource_id": fragment_number,
            "resource_type": "fragments",
            "user_profile.name": user.profile["name"],
        }
    )
