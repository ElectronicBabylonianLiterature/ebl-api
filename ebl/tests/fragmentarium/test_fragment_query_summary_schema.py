from ebl.bibliography.application.reference_schema import ReferenceSchema
from ebl.common.application.schemas import AccessionSchema
from ebl.common.domain.project import ResearchProject
from ebl.common.query.query_result import QueryItem, QueryResult
from ebl.fragmentarium.application.fragment_fields_schemas import (
    DossierReferenceSchema,
)
from ebl.fragmentarium.application.fragment_query_summary_schema import (
    FragmentQueryArchaeologySchema,
    FragmentQueryMatchingLinePreviewSchema,
    FragmentQueryResultSchema,
    FragmentQuerySummarySchema,
)
from ebl.fragmentarium.application.genre_schema import GenreSchema
from ebl.fragmentarium.domain.date import DateSchema
from ebl.fragmentarium.domain.fragment_query_summary import (
    FragmentQueryArchaeology,
    FragmentQueryResult,
    FragmentQuerySummary,
    matching_line_preview_of,
)
from ebl.schemas import ResearchProjectField
from ebl.tests.factories.bibliography import ReferenceFactory
from ebl.tests.factories.fragment import (
    FragmentDossierReferenceFactory,
    TransliteratedFragmentFactory,
)
from ebl.transliteration.application.museum_number_schema import MuseumNumberSchema


def build_summary() -> FragmentQuerySummary:
    fragment = TransliteratedFragmentFactory.build(
        references=(ReferenceFactory.build(), ReferenceFactory.build())
    )
    matching_lines = (0, 2)
    preview = matching_line_preview_of(fragment.text, matching_lines)

    return FragmentQuerySummary(
        museum_number=fragment.number,
        accession=fragment.accession,
        description=fragment.description,
        script=fragment.script,
        date=fragment.date,
        genres=fragment.genres,
        archaeology=FragmentQueryArchaeology(
            excavation_number=MuseumNumberSchema().load(
                MuseumNumberSchema().dump(fragment.archaeology.excavation_number)
            ),
            site=fragment.archaeology.site.long_name,
        ),
        references=fragment.references,
        projects=(ResearchProject.CAIC, ResearchProject.RECC),
        dossiers=(
            FragmentDossierReferenceFactory.build(dossierId="DOS.1", isUncertain=True),
        ),
        matching_lines=matching_lines,
        matching_line_preview=preview,
        match_count=2,
        has_photo=True,
    )


def test_fragment_query_summary_schema_dump_exact_shape():
    summary = build_summary()
    dumped = FragmentQuerySummarySchema().dump(summary)

    assert set(dumped) == {
        "museumNumber",
        "accession",
        "description",
        "script",
        "date",
        "genres",
        "archaeology",
        "references",
        "projects",
        "dossiers",
        "matchingLines",
        "matchingLinePreview",
        "matchCount",
        "hasPhoto",
        "thumbnailPath",
    }
    assert dumped == {
        "museumNumber": MuseumNumberSchema().dump(summary.museum_number),
        "accession": AccessionSchema().dump(summary.accession),
        "description": summary.description,
        "script": {
            "period": summary.script.period.abbreviation,
            "periodModifier": summary.script.period_modifier.value,
            "uncertain": summary.script.uncertain,
        },
        "date": DateSchema().dump(summary.date),
        "genres": GenreSchema().dump(summary.genres, many=True),
        "archaeology": {
            "excavationNumber": MuseumNumberSchema().dump(
                summary.archaeology.excavation_number
            ),
            "site": {"name": summary.archaeology.site},
        },
        "references": ReferenceSchema().dump(summary.references, many=True),
        "projects": [
            ResearchProjectField()._serialize(project, None, None)
            for project in summary.projects
        ],
        "dossiers": DossierReferenceSchema().dump(summary.dossiers, many=True),
        "matchingLines": [0, 2],
        "matchingLinePreview": FragmentQueryMatchingLinePreviewSchema().dump(
            summary.matching_line_preview
        ),
        "matchCount": 2,
        "hasPhoto": True,
        "thumbnailPath": f"/fragments/{summary.museum_number}/thumbnail/small",
    }
    assert (
        dumped["matchingLinePreview"]["lines"][0]["prefix"]
        == (summary.matching_line_preview["lines"][0]["prefix"])
    )
    assert dumped["matchingLinePreview"]["lines"][0]["text"]
    assert dumped["matchingLinePreview"]["lines"][0]["tokens"][0]["value"]
    assert dumped["matchingLinePreview"]["parserVersion"]
    assert "parser_version" not in dumped["matchingLinePreview"]
    assert "parts" not in dumped["matchingLinePreview"]["lines"][0]["tokens"][0]
    assert "text" not in dumped
    assert "record" not in dumped
    assert "atf" not in dumped


def test_fragment_query_summary_schema_roundtrip():
    summary = build_summary()

    assert (
        FragmentQuerySummarySchema().load(FragmentQuerySummarySchema().dump(summary))
        == summary
    )


def test_fragment_query_summary_compares_with_compatible_query_item():
    summary = build_summary()
    item = QueryItem(summary.museum_number, summary.matching_lines, summary.match_count)

    assert summary == item
    assert summary.__eq__(object()) is NotImplemented


def test_fragment_query_archaeology_schema_loads_non_dict_site():
    archaeology = FragmentQueryArchaeologySchema().load({"site": "Nineveh"})

    assert archaeology.site == "Nineveh"


def test_matching_line_preview_skips_out_of_range_lines():
    fragment = TransliteratedFragmentFactory.build()
    line_count = len(fragment.text.lines)

    preview = matching_line_preview_of(fragment.text, (0, line_count))
    empty_preview = matching_line_preview_of(fragment.text, (line_count,))

    assert len(preview["lines"]) == 1
    assert (
        FragmentQueryMatchingLinePreviewSchema().load(
            FragmentQueryMatchingLinePreviewSchema().dump(empty_preview)
        )["lines"]
        == []
    )


def test_fragment_query_result_schema_roundtrip_and_compatibility():
    summary = build_summary()
    result = FragmentQueryResult((summary,), 7)
    dumped = FragmentQueryResultSchema().dump(result)

    assert dumped == {
        "items": [FragmentQuerySummarySchema().dump(summary)],
        "matchCountTotal": 7,
    }
    assert FragmentQueryResultSchema().load(dumped) == result

    old_result = QueryResult(
        [QueryItem(summary.museum_number, summary.matching_lines, summary.match_count)],
        7,
    )
    assert result == old_result
    assert old_result == result

    assert FragmentQueryResultSchema(include_count_metadata=True).dump(result) == {
        "items": [FragmentQuerySummarySchema().dump(summary)],
        "matchCountTotal": 7,
        "isMatchCountTotalExact": True,
        "hasNextPage": None,
    }


def test_fragment_query_result_compatibility_respects_count_metadata():
    summary = build_summary()
    item = QueryItem(summary.museum_number, summary.matching_lines, summary.match_count)
    result = FragmentQueryResult((summary,), None, False, True)
    matching_query_result = QueryResult([item], None, False, True)
    mismatched_query_result = QueryResult([item], None, False, False)

    assert result == matching_query_result
    assert matching_query_result == result
    assert result != mismatched_query_result
