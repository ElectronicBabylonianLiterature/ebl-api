import falcon
import pytest

from ebl.tests.factories.fragment import TransliteratedFragmentFactory
from ebl.tests.fragmentarium.conftest import KNOWN_REALIA_ID, OTHER_REALIA_ID

ENTITY_SPAN = {"id": "Entity-1", "type": "PERSONAL_NAME", "span": ["Word-2"]}
REALIA_SPAN = {"id": "Realia-1", "realiaId": KNOWN_REALIA_ID, "span": ["Word-2"]}


@pytest.fixture
def annotation_url(fragmentarium):
    fragment = TransliteratedFragmentFactory.build().set_token_ids()
    fragmentarium.create(fragment)
    return f"/fragments/{fragment.number}/named-entities"


def post(client, url, annotations):
    return client.simulate_post(url, json={"annotations": annotations})


@pytest.mark.parametrize(
    "annotations,expected",
    [
        pytest.param(
            [ENTITY_SPAN, {**ENTITY_SPAN, "id": "Entity-2"}],
            [ENTITY_SPAN],
            id="same_tag_same_span",
        ),
        pytest.param(
            [REALIA_SPAN, {**REALIA_SPAN, "id": "Realia-2"}],
            [REALIA_SPAN],
            id="same_realia_same_span",
        ),
        pytest.param(
            [ENTITY_SPAN, ENTITY_SPAN],
            [ENTITY_SPAN],
            id="exact_duplicate_including_id",
        ),
    ],
)
def test_duplicates_are_dropped(
    client, stored_realia, annotation_url, annotations, expected
):
    post_result = post(client, annotation_url, annotations)

    assert post_result.status == falcon.HTTP_OK
    assert client.simulate_get(annotation_url).json == expected


@pytest.mark.parametrize(
    "annotations",
    [
        pytest.param(
            [ENTITY_SPAN, {**ENTITY_SPAN, "id": "Entity-2", "span": ["Word-3"]}],
            id="same_tag_different_span",
        ),
        pytest.param(
            [ENTITY_SPAN, {**ENTITY_SPAN, "id": "Entity-2", "type": "DIVINE_NAME"}],
            id="different_tag_same_span",
        ),
        pytest.param(
            [REALIA_SPAN, {**REALIA_SPAN, "id": "Realia-2", "span": ["Word-3"]}],
            id="same_realia_different_span",
        ),
        pytest.param(
            [
                REALIA_SPAN,
                {**REALIA_SPAN, "id": "Realia-2", "realiaId": OTHER_REALIA_ID},
            ],
            id="different_realia_same_span",
        ),
        pytest.param([ENTITY_SPAN, REALIA_SPAN], id="tag_and_realia_same_span"),
    ],
)
def test_distinct_annotations_are_kept(
    client, stored_realia, annotation_url, annotations
):
    post_result = post(client, annotation_url, annotations)

    assert post_result.status == falcon.HTTP_OK
    assert client.simulate_get(annotation_url).json == annotations


def test_conflicting_ids_are_rejected(client, stored_realia, annotation_url):
    conflicting = {**ENTITY_SPAN, "type": "DIVINE_NAME", "span": ["Word-3"]}

    post_result = post(client, annotation_url, [ENTITY_SPAN, conflicting])

    assert post_result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert "Entity-1" in post_result.json["description"]


def test_conflicting_ids_across_layers_are_rejected(
    client, stored_realia, annotation_url
):
    realia_reusing_entity_id = {**REALIA_SPAN, "id": "Entity-1"}

    post_result = post(client, annotation_url, [ENTITY_SPAN, realia_reusing_entity_id])

    assert post_result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert "Entity-1" in post_result.json["description"]


def test_conflicting_ids_write_nothing(client, stored_realia, annotation_url):
    conflicting = {**ENTITY_SPAN, "type": "DIVINE_NAME", "span": ["Word-3"]}

    post(client, annotation_url, [ENTITY_SPAN, conflicting])

    assert client.simulate_get(annotation_url).json == []
