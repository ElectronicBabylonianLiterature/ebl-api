from ebl.common.query.query_result import QueryItem, QueryResult
from ebl.fragmentarium.domain.archaeology import Archaeology
from ebl.tests.factories.fragment import FragmentFactory
from ebl.transliteration.domain.museum_number import MuseumNumber


def test_query_fragmentarium_findspot_id(fragment_repository):
    matching = FragmentFactory.build(
        number=MuseumNumber.of("X.1"),
        archaeology=Archaeology(findspot_id=123),
    )
    other = FragmentFactory.build(
        number=MuseumNumber.of("X.2"),
        archaeology=Archaeology(findspot_id=456),
    )
    fragment_repository.create_many([matching, other])

    assert fragment_repository.query({"findspotId": 123}) == QueryResult(
        [QueryItem(matching.number, (), 0)],
        0,
    )
