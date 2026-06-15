from ebl.common.domain.period import Period
from ebl.common.query.query_result import QueryItem, QueryResult
from ebl.fragmentarium.application.fragment_query_summary_schema import (
    FragmentQueryResultSchema,
    FragmentQuerySummarySchema,
)
from ebl.fragmentarium.domain.fragment import Script
from ebl.fragmentarium.domain.fragment_query_summary import (
    FragmentQueryResult,
    FragmentQuerySummary,
)
from ebl.transliteration.domain.museum_number import MuseumNumber


def build_summary() -> FragmentQuerySummary:
    return FragmentQuerySummary(
        museum_number=MuseumNumber.of("K.1"),
        accession=None,
        description="desc",
        script=Script(Period.OLD_ASSYRIAN),
        matching_lines=(1, 3),
        match_count=2,
        has_photo=True,
    )


def test_fragment_query_summary_schema_dump_is_compact():
    dumped = FragmentQuerySummarySchema().dump(build_summary())

    assert dumped["museumNumber"] == {"prefix": "K", "number": "1", "suffix": ""}
    assert dumped["matchingLines"] == [1, 3]
    assert dumped["matchCount"] == 2
    assert dumped["hasPhoto"] is True
    assert dumped["thumbnailPath"] == "/fragments/K.1/thumbnail/small"
    assert "text" not in dumped
    assert "record" not in dumped


def test_fragment_query_summary_schema_roundtrip():
    summary = build_summary()

    assert FragmentQuerySummarySchema().load(FragmentQuerySummarySchema().dump(summary)) == summary


def test_fragment_query_result_schema_roundtrip_and_compatibility():
    summary = build_summary()
    result = FragmentQueryResult((summary,), 2)
    dumped = FragmentQueryResultSchema().dump(result)

    assert dumped["matchCountTotal"] == 2
    assert dumped["items"][0]["thumbnailPath"] == "/fragments/K.1/thumbnail/small"
    assert FragmentQueryResultSchema().load(dumped) == result

    old_result = QueryResult([QueryItem(summary.museum_number, summary.matching_lines, 2)], 2)
    assert result == old_result
    assert old_result == result
