from typing import cast

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
        "totalDocuments": 0,
    }


def test_old_result_payload_remains_loadable() -> None:
    result = cast(
        QueryResult, QueryResultSchema().load({"items": [], "matchCountTotal": 0})
    )
    assert result.total_documents is None
    assert QueryResultSchema().dump(result) == {"items": [], "matchCountTotal": 0}


def test_corpus_result_does_not_gain_library_document_metadata() -> None:
    from ebl.common.query.query_result import CorpusQueryResult
    from ebl.common.query.query_schemas import CorpusQueryResultSchema

    payload = {"items": [], "matchCountTotal": 0}
    assert CorpusQueryResultSchema().load(payload) == CorpusQueryResult([], 0)
    assert CorpusQueryResultSchema(include_count_metadata=True).dump(
        CorpusQueryResult([], 0)
    ) == {
        **payload,
        "isMatchCountTotalExact": True,
        "hasNextPage": None,
        "totalChapters": None,
    }
