import falcon

from ebl.bibliography.application.bibliography_repository import BibliographyRepository
from ebl.realia.domain.realia_entry import RealiaEntry
from ebl.realia.infrastructure.mongo_realia_repository import MongoRealiaRepository
from ebl.tests.factories.realia import RealiaEntryFactory
from ebl.tests.realia.realia_repository_helpers import create_entry_with_bibliography


def _seed_entry(
    realia_repository: MongoRealiaRepository,
    bibliography_repository: BibliographyRepository,
    **kwargs,
) -> RealiaEntry:
    entry = RealiaEntryFactory.build(**kwargs)
    create_entry_with_bibliography(realia_repository, bibliography_repository, entry)
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


def test_get_realia_surfaces_wikidata_id(
    realia_repository: MongoRealiaRepository,
    bibliography_repository: BibliographyRepository,
    client,
) -> None:
    entry = _seed_entry(
        realia_repository, bibliography_repository, wikidata_id=("Q221574",)
    )

    result = client.simulate_get(f"/realia/{entry.id}")

    assert result.status == falcon.HTTP_OK
    assert result.json["wikidataId"] == ["Q221574"]


def test_get_realia_not_found(client) -> None:
    result = client.simulate_get("/realia/nonexistent")

    assert result.status == falcon.HTTP_NOT_FOUND


def test_get_realia_surfaces_cross_references(
    realia_repository: MongoRealiaRepository,
    bibliography_repository: BibliographyRepository,
    client,
) -> None:
    entry = _seed_entry(realia_repository, bibliography_repository)

    result = client.simulate_get(f"/realia/{entry.id}")

    assert result.status == falcon.HTTP_OK
    body = result.json
    assert body["realiaId"] == entry.realia_id
    assert body["crossReferences"] == [
        {"id": cross.id, "lemma": cross.lemma} for cross in entry.cross_references
    ]
    assert body["afoCrossReferences"] == [
        {
            "id": cross.id,
            "lemma": cross.lemma,
            "afoVolume": cross.afo_volume,
            "page": cross.page,
        }
        for cross in entry.afo_cross_references
    ]
    assert body["afoRegister"][0]["crossReferences"] == [
        {
            "id": cross.id,
            "lemma": cross.lemma,
            "afoVolume": cross.afo_volume,
            "page": cross.page,
        }
        for cross in entry.afo_register[0].cross_references
    ]


def test_get_realia_by_realia_id(
    realia_repository: MongoRealiaRepository,
    bibliography_repository: BibliographyRepository,
    client,
) -> None:
    _seed_entry(
        realia_repository,
        bibliography_repository,
        id="Elam (Geschichte)",
        realia_id="realia_003277",
    )

    result = client.simulate_get("/realia/by-id/realia_003277")

    assert result.status == falcon.HTTP_OK
    assert result.json["_id"] == "Elam (Geschichte)"
    assert result.json["realiaId"] == "realia_003277"


def test_get_realia_by_realia_id_not_found(client) -> None:
    result = client.simulate_get("/realia/by-id/realia_999999")

    assert result.status == falcon.HTTP_NOT_FOUND


def test_lemma_named_by_id_is_not_shadowed(
    realia_repository: MongoRealiaRepository,
    bibliography_repository: BibliographyRepository,
    client,
) -> None:
    _seed_entry(realia_repository, bibliography_repository, id="by-id")

    result = client.simulate_get("/realia/by-id")

    assert result.status == falcon.HTTP_OK
    assert result.json["_id"] == "by-id"


def test_get_realia_with_slash_in_id(
    realia_repository: MongoRealiaRepository,
    bibliography_repository: BibliographyRepository,
    client,
) -> None:
    _seed_entry(realia_repository, bibliography_repository, id="Ninurta/Ninĝirsu")

    result = client.simulate_get("/realia/Ninurta/Ninĝirsu")

    assert result.status == falcon.HTTP_OK
    assert result.json["_id"] == "Ninurta/Ninĝirsu"


def test_get_realia_with_slash_in_id_not_found(client) -> None:
    result = client.simulate_get("/realia/missing/nested")

    assert result.status == falcon.HTTP_NOT_FOUND


def test_realia_lemma_sink_rejects_non_get(client) -> None:
    result = client.simulate_post("/realia/Ninurta/Ninĝirsu")

    assert result.status == falcon.HTTP_METHOD_NOT_ALLOWED
    assert "GET" in result.headers["Allow"]


def test_realia_lemma_sink_allows_cors_preflight(client) -> None:
    result = client.simulate_options(
        "/realia/Ninurta/Ninĝirsu",
        headers={
            "Origin": "https://www.ebl.lmu.de",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert result.status == falcon.HTTP_OK
    assert "GET" in result.headers["Access-Control-Allow-Methods"]
    assert result.headers["Access-Control-Allow-Origin"] == "*"


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


def test_list_non_redirect_ids_returns_sorted_ids(
    realia_repository: MongoRealiaRepository,
    bibliography_repository: BibliographyRepository,
    client,
) -> None:
    for identifier in ("Pig", "Anu", "Enlil, Ellil"):
        _seed_entry(realia_repository, bibliography_repository, id=identifier)

    result = client.simulate_get("/realia/all")

    assert result.status == falcon.HTTP_OK
    assert result.json == ["Anu", "Enlil, Ellil", "Pig"]


def test_list_non_redirect_ids_is_not_shadowed_by_id(client) -> None:
    result = client.simulate_get("/realia/all")

    assert result.status == falcon.HTTP_OK
    assert result.json == []


def test_list_non_redirect_ids_shadows_entry_named_all(
    realia_repository: MongoRealiaRepository,
    bibliography_repository: BibliographyRepository,
    client,
) -> None:
    for identifier in ("all", "Pig"):
        _seed_entry(realia_repository, bibliography_repository, id=identifier)

    result = client.simulate_get("/realia/all")

    assert result.status == falcon.HTTP_OK
    assert result.json == ["Pig", "all"]


def test_list_non_redirect_ids_returns_ids_verbatim(
    realia_repository: MongoRealiaRepository,
    bibliography_repository: BibliographyRepository,
    client,
) -> None:
    _seed_entry(realia_repository, bibliography_repository, id="(Heiliger) Hügel")

    result = client.simulate_get("/realia/all")

    assert result.status == falcon.HTTP_OK
    assert "(Heiliger) Hügel" in result.json
