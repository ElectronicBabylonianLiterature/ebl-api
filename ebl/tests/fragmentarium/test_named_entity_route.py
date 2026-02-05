import falcon
import pytest
from ebl.fragmentarium.application.named_entity_schema import EntityAnnotationSpanSchema
from ebl.fragmentarium.web.dtos import create_response_dto
from ebl.tests.factories.fragment import TransliteratedFragmentFactory
from ebl.transliteration.domain.museum_number import MuseumNumber


@pytest.fixture
def serialized_annotations(named_entity_spans):
    return EntityAnnotationSpanSchema().dump(named_entity_spans, many=True)


def test_fetch_named_entity_annotation(
    client, fragmentarium, named_entity_spans, serialized_annotations
):
    fragment = (
        TransliteratedFragmentFactory.build()
        .set_token_ids()
        .set_named_entities(named_entity_spans)
    )
    fragmentarium.create(fragment)

    url = f"/fragments/{fragment.number}/named-entities"
    get_result = client.simulate_get(url)

    assert get_result.status == falcon.HTTP_OK
    assert get_result.json == serialized_annotations


def test_update_named_entity_annotation(
    client, fragmentarium, user, named_entity_spans, serialized_annotations
):
    fragment = TransliteratedFragmentFactory.build().set_token_ids()
    fragmentarium.create(fragment)

    url = f"/fragments/{fragment.number}/named-entities"
    post_result = client.simulate_post(
        url, json={"annotations": serialized_annotations}
    )
    updated_fragment = create_response_dto(
        fragment.set_named_entities(named_entity_spans),
        user,
        fragment.number == MuseumNumber("K", "1"),
    )
    assert post_result.status == falcon.HTTP_OK
    assert post_result.json == updated_fragment
