import falcon
from ebl.fragmentarium.application.archaeology_schemas import FindspotSchema


def test_fetch_all_findspots(client, findspot_repository, findspots):
    for findspot in findspots:
        findspot_repository.create(findspot)

    result = client.simulate_get("/findspots")
    expected = FindspotSchema().dump(findspots, many=True)

    assert result.json == expected
    assert result.status == falcon.HTTP_OK
