import pytest

from ebl.common.query.query_result import (
    AfORegisterToFragmentQueryResult,
    CorpusQueryResult,
    QueryResult,
)
from ebl.common.query.query_schemas import (
    AfORegisterToFragmentQueryResultSchema,
    CorpusQueryResultSchema,
)
from ebl.fragmentarium.domain.fragment_query_summary import FragmentQueryResult


@pytest.mark.parametrize(
    "factory", [QueryResult, FragmentQueryResult], ids=["lean", "summary"]
)
def test_document_total_is_part_of_result_value(
    factory: type[QueryResult] | type[FragmentQueryResult],
) -> None:
    first = factory([], 0, total_documents=1)
    same = factory([], 0, total_documents=1)
    different = factory([], 0, total_documents=2)
    unknown = factory([], 0)

    assert first == same
    assert first != different
    assert different != first
    assert first != unknown
    assert unknown != first


def test_result_types_share_the_same_document_identity_contract() -> None:
    lean = QueryResult([], 0, total_documents=3)
    summary = FragmentQueryResult([], 0, total_documents=3)
    different = FragmentQueryResult([], 0, total_documents=4)

    assert lean == summary
    assert summary == lean
    assert lean != different
    assert different != lean


def test_shared_result_schemas_keep_non_library_empty_contracts() -> None:
    assert AfORegisterToFragmentQueryResultSchema().dump(
        AfORegisterToFragmentQueryResult.create_empty()
    ) == {"items": []}
    assert CorpusQueryResultSchema().dump(CorpusQueryResult.create_empty()) == {
        "items": [],
        "matchCountTotal": 0,
    }
