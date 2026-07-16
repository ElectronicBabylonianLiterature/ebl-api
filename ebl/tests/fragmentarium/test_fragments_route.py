import pytest
import attr
import falcon
from ebl.common.domain.scopes import Scope

from ebl.fragmentarium.domain.named_entity import RealiaAnnotationSpan
from ebl.fragmentarium.web.dtos import create_response_dto
from ebl.tests.factories.fragment import FragmentFactory, TransliteratedFragmentFactory
from ebl.tests.fragmentarium.realia_helpers import (
    create_realia_fragment,
    store_realia,
)
from ebl.transliteration.domain.museum_number import MuseumNumber
from urllib.parse import urlencode

APKALLU_ID = "realia_000846"
LAMASSU_ID = "realia_000847"
DANGLING_ID = "realia_999999"


@pytest.mark.parametrize(
    "lines_parameter,lines_slice",
    [
        ([], (0, None)),
        (
            ["0", "1"],
            (0, 2),
        ),
        (
            "1",
            (1, 2),
        ),
    ],
)
def test_get(
    client, fragmentarium, parallel_line_injector, user, lines_parameter, lines_slice
):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    fragmentarium.create(transliterated_fragment)
    query_parameters = f"?{urlencode({'lines': lines_parameter}, doseq=True)}"

    result = client.simulate_get(
        f"/fragments/{transliterated_fragment.number}{query_parameters}"
    )

    start, end = lines_slice
    text_lines = transliterated_fragment.text.lines
    end_index = end or len(text_lines)

    expected_fragment = attr.evolve(
        transliterated_fragment,
        text=attr.evolve(
            transliterated_fragment.text,
            lines=parallel_line_injector.inject(text_lines[start:end_index])
            or text_lines,
        ),
    )
    expected = create_response_dto(
        expected_fragment,
        user,
        transliterated_fragment.number == MuseumNumber("K", "1"),
        realia_info=[],
    )

    assert result.json == expected
    assert result.json["realiaInfo"] == []
    assert result.status == falcon.HTTP_OK


def test_get_invalid_lines(client, fragmentarium):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    fragmentarium.create(transliterated_fragment)

    result = client.simulate_get(
        f"/fragments/{transliterated_fragment.number}?lines=invalidtest"
    )

    expected_json = {
        "title": "422 Unprocessable Entity",
        "description": "lines must be a list of integers, got ['invalidtest'] instead",
    }

    assert result.json == expected_json
    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_get_invalid_id(client):
    result = client.simulate_get("/fragments/invalid-number")

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_get_not_found(client):
    result = client.simulate_get("/fragments/unknown.number")

    assert result.status == falcon.HTTP_NOT_FOUND


def test_get_fragment_as_guest(guest_client, fragmentarium):
    fragment = FragmentFactory.build()
    fragmentarium.create(fragment)
    result = guest_client.simulate_get(f"/fragments/{fragment.number}")

    assert result.status == falcon.HTTP_OK


def test_get_restricted_fragment_as_guest(guest_client, fragmentarium):
    fragment = FragmentFactory.build(
        authorized_scopes=[Scope.READ_SIPPARLIBRARY_FRAGMENTS]
    )
    fragmentarium.create(fragment)
    result = guest_client.simulate_get(f"/fragments/{fragment.number}")

    assert result.status == falcon.HTTP_FORBIDDEN


def test_fragments_retrieve_all(guest_client, fragmentarium):
    fragments = TransliteratedFragmentFactory.build_batch(5)
    fragment_with_scope = TransliteratedFragmentFactory.build(
        authorized_scopes=[Scope.READ_ITALIANNINEVEH_FRAGMENTS]
    )
    fragmentarium.create(fragment_with_scope)
    for fragment in fragments:
        fragmentarium.create(fragment)
    result = guest_client.simulate_get("/fragments/retrieve-all?skip=0")
    assert result.status == falcon.HTTP_OK
    assert len(result.json["fragments"]) == 0
    assert result.json["totalCount"] == 0


