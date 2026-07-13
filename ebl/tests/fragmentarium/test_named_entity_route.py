import falcon
import pytest
from ebl.fragmentarium.application.named_entity_schema import (
    AnnotationSpanSchema,
    EntityAnnotationSpanSchema,
)
from ebl.fragmentarium.web.dtos import create_response_dto
from ebl.tests.factories.fragment import TransliteratedFragmentFactory
from ebl.transliteration.domain.museum_number import MuseumNumber


@pytest.fixture
def serialized_annotations(named_entity_spans):
    return EntityAnnotationSpanSchema().dump(named_entity_spans, many=True)


@pytest.fixture
def serialized_mixed_annotations(mixed_annotation_spans):
    return AnnotationSpanSchema().dump(mixed_annotation_spans, many=True)


def create_url(fragment) -> str:
    return f"/fragments/{fragment.number}/named-entities"


def build_dto(fragment, user):
    return create_response_dto(
        fragment, user, fragment.number == MuseumNumber("K", "1")
    )


def test_fetch_named_entity_annotation(
    client, fragmentarium, named_entity_spans, serialized_annotations
):
    fragment = (
        TransliteratedFragmentFactory.build()
        .set_token_ids()
        .set_named_entities(named_entity_spans)
    )
    fragmentarium.create(fragment)

    get_result = client.simulate_get(create_url(fragment))

    assert get_result.status == falcon.HTTP_OK
    assert get_result.json == serialized_annotations


def test_update_named_entity_annotation(
    client, fragmentarium, user, named_entity_spans, serialized_annotations
):
    fragment = TransliteratedFragmentFactory.build().set_token_ids()
    fragmentarium.create(fragment)

    post_result = client.simulate_post(
        create_url(fragment), json={"annotations": serialized_annotations}
    )

    assert post_result.status == falcon.HTTP_OK
    assert post_result.json == build_dto(
        fragment.set_named_entities(named_entity_spans), user
    )


def test_round_trip_mixed_annotations(
    client, fragmentarium, stored_realia, serialized_mixed_annotations
):
    fragment = TransliteratedFragmentFactory.build().set_token_ids()
    fragmentarium.create(fragment)
    url = create_url(fragment)

    post_result = client.simulate_post(
        url, json={"annotations": serialized_mixed_annotations}
    )
    assert post_result.status == falcon.HTTP_OK

    get_result = client.simulate_get(url)
    assert get_result.status == falcon.HTTP_OK
    assert get_result.json == serialized_mixed_annotations


def test_round_trip_overlapping_annotations(
    client, fragmentarium, stored_realia, overlapping_annotation_spans
):
    serialized = AnnotationSpanSchema().dump(overlapping_annotation_spans, many=True)
    fragment = TransliteratedFragmentFactory.build().set_token_ids()
    fragmentarium.create(fragment)
    url = create_url(fragment)

    post_result = client.simulate_post(url, json={"annotations": serialized})
    assert post_result.status == falcon.HTTP_OK

    get_result = client.simulate_get(url)
    assert get_result.status == falcon.HTTP_OK
    assert get_result.json == serialized


def test_fetch_legacy_entity_annotations_unchanged(
    client, fragmentarium, named_entity_spans
):
    fragment = (
        TransliteratedFragmentFactory.build()
        .set_token_ids()
        .set_named_entities(named_entity_spans)
    )
    fragmentarium.create(fragment)

    get_result = client.simulate_get(create_url(fragment))

    assert get_result.json == [
        {"id": "Entity-1", "type": "PERSONAL_NAME", "span": ["Word-2"]},
        {"id": "Entity-2", "type": "BUILDING_NAME", "span": ["Word-2", "Word-3"]},
        {"id": "Entity-3", "type": "YEAR_NAME", "span": ["Word-7", "Word-14"]},
    ]


def test_fetch_without_annotations(client, fragmentarium):
    fragment = TransliteratedFragmentFactory.build().set_token_ids()
    fragmentarium.create(fragment)

    get_result = client.simulate_get(create_url(fragment))

    assert get_result.status == falcon.HTTP_OK
    assert get_result.json == []


def annotated_word_entity_ids(dto) -> set:
    return {
        entity_id
        for line in dto["text"]["lines"]
        for word in line["content"]
        for entity_id in word.get("namedEntities", [])
    }


def test_delete_realia_span(
    client, fragmentarium, stored_realia, serialized_mixed_annotations
):
    fragment = TransliteratedFragmentFactory.build().set_token_ids()
    fragmentarium.create(fragment)
    url = create_url(fragment)
    annotated = client.simulate_post(
        url, json={"annotations": serialized_mixed_annotations}
    )
    assert annotated_word_entity_ids(annotated.json) == {
        "Entity-1",
        "Entity-2",
        "Entity-3",
        "Realia-1",
        "Realia-2",
    }

    remaining = [
        annotation
        for annotation in serialized_mixed_annotations
        if "realiaId" not in annotation
    ]
    post_result = client.simulate_post(url, json={"annotations": remaining})

    assert post_result.status == falcon.HTTP_OK
    assert annotated_word_entity_ids(post_result.json) == {
        "Entity-1",
        "Entity-2",
        "Entity-3",
    }
    assert client.simulate_get(url).json == remaining
