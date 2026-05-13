import falcon

from ebl.bibliography.application.bibliography_repository import BibliographyRepository
from ebl.realia.infrastructure.mongo_realia_repository import (
    MongoRealiaRepository,
    RealiaEntrySchema,
)
from ebl.tests.factories.realia import RealiaEntryFactory


def _seed_entry(
    realia_repository: MongoRealiaRepository,
    bibliography_repository: BibliographyRepository,
):
    entry = RealiaEntryFactory.build()
    realia_repository._realia_collection.insert_one(RealiaEntrySchema().dump(entry))
    for ref in entry.references:
        if ref.document:
            bibliography_repository.create(ref.document)
    for rlex in entry.reallexikon:
        if rlex.reference is not None and rlex.reference.document:
            bibliography_repository.create(rlex.reference.document)
    return entry


def test_get_realia_by_id(
    realia_repository: MongoRealiaRepository,
    bibliography_repository: BibliographyRepository,
    client,
) -> None:
    entry = _seed_entry(realia_repository, bibliography_repository)

    result = client.simulate_get(f"/realia/{entry.id}")

    assert result.status == falcon.HTTP_OK
    assert result.json["_id"] == entry.id


def test_get_realia_not_found(client) -> None:
    result = client.simulate_get("/realia/nonexistent")

    assert result.status == falcon.HTTP_NOT_FOUND


def test_search_realia(
    realia_repository: MongoRealiaRepository,
    bibliography_repository: BibliographyRepository,
    client,
) -> None:
    entry = _seed_entry(realia_repository, bibliography_repository)

    result = client.simulate_get("/realia", params={"query": entry.id})

    assert result.status == falcon.HTTP_OK
    assert any(r["_id"] == entry.id for r in result.json)


def test_search_realia_empty_query(client) -> None:
    result = client.simulate_get("/realia", params={"query": ""})

    assert result.status == falcon.HTTP_OK
    assert result.json == []


def test_search_realia_no_match(client) -> None:
    result = client.simulate_get("/realia", params={"query": "zzz_no_match_xyz"})

    assert result.status == falcon.HTTP_OK
    assert result.json == []


def test_search_realia_missing_query(client) -> None:
    result = client.simulate_get("/realia")

    assert result.status == falcon.HTTP_OK
    assert result.json == []
