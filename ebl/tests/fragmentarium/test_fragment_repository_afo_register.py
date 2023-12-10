from ebl.common.query.query_schemas import (
    AfORegisterToFragmentQueryResultSchema,
)
from ebl.tests.factories.fragment import (
    FragmentFactory,
)


def test_query_fragmentarium_afo_register(fragment_repository):
    fragment = FragmentFactory.build(traditional_references=[])

    # ToDo: Add data to test

    fragment_repository.create_many([fragment, FragmentFactory.build()])

    result = fragment_repository.query_by_traditional_references([])
    assert result == AfORegisterToFragmentQueryResultSchema().load({"items": []})
