import falcon
import pytest

from ebl.bibliography.application.reference_schema import ReferenceSchema
from ebl.bibliography.domain.reference import BibliographyId, ReferenceType
from ebl.common.domain.period import Period
from ebl.fragmentarium.domain.fragment import Script
from ebl.tests.factories.bibliography import BibliographyEntryFactory, ReferenceFactory
from ebl.tests.factories.fragment import FragmentFactory
from ebl.transliteration.domain.museum_number import MuseumNumber


@pytest.fixture
def spied_bibliography_repository(monkeypatch, bibliography_repository):
    calls = []
    original_query_by_ids = bibliography_repository.query_by_ids

    def query_by_ids(ids):
        calls.append(list(ids))
        return original_query_by_ids(ids)

    monkeypatch.setattr(bibliography_repository, "query_by_ids", query_by_ids)
    return bibliography_repository, calls


def reference_of(id_: str, type_: ReferenceType = ReferenceType.COPY):
    return ReferenceFactory.build(id=BibliographyId(id_), type=type_)


def build_fragment(number: str, *references):
    return FragmentFactory.build(
        number=MuseumNumber.of(number),
        script=Script(Period.LATE_BABYLONIAN),
        references=references,
    )


def test_query_returns_deduplicated_bibliography_documents(
    client, fragmentarium, spied_bibliography_repository
):
    repository, calls = spied_bibliography_repository
    entries = [BibliographyEntryFactory.build(id=id_) for id_ in ("RN52", "RN54")]
    for entry in entries:
        repository.create(entry)
    fragments = [
        build_fragment(
            "X.1",
            reference_of("RN52"),
            reference_of("RN52", ReferenceType.EDITION),
            reference_of("RN54"),
        ),
        build_fragment("X.2", reference_of("RN52", ReferenceType.PHOTO)),
    ]
    for index, fragment in enumerate(fragments):
        fragmentarium.create(fragment, sort_key=index)

    result = client.simulate_get("/fragments/query", params={"limit": "10"})

    assert result.status == falcon.HTTP_OK
    assert result.json["bibliographyDocuments"] == {
        "RN52": entries[0],
        "RN54": entries[1],
    }
    assert calls == [["RN52", "RN54"]]


def test_query_keeps_reference_occurrence_data(
    client, fragmentarium, bibliography_repository
):
    bibliography_repository.create(BibliographyEntryFactory.build(id="RN52"))
    references = (
        reference_of("RN52"),
        reference_of("RN52", ReferenceType.EDITION),
    )
    fragmentarium.create(build_fragment("X.1", *references))

    result = client.simulate_get("/fragments/query", params={"limit": "10"})

    assert result.json["items"][0]["references"] == ReferenceSchema().dump(
        references, many=True
    )
    assert [
        reference["type"] for reference in result.json["items"][0]["references"]
    ] == [
        "COPY",
        "EDITION",
    ]


def test_query_omits_missing_bibliography_documents(
    client, fragmentarium, spied_bibliography_repository
):
    repository, calls = spied_bibliography_repository
    entry = BibliographyEntryFactory.build(id="RN52")
    repository.create(entry)
    fragmentarium.create(
        build_fragment("X.1", reference_of("RN52"), reference_of("RN99"))
    )

    result = client.simulate_get("/fragments/query", params={"limit": "10"})

    assert result.status == falcon.HTTP_OK
    assert result.json["bibliographyDocuments"] == {"RN52": entry}
    assert calls == [["RN52", "RN99"]]


def test_query_bibliography_documents_are_page_bounded(
    client, fragmentarium, spied_bibliography_repository
):
    repository, calls = spied_bibliography_repository
    entries = [BibliographyEntryFactory.build(id=f"RN{index}") for index in range(4)]
    for entry in entries:
        repository.create(entry)
    for index in range(4):
        fragmentarium.create(
            build_fragment(f"X.{index}", reference_of(f"RN{index}")), sort_key=index
        )

    result = client.simulate_get(
        "/fragments/query", params={"limit": "2", "offset": "1"}
    )

    assert [item["museumNumber"]["number"] for item in result.json["items"]] == [
        "1",
        "2",
    ]
    assert set(result.json["bibliographyDocuments"]) == {"RN1", "RN2"}
    assert calls == [["RN1", "RN2"]]


def test_query_without_references_skips_bibliography_lookup(
    client, fragmentarium, spied_bibliography_repository
):
    _, calls = spied_bibliography_repository
    fragmentarium.create(build_fragment("X.1"))

    result = client.simulate_get("/fragments/query", params={"limit": "10"})

    assert result.json["bibliographyDocuments"] == {}
    assert calls == []


def test_query_without_limit_omits_bibliography_documents(
    client, fragmentarium, spied_bibliography_repository
):
    _, calls = spied_bibliography_repository
    fragmentarium.create(build_fragment("X.1", reference_of("RN52")))

    result = client.simulate_get("/fragments/query", params={"number": "X.1"})

    assert "bibliographyDocuments" not in result.json
    assert calls == []
