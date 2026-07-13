import falcon
import pytest

from ebl.tests.factories.fragment import TransliteratedFragmentFactory
from ebl.tests.fragmentarium.conftest import KNOWN_REALIA_ID, UNKNOWN_REALIA_ID

ENTITY_SPAN = {"id": "Entity-1", "type": "PERSONAL_NAME", "span": ["Word-2"]}
REALIA_SPAN = {"id": "Realia-1", "realiaId": KNOWN_REALIA_ID, "span": ["Word-2"]}


@pytest.fixture
def annotation_url(fragmentarium):
    fragment = TransliteratedFragmentFactory.build().set_token_ids()
    fragmentarium.create(fragment)
    return f"/fragments/{fragment.number}/named-entities"


@pytest.mark.parametrize(
    "annotation",
    [
        pytest.param(
            {**ENTITY_SPAN, "realiaId": KNOWN_REALIA_ID}, id="type_and_realia"
        ),
        pytest.param({"id": "X", "span": ["Word-2"]}, id="neither_type_nor_realia"),
        pytest.param({**REALIA_SPAN, "realiaId": "Apkallu"}, id="lemma_id"),
        pytest.param({**REALIA_SPAN, "realiaId": "realia_"}, id="no_digits"),
        pytest.param({**REALIA_SPAN, "realiaId": "realia_abc"}, id="non_numeric"),
        pytest.param({**REALIA_SPAN, "tier": 1}, id="unknown_key_on_realia"),
        pytest.param({**ENTITY_SPAN, "name": "Marduk"}, id="unknown_key_on_entity"),
    ],
)
def test_reject_invalid_annotation(client, stored_realia, annotation_url, annotation):
    post_result = client.simulate_post(
        annotation_url, json={"annotations": [annotation]}
    )

    assert post_result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_reject_unknown_realia_id(client, stored_realia, annotation_url):
    annotation = {**REALIA_SPAN, "realiaId": UNKNOWN_REALIA_ID}

    post_result = client.simulate_post(
        annotation_url, json={"annotations": [annotation]}
    )

    assert post_result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert UNKNOWN_REALIA_ID in post_result.json["description"]


def test_reject_without_scope(guest_client, annotation_url):
    post_result = guest_client.simulate_post(
        annotation_url, json={"annotations": [ENTITY_SPAN]}
    )

    assert post_result.status == falcon.HTTP_FORBIDDEN