def test_get_all_fragment_ocred_signs(client, fragmentarium):
    fragment = TransliteratedFragmentFactory.build()
    fragmentarium.create(fragment)

    result = client.simulate_get("/fragments/all-ocred-signs")

    assert result.status == falcon.HTTP_OK
    assert len(result.json) == 1
    assert "ocredSigns" in result.json[0]
    assert result.json[0]["ocredSigns"] == "ABZ10 X"


def test_get_all_fragment_signs(client, fragmentarium):
    fragment = TransliteratedFragmentFactory.build()
    fragmentarium.create(fragment)

    result = client.simulate_get("/fragments/all-signs")

    assert result.status == falcon.HTTP_OK
    assert len(result.json) == 1


def test_retrieve_all_serializes_fragment(client, fragmentarium):
    fragment = TransliteratedFragmentFactory.build(authorized_scopes=None)
    fragmentarium.create(fragment)

    result = client.simulate_get("/fragments/retrieve-all?skip=0")

    assert result.status == falcon.HTTP_OK
    assert result.json["totalCount"] == 1
    [serialized] = result.json["fragments"]
    assert "atf" in serialized
    assert "hasPhoto" in serialized
    assert "text" not in serialized
    assert serialized["realiaInfo"] == []


def test_retrieve_all_resolves_realia_info(
    client, fragmentarium, realia_repository, monkeypatch
):
    store_realia(realia_repository, APKALLU_ID, "Apkallu", ["Divine names"])
    store_realia(realia_repository, LAMASSU_ID, "Lamassu", ["Object names"])
    create_realia_fragment(
        fragmentarium,
        [RealiaAnnotationSpan("Realia-1", APKALLU_ID, ["Word-2", "Word-3"])],
        authorized_scopes=None,
    )
    create_realia_fragment(
        fragmentarium,
        [RealiaAnnotationSpan("Realia-1", LAMASSU_ID, ["Word-7"])],
        authorized_scopes=None,
    )
    calls = []
    original = realia_repository.find_by_realia_ids
    monkeypatch.setattr(
        realia_repository,
        "find_by_realia_ids",
        lambda realia_ids: calls.append(list(realia_ids)) or original(realia_ids),
    )

    result = client.simulate_get("/fragments/retrieve-all?skip=0")

    assert result.status == falcon.HTTP_OK
    realia_info = [fragment["realiaInfo"] for fragment in result.json["fragments"]]
    assert sorted(realia_info, key=lambda info: info[0]["realiaId"]) == [
        [{"realiaId": APKALLU_ID, "lemma": "Apkallu", "type": ["Divine names"]}],
        [{"realiaId": LAMASSU_ID, "lemma": "Lamassu", "type": ["Object names"]}],
    ]
    assert calls == [[APKALLU_ID, LAMASSU_ID]]


def test_retrieve_all_skips_dangling_realia_id(
    client, fragmentarium, realia_repository
):
    store_realia(realia_repository, APKALLU_ID, "Apkallu", ["Divine names"])
    create_realia_fragment(
        fragmentarium,
        [
            RealiaAnnotationSpan("Realia-1", APKALLU_ID, ["Word-2"]),
            RealiaAnnotationSpan("Realia-2", DANGLING_ID, ["Word-7"]),
        ],
        authorized_scopes=None,
    )

    result = client.simulate_get("/fragments/retrieve-all?skip=0")

    assert result.status == falcon.HTTP_OK
    [serialized] = result.json["fragments"]
    assert serialized["realiaInfo"] == [
        {"realiaId": APKALLU_ID, "lemma": "Apkallu", "type": ["Divine names"]}
    ]


def test_retrieve_all_skip_not_numeric(client):
    result = client.simulate_get("/fragments/retrieve-all?skip=abc")

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_retrieve_all_skip_negative(client):
    result = client.simulate_get("/fragments/retrieve-all?skip=-1")

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_retrieve_all_skip_greater_than_total(client):
    result = client.simulate_get("/fragments/retrieve-all?skip=99")

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
