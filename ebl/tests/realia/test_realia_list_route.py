import falcon

from ebl.bibliography.application.bibliography_repository import BibliographyRepository
from ebl.cache.application.cache import DEFAULT_TIMEOUT
from ebl.realia.domain.reserved_identifiers import RESERVED_REALIA_IDS
from ebl.realia.infrastructure.mongo_realia_repository import MongoRealiaRepository
from ebl.tests.factories.realia import RealiaEntryFactory
from ebl.tests.realia.realia_repository_helpers import create_entry_with_bibliography

LIST_ROUTE = "/realia/all"


def _seed_entry(
    realia_repository: MongoRealiaRepository,
    bibliography_repository: BibliographyRepository,
    **kwargs,
) -> None:
    entry = RealiaEntryFactory.build(**kwargs)
    create_entry_with_bibliography(realia_repository, bibliography_repository, entry)


def test_list_returns_sorted_ids(
    realia_repository: MongoRealiaRepository,
    bibliography_repository: BibliographyRepository,
    client,
) -> None:
    for identifier in ("Pig", "Anu", "Enlil, Ellil"):
        _seed_entry(realia_repository, bibliography_repository, id=identifier)

    result = client.simulate_get(LIST_ROUTE)

    assert result.status == falcon.HTTP_OK
    assert result.json == ["Anu", "Enlil, Ellil", "Pig"]


def test_list_empty_collection(client) -> None:
    result = client.simulate_get(LIST_ROUTE)

    assert result.status == falcon.HTTP_OK
    assert result.json == []


def test_list_sets_public_cache_control(
    realia_repository: MongoRealiaRepository,
    bibliography_repository: BibliographyRepository,
    client,
) -> None:
    _seed_entry(realia_repository, bibliography_repository, id="Pig")

    result = client.simulate_get(LIST_ROUTE)

    assert result.headers["Cache-Control"] == f"public, max-age={DEFAULT_TIMEOUT}"


def test_list_returns_ids_verbatim(
    realia_repository: MongoRealiaRepository,
    bibliography_repository: BibliographyRepository,
    client,
) -> None:
    _seed_entry(realia_repository, bibliography_repository, id="(Heiliger) Hügel")

    result = client.simulate_get(LIST_ROUTE)

    assert result.status == falcon.HTTP_OK
    assert result.json == ["(Heiliger) Hügel"]


def test_list_excludes_reserved_identifiers(
    realia_repository: MongoRealiaRepository,
    bibliography_repository: BibliographyRepository,
    client,
) -> None:
    for identifier in (*RESERVED_REALIA_IDS, "Anu"):
        _seed_entry(realia_repository, bibliography_repository, id=identifier)

    result = client.simulate_get(LIST_ROUTE)

    assert result.json == ["Anu"]


def test_every_listed_id_is_retrievable(
    realia_repository: MongoRealiaRepository,
    bibliography_repository: BibliographyRepository,
    client,
) -> None:
    for identifier in (*RESERVED_REALIA_IDS, "Anu", "(Heiliger) Hügel"):
        _seed_entry(realia_repository, bibliography_repository, id=identifier)

    listed_identifiers = client.simulate_get(LIST_ROUTE).json

    for identifier in listed_identifiers:
        entry = client.simulate_get(f"/realia/{identifier}")
        assert entry.status == falcon.HTTP_OK
        assert entry.json["_id"] == identifier
