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


def post(client, url, payload):
    return client.simulate_post(url, json=payload)


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param(
            {"namedEntities": [{**ENTITY_SPAN, "realiaId": KNOWN_REALIA_ID}]},
            id="realia_id_in_named_entities",
        ),
        pytest.param(
            {"realia": [{**REALIA_SPAN, "type": "PERSONAL_NAME"}]},
            id="type_in_realia",
        ),
        pytest.param(
            {"namedEntities": [{"id": "X", "span": ["Word-2"]}]}, id="no_type"
        ),
        pytest.param({"realia": [{"id": "X", "span": ["Word-2"]}]}, id="no_realia_id"),
        pytest.param(
            {"realia": [{**REALIA_SPAN, "realiaId": "Apkallu"}]}, id="lemma_id"
        ),
        pytest.param(
            {"realia": [{**REALIA_SPAN, "realiaId": "realia_"}]}, id="no_digits"
        ),
        pytest.param(
            {"realia": [{**REALIA_SPAN, "realiaId": "realia_abc"}]}, id="non_numeric"
        ),
        pytest.param(
            {"namedEntities": [{**ENTITY_SPAN, "tier": 1}]}, id="unknown_key_on_entity"
        ),
        pytest.param(
            {"realia": [{**REALIA_SPAN, "name": "x"}]}, id="unknown_key_on_realia"
        ),
    ],
)
def test_reject_invalid_annotation(client, stored_realia, annotation_url, payload):
    post_result = post(client, annotation_url, payload)

    assert post_result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_reject_unknown_realia_id(client, stored_realia, annotation_url):
    payload = {"realia": [{**REALIA_SPAN, "realiaId": UNKNOWN_REALIA_ID}]}

    post_result = post(client, annotation_url, payload)

    assert post_result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert UNKNOWN_REALIA_ID in post_result.json["description"]


def test_missing_keys_default_to_empty(client, stored_realia, annotation_url):
    post_result = post(client, annotation_url, {})

    assert post_result.status == falcon.HTTP_OK
    assert client.simulate_get(annotation_url).json == {
        "namedEntities": [],
        "realia": [],
    }


def test_reject_without_scope(guest_client, annotation_url):
    post_result = guest_client.simulate_post(
        annotation_url, json={"namedEntities": [ENTITY_SPAN]}
    )

    assert post_result.status == falcon.HTTP_FORBIDDEN
