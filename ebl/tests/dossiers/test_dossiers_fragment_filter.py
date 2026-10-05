import falcon

from ebl.tests.factories.dossier import DossierRecordFactory


def create_dossiers(dossiers_repository, *ids: str) -> None:
    for id_ in ids:
        dossiers_repository.create(DossierRecordFactory.build(id=id_, references=()))


def test_multi_part_genre_collects_every_dossier_reference_shape(
    dossiers_repository, database
):
    create_dossiers(dossiers_repository, "D1", "D2", "D3")
    database["fragments"].insert_many(
        [
            {
                "_id": "X.1",
                "genres": [{"category": ["CANONICAL", "Divination"]}],
                "dossiers": [{"dossierId": "D1"}, "D2", 7, {"dossierId": None}],
            },
            {
                "_id": "X.2",
                "genres": [{"category": ["CANONICAL", "Literature"]}],
                "dossiers": [{"dossierId": "D3"}],
            },
        ]
    )

    result = dossiers_repository.filter_by_fragment_criteria(
        genre="CANONICAL:Divination"
    )

    assert sorted(dossier.id for dossier in result) == ["D1", "D2"]


def test_filter_without_matching_fragments_returns_no_dossiers(dossiers_repository):
    create_dossiers(dossiers_repository, "D1")

    assert dossiers_repository.filter_by_fragment_criteria(genre="Unknown") == []


def test_filter_failure_returns_no_dossiers(dossiers_repository, when):
    create_dossiers(dossiers_repository, "D1")
    (
        when(dossiers_repository._fragments_collection)
        .find_many(...)
        .thenRaise(RuntimeError("fragment query failed"))
    )

    assert dossiers_repository.filter_by_fragment_criteria(provenance="Babylon") == []


def test_invalid_dossier_ids_are_not_found(client, dossiers_repository, when):
    when(dossiers_repository).query_by_ids(...).thenRaise(ValueError("invalid"))

    result = client.simulate_get("/dossiers", query_string="ids[]=D1")

    assert result.status == falcon.HTTP_NOT_FOUND
