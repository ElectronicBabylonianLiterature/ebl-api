import falcon
import pytest

from ebl.fragmentarium.application.named_entity_schema import (
    EntityAnnotationSpanSchema,
    RealiaAnnotationSpanSchema,
)
from ebl.fragmentarium.web.dtos import create_response_dto
from ebl.tests.factories.fragment import TransliteratedFragmentFactory
from ebl.transliteration.domain.museum_number import MuseumNumber


@pytest.fixture
def serialized_entities(named_entity_spans):
    return EntityAnnotationSpanSchema().dump(named_entity_spans, many=True)


@pytest.fixture
def serialized_realia(realia_annotation_spans):
    return RealiaAnnotationSpanSchema().dump(realia_annotation_spans, many=True)


def create_url(fragment) -> str:
    return f"/fragments/{fragment.number}/named-entities"


def annotated_fragment(fragmentarium, *annotations):
    fragment = TransliteratedFragmentFactory.build().set_token_ids()
    if annotations:
        fragment = fragment.set_named_entities(*annotations)
    fragmentarium.create(fragment)
    return fragment


def test_fetch_entity_annotations(
    client, fragmentarium, named_entity_spans, serialized_entities
):
    fragment = annotated_fragment(fragmentarium, named_entity_spans)

    get_result = client.simulate_get(create_url(fragment))

    assert get_result.status == falcon.HTTP_OK
    assert get_result.json == {"namedEntities": serialized_entities, "realia": []}


def test_fetch_without_annotations(client, fragmentarium):
    fragment = annotated_fragment(fragmentarium)

    get_result = client.simulate_get(create_url(fragment))

    assert get_result.status == falcon.HTTP_OK
    assert get_result.json == {"namedEntities": [], "realia": []}


def test_update_entity_annotations(
    client, fragmentarium, user, named_entity_spans, serialized_entities
):
    fragment = annotated_fragment(fragmentarium)

    post_result = client.simulate_post(
        create_url(fragment),
        json={"namedEntities": serialized_entities, "realia": []},
    )

    assert post_result.status == falcon.HTTP_OK
    assert post_result.json == create_response_dto(
        fragment.set_named_entities(named_entity_spans),
        user,
        fragment.number == MuseumNumber("K", "1"),
        [],
    )


def test_round_trip_both_kinds(
    client, fragmentarium, stored_realia, serialized_entities, serialized_realia
):
    fragment = annotated_fragment(fragmentarium)
    url = create_url(fragment)
    payload = {"namedEntities": serialized_entities, "realia": serialized_realia}

    assert client.simulate_post(url, json=payload).status == falcon.HTTP_OK
    assert client.simulate_get(url).json == payload


def test_round_trip_same_token_range(
    client,
    fragmentarium,
    stored_realia,
    overlapping_annotation_spans,
    overlapping_realia_spans,
):
    payload = {
        "namedEntities": EntityAnnotationSpanSchema().dump(
            overlapping_annotation_spans, many=True
        ),
        "realia": RealiaAnnotationSpanSchema().dump(
            overlapping_realia_spans, many=True
        ),
    }
    fragment = annotated_fragment(fragmentarium)
    url = create_url(fragment)

    assert client.simulate_post(url, json=payload).status == falcon.HTTP_OK
    assert client.simulate_get(url).json == payload


def test_kinds_stay_separate_on_the_word(
    client, fragmentarium, stored_realia, serialized_entities, serialized_realia
):
    fragment = annotated_fragment(fragmentarium)
    payload = {"namedEntities": serialized_entities, "realia": serialized_realia}

    post_result = client.simulate_post(create_url(fragment), json=payload)

    words = [
        word
        for line in post_result.json["text"]["lines"]
        for word in line["content"]
        if "namedEntities" in word
    ]
    assert any(word["namedEntities"] for word in words)
    assert any(word["realia"] for word in words)
    for word in words:
        assert all(id_.startswith("Entity-") for id_ in word["namedEntities"])
        assert all(id_.startswith("Realia-") for id_ in word["realia"])


def test_delete_realia_keeps_entities(
    client, fragmentarium, stored_realia, serialized_entities, serialized_realia
):
    fragment = annotated_fragment(fragmentarium)
    url = create_url(fragment)
    client.simulate_post(
        url, json={"namedEntities": serialized_entities, "realia": serialized_realia}
    )

    post_result = client.simulate_post(
        url, json={"namedEntities": serialized_entities, "realia": []}
    )

    assert post_result.status == falcon.HTTP_OK
    assert client.simulate_get(url).json == {
        "namedEntities": serialized_entities,
        "realia": [],
    }
