import falcon

from ebl.bibliography.application.bibliography_repository import BibliographyRepository
from ebl.cache.application.cache import DEFAULT_TIMEOUT
from ebl.realia.infrastructure.mongo_realia_repository import MongoRealiaRepository
from ebl.tests.factories.realia import RealiaEntryFactory
from ebl.tests.realia.realia_repository_helpers import create_entry_with_bibliography


def _seed_entry(
    realia_repository: MongoRealiaRepository,
    bibliography_repository: BibliographyRepository,
    **kwargs,
) -> None:
    entry = RealiaEntryFactory.build(**kwargs)
    create_entry_with_bibliography(realia_repository, bibliography_repository, entry)


def test_list_ids_returns_sorted_ids(
    realia_repository: MongoRealiaRepository,
    bibliography_repository: BibliographyRepository,
    client,
) -> None:
    for identifier in ("Pig", "Anu", "Enlil, Ellil"):
        _seed_entry(realia_repository, bibliography_repository, id=identifier)

    result = client.simulate_get("/realia/ids")

    assert result.status == falcon.HTTP_OK
    assert result.json == ["Anu", "Enlil, Ellil", "Pig"]


def test_list_ids_empty_collection(client) -> None:
    result = client.simulate_get("/realia/ids")

    assert result.status == falcon.HTTP_OK
    assert result.json == []


def test_list_ids_sets_public_cache_control(
    realia_repository: MongoRealiaRepository,
    bibliography_repository: BibliographyRepository,
    client,
) -> None:
    _seed_entry(realia_repository, bibliography_repository, id="Pig")

    result = client.simulate_get("/realia/ids")

    assert result.headers["Cache-Control"] == f"public, max-age={DEFAULT_TIMEOUT}"


def test_entry_named_all_is_reachable(
    realia_repository: MongoRealiaRepository,
    bibliography_repository: BibliographyRepository,
    client,
) -> None:
    _seed_entry(realia_repository, bibliography_repository, id="all")

    result = client.simulate_get("/realia/all")

    assert result.status == falcon.HTTP_OK
    assert result.json["_id"] == "all"


def test_list_ids_returns_ids_verbatim(
    realia_repository: MongoRealiaRepository,
    bibliography_repository: BibliographyRepository,
    client,
) -> None:
    _seed_entry(realia_repository, bibliography_repository, id="(Heiliger) Hügel")

    result = client.simulate_get("/realia/ids")

    assert result.status == falcon.HTTP_OK
    assert result.json == ["(Heiliger) Hügel"]
