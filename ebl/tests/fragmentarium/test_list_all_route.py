import falcon
from ebl.tests.factories.fragment import FragmentFactory


def test_list_all_fragments(client, fragment_repository):
    fragment = FragmentFactory.build()
    fragment_repository.create(fragment)

    get_result = client.simulate_get("/fragments/all")

    assert get_result.status == falcon.HTTP_OK
    assert get_result.json == [str(fragment.number)]
