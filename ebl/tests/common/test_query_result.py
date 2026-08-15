from ebl.common.query.query_result import QueryResult
from ebl.common.query.query_schemas import QueryResultSchema


def test_query_result_equality_with_unsupported_type_returns_not_implemented():
    result = QueryResult.create_empty()

    assert result.__eq__(object()) is NotImplemented


def test_query_result_schema_can_include_count_metadata():
    assert QueryResultSchema(include_count_metadata=True).dump(
        QueryResult.create_empty()
    ) == {
        "items": [],
        "matchCountTotal": 0,
        "isMatchCountTotalExact": True,
        "hasNextPage": None,
    }
