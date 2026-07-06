from typing import Dict, List, Optional
from datetime import date, timedelta

import attr
import falcon
import pytest
from ebl.common.domain.period import Period, PeriodModifier
from ebl.common.domain.project import ResearchProject

from ebl.fragmentarium.application.fragment_info_schema import (
    ApiFragmentInfoSchema,
    ApiFragmentInfosPaginationSchema,
)
from ebl.fragmentarium.application.fragment_query_summary_schema import (
    FragmentQuerySummarySchema,
)
from ebl.fragmentarium.application.fragment_fields_schemas import (
    DossierReferenceSchema,
)
from ebl.fragmentarium.domain.fragment_query_summary import (
    FragmentQueryArchaeology,
    FragmentQuerySummary,
    matching_line_preview_of,
)
from ebl.fragmentarium.domain.fragment import Fragment, Genre, Script
from ebl.fragmentarium.domain.fragment_info import FragmentInfo
from ebl.fragmentarium.domain.fragment_infos_pagination import FragmentInfosPagination
from ebl.fragmentarium.domain.museum import Museum
from ebl.fragmentarium.domain.record import RecordType
from ebl.fragmentarium.infrastructure.queries import (
    LATEST_TRANSLITERATION_LIMIT,
    LATEST_TRANSLITERATION_LINE_LIMIT,
)
from ebl.tests.factories.bibliography import ReferenceFactory, BibliographyEntryFactory

from ebl.tests.factories.fragment import (
    FragmentFactory,
    InterestingFragmentFactory,
    TransliteratedFragmentFactory,
    LemmatizedFragmentFactory,
)
from ebl.tests.factories.record import RecordEntryFactory, RecordFactory
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.application.museum_number_schema import MuseumNumberSchema
from ebl.transliteration.domain.sign import Sign, Value
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.word_tokens import Word
from ebl.fragmentarium.domain.genres import genres
from ebl.common.domain.scopes import Scope
from ebl.tests.factories.provenance import build_provenance_records


def get_provenance_record(record_id: str):
    return next(
        record for record in build_provenance_records() if record.id == record_id
    )


def expected_fragment_info_dto(fragment: Fragment, text=None) -> Dict:
    return ApiFragmentInfoSchema().dump(FragmentInfo.of(fragment, text))


def expected_fragment_infos_pagination_dto(
    fragment_infos_pagination: FragmentInfosPagination,
) -> Dict:
    return ApiFragmentInfosPaginationSchema().dump(fragment_infos_pagination)


def query_item_of(
    fragment: Fragment,
    matching_lines: Optional[List[int]] = None,
    match_count: Optional[int] = None,
) -> Dict:
    lines = [] if matching_lines is None else matching_lines

    return {
        "museumNumber": MuseumNumberSchema().dump(fragment.number),
        "matchingLines": lines,
        "matchCount": len(lines) if match_count is None else match_count,
    }


def query_result_of(
    items: List[Dict],
    match_count_total: Optional[int],
    is_match_count_total_exact: bool = True,
    has_next_page: Optional[bool] = None,
) -> Dict:
    return {
        "items": items,
        "matchCountTotal": match_count_total,
        "isMatchCountTotalExact": is_match_count_total_exact,
        "hasNextPage": has_next_page,
    }


def query_summary_of(
    fragment: Fragment,
    matching_lines: Optional[List[int]] = None,
    match_count: Optional[int] = None,
    has_photo: bool = False,
) -> Dict:
    lines = [] if matching_lines is None else matching_lines
    archaeology = (
        FragmentQueryArchaeology(
            excavation_number=fragment.archaeology.excavation_number,
            site=(
                fragment.archaeology.site.long_name
                if fragment.archaeology.site
                else None
            ),
        )
        if fragment.archaeology is not None
        else None
    )
    preview = matching_line_preview_of(fragment.text, lines)

    return FragmentQuerySummarySchema().dump(
        FragmentQuerySummary(
            museum_number=fragment.number,
            accession=fragment.accession,
            description=fragment.description,
            script=fragment.script,
            date=fragment.date,
            genres=fragment.genres,
            archaeology=archaeology,
            references=fragment.references,
            projects=tuple(
                project
                if isinstance(project, ResearchProject)
                else ResearchProject.from_abbreviation(str(project))
                for project in fragment.projects
            ),
            dossiers=tuple(
                DossierReferenceSchema().load(DossierReferenceSchema().dump(dossier))
                for dossier in fragment.dossiers
            ),
            matching_lines=tuple(lines),
            matching_line_preview=preview,
            match_count=len(lines) if match_count is None else match_count,
            has_photo=has_photo,
        )
    )


@pytest.mark.parametrize(
    "get_number",
    [
        lambda fragment: str(fragment.number),
        lambda fragment: fragment.cdli_number,
        lambda fragment: str(fragment.accession),
        lambda fragment: str(fragment.archaeology.excavation_number),
    ],
)
def test_query_fragmentarium_number(get_number, client, fragmentarium):
    fragment = FragmentFactory.build()
    fragmentarium.create(fragment)
    result = client.simulate_get(
        "/fragments/query",
        params={
            "number": get_number(fragment),
        },
    )

    assert result.status == falcon.HTTP_OK
    assert result.json == query_result_of([query_item_of(fragment)], 0)


def test_query_fragmentarium_number_summary_only(client, fragmentarium):
    fragment = FragmentFactory.build(number=MuseumNumber.of("K.1"))
    fragmentarium.create(fragment)
    result = client.simulate_get(
        "/fragments/query",
        params={"number": str(fragment.number), "limit": "1"},
    )

    assert result.status == falcon.HTTP_OK
    assert result.json == query_result_of(
        [query_summary_of(fragment, has_photo=True)], 0
    )
    assert result.json["items"][0]["matchingLinePreview"]["lines"] == []
    assert result.json["items"][0]["matchingLinePreview"]["parserVersion"] is not None
    assert "text" not in result.json["items"][0]
    assert "record" not in result.json["items"][0]
    assert "atf" not in result.json["items"][0]


def test_query_fragmentarium_number_not_found(client):
    result = client.simulate_get(
        "/fragments/query",
        params={"number": "K.1"},
    )

    assert result.json == query_result_of([], 0)


def test_query_fragmentarium_empty_query_includes_count_metadata(client):
    result = client.simulate_get("/fragments/query")

    assert result.status == falcon.HTTP_OK
    assert result.json == query_result_of([], 0)


def test_query_fragmentarium_pagination_index_only_matches_empty_query(client):
    result = client.simulate_get("/fragments/query", params={"paginationIndex": 999})

    assert result.status == falcon.HTTP_OK
    assert result.json == query_result_of([], 0)


def test_query_fragmentarium_references(client, fragmentarium, bibliography, user):
    bib_entry_1 = BibliographyEntryFactory.build(id="RN.0", pages="254")
    bib_entry_2 = BibliographyEntryFactory.build(id="RN.1")
    bibliography.create(bib_entry_1, user)
    bibliography.create(bib_entry_2, user)

    fragment = FragmentFactory.build(
        references=(
            ReferenceFactory.build(id="RN.0", pages="254"),
            ReferenceFactory.build(id="RN.1"),
        )
    )
    fragmentarium.create(fragment)
    result = client.simulate_get(
        "/fragments/query",
        params={
            "bibId": fragment.references[0].id,
            "pages": fragment.references[0].pages,
        },
    )

    assert result.status == falcon.HTTP_OK
    assert result.json == query_result_of([query_item_of(fragment)], 0)


def test_query_fragmentarium_transliteration(
    client, fragmentarium, sign_repository, signs
):
    transliterated_fragments = [
        TransliteratedFragmentFactory.build(
            number=MuseumNumber.of("X.123"), script=Script(Period.MIDDLE_ASSYRIAN)
        ),
        TransliteratedFragmentFactory.build(
            number=MuseumNumber.of("X.5"), script=Script(Period.LATE_BABYLONIAN)
        ),
        TransliteratedFragmentFactory.build(
            number=MuseumNumber.of("X.42"), script=Script(Period.LATE_BABYLONIAN)
        ),
    ]
    for index, fragment in enumerate(transliterated_fragments):
        fragmentarium.create(fragment, sort_key=index)

    for sign in signs:
        sign_repository.create(sign)

    result = client.simulate_get(
        "/fragments/query",
        params={"transliteration": "ma-tu₂"},
    )

    assert result.status == falcon.HTTP_OK
    assert result.json == query_result_of(
        [
            query_item_of(fragment, matching_lines=[3])
            for fragment in transliterated_fragments
        ],
        3,
    )
    assert "matchingLinePreview" not in result.json["items"][0]
    assert "hasPhoto" not in result.json["items"][0]
    assert "thumbnailPath" not in result.json["items"][0]
    assert "text" not in result.json["items"][0]
    assert "record" not in result.json["items"][0]
    assert "atf" not in result.json["items"][0]


def test_query_fragmentarium_transliteration_limit_preserves_total_count(
    client, fragmentarium, sign_repository, signs
):
    transliterated_fragments = [
        TransliteratedFragmentFactory.build(
            number=MuseumNumber.of(f"X.{index}"),
            script=Script(Period.LATE_BABYLONIAN),
        )
        for index in range(5)
    ]

    for fragment in transliterated_fragments:
        fragmentarium.create(fragment)

    for sign in signs:
        sign_repository.create(sign)

    result = client.simulate_get(
        "/fragments/query",
        params={"transliteration": "ma-tu₂", "limit": "2"},
    )

    assert result.status == falcon.HTTP_OK
    assert len(result.json["items"]) == 2
    assert result.json["matchCountTotal"] == 5
    assert result.json["isMatchCountTotalExact"] is True
    assert result.json["hasNextPage"] is None


def test_query_fragmentarium_transliteration_count_exact(
    client, fragmentarium, sign_repository, signs
):
    transliterated_fragments = [
        TransliteratedFragmentFactory.build(
            number=MuseumNumber.of(f"X.{index}"),
            script=Script(Period.LATE_BABYLONIAN),
        )
        for index in range(3)
    ]

    for fragment in transliterated_fragments:
        fragmentarium.create(fragment)

    for sign in signs:
        sign_repository.create(sign)

    result = client.simulate_get(
        "/fragments/query",
        params={"transliteration": "ma-tu₂", "limit": "2", "count": "exact"},
    )

    assert result.status == falcon.HTTP_OK
    assert result.json["matchCountTotal"] == 3
    assert result.json["isMatchCountTotalExact"] is True
    assert result.json["hasNextPage"] is None


def test_query_fragmentarium_transliteration_count_none(
    client, fragmentarium, sign_repository, signs
):
    transliterated_fragments = [
        TransliteratedFragmentFactory.build(
            number=MuseumNumber.of(f"X.{index}"),
            script=Script(Period.LATE_BABYLONIAN),
        )
        for index in range(3)
    ]

    for fragment in transliterated_fragments:
        fragmentarium.create(fragment)

    for sign in signs:
        sign_repository.create(sign)

    result = client.simulate_get(
        "/fragments/query",
        params={"transliteration": "ma-tu₂", "limit": "2", "count": "none"},
    )

    assert result.status == falcon.HTTP_OK
    assert len(result.json["items"]) == 2
    assert result.json["matchCountTotal"] is None
    assert result.json["isMatchCountTotalExact"] is False
    assert result.json["hasNextPage"] is None


def test_query_fragmentarium_transliteration_count_page(
    client, fragmentarium, sign_repository, signs
):
    transliterated_fragments = [
        TransliteratedFragmentFactory.build(
            number=MuseumNumber.of(f"X.{index}"),
            script=Script(Period.LATE_BABYLONIAN),
        )
        for index in range(3)
    ]

    for index, fragment in enumerate(transliterated_fragments):
        fragmentarium.create(fragment, sort_key=index)

    for sign in signs:
        sign_repository.create(sign)

    result = client.simulate_get(
        "/fragments/query",
        params={"transliteration": "ma-tu₂", "limit": "2", "count": "page"},
    )
    last_page_result = client.simulate_get(
        "/fragments/query",
        params={
            "transliteration": "ma-tu₂",
            "limit": "2",
            "offset": "2",
            "count": "page",
        },
    )

    assert result.status == falcon.HTTP_OK
    assert result.json == query_result_of(
        [
            query_summary_of(fragment, matching_lines=[3])
            for fragment in transliterated_fragments[:2]
        ],
        None,
        False,
        True,
    )
    assert last_page_result.status == falcon.HTTP_OK
    assert last_page_result.json == query_result_of(
        [query_summary_of(transliterated_fragments[2], matching_lines=[3])],
        None,
        False,
        False,
    )


def test_query_fragmentarium_transliteration_limit_with_offset(
    client, fragmentarium, sign_repository, signs
):
    transliterated_fragments = [
        TransliteratedFragmentFactory.build(
            number=MuseumNumber.of(f"X.{index}"),
            script=Script(Period.LATE_BABYLONIAN),
        )
        for index in range(4)
    ]

    for index, fragment in enumerate(transliterated_fragments):
        fragmentarium.create(fragment, sort_key=index)

    for sign in signs:
        sign_repository.create(sign)

    result = client.simulate_get(
        "/fragments/query",
        params={"transliteration": "ma-tu₂", "limit": "2", "offset": "1"},
    )

    assert result.status == falcon.HTTP_OK
    assert result.json == query_result_of(
        [
            query_summary_of(fragment, matching_lines=[3])
            for fragment in transliterated_fragments[1:3]
        ],
        4,
    )
    assert result.json["items"][0]["matchingLinePreview"]["parserVersion"] is not None


def test_query_fragmentarium_transliteration_offset_without_limit_returns_lean_items(
    client, fragmentarium, sign_repository, signs
):
    transliterated_fragments = [
        TransliteratedFragmentFactory.build(
            number=MuseumNumber.of(f"X.{index}"),
            script=Script(Period.LATE_BABYLONIAN),
        )
        for index in range(4)
    ]

    for index, fragment in enumerate(transliterated_fragments):
        fragmentarium.create(fragment, sort_key=index)

    for sign in signs:
        sign_repository.create(sign)

    result = client.simulate_get(
        "/fragments/query",
        params={"transliteration": "ma-tu₂", "offset": "2"},
    )

    assert result.status == falcon.HTTP_OK
    assert result.json == query_result_of(
        [
            query_item_of(fragment, matching_lines=[3])
            for fragment in transliterated_fragments[2:]
        ],
        4,
    )


def test_query_fragmentarium_transliteration_offset_zero_is_accepted(
    client, fragmentarium, sign_repository, signs
):
    fragment = TransliteratedFragmentFactory.build(
        number=MuseumNumber.of("X.0"),
        script=Script(Period.LATE_BABYLONIAN),
    )
    fragmentarium.create(fragment)

    for sign in signs:
        sign_repository.create(sign)

    result = client.simulate_get(
        "/fragments/query",
        params={"transliteration": "ma-tu₂", "limit": "1", "offset": "0"},
    )

    assert result.status == falcon.HTTP_OK
    assert result.json == query_result_of(
        [query_summary_of(fragment, matching_lines=[3])], 1
    )


@pytest.mark.parametrize("offset", ["invalid", "-1"])
def test_query_fragmentarium_offset_invalid(client, offset):
    result = client.simulate_get(
        "/fragments/query",
        params={"number": "K.1", "offset": offset},
    )

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


@pytest.mark.parametrize("count", ["false", "0", "random", "approx"])
def test_query_fragmentarium_count_invalid(client, count):
    result = client.simulate_get(
        "/fragments/query",
        params={"number": "K.1", "count": count},
    )

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_query_fragmentarium_transliteration_without_limit_returns_all_lean_items(
    client, fragmentarium, sign_repository, signs
):
    transliterated_fragments = [
        TransliteratedFragmentFactory.build(
            number=MuseumNumber.of(f"X.{index}"),
            script=Script(Period.LATE_BABYLONIAN),
        )
        for index in range(101)
    ]

    for fragment in transliterated_fragments:
        fragmentarium.create(fragment)

    for sign in signs:
        sign_repository.create(sign)

    result = client.simulate_get(
        "/fragments/query",
        params={"transliteration": "ma-tu₂"},
    )

    assert result.status == falcon.HTTP_OK
    assert len(result.json["items"]) == 101
    assert result.json["matchCountTotal"] == 101
    assert "matchingLinePreview" not in result.json["items"][0]


def test_query_fragmentarium_kur2_transliteration_returns_summary(
    client, fragmentarium, sign_repository
):
    fragment = TransliteratedFragmentFactory.build(
        number=MuseumNumber.of("X.4936"),
        signs="KUR₂",
        text=Text(
            (
                TextLine.of_iterable(
                    LineNumber(1), (Word.of([Reading.of_name("kur", 2)]),)
                ),
            )
        ),
    )
    fragmentarium.create(fragment)
    sign_repository.create(Sign("KUR₂", values=(Value("kur", 2),)))

    result = client.simulate_get(
        "/fragments/query",
        params={"transliteration": "kur₂", "limit": "1"},
    )

    assert result.status == falcon.HTTP_OK
    assert result.json == query_result_of(
        [query_summary_of(fragment, matching_lines=[0])], 1
    )
    assert result.json["items"][0]["matchingLinePreview"]["parserVersion"] is not None
    assert "description" in result.json["items"][0]
    assert "script" in result.json["items"][0]
    assert "hasPhoto" in result.json["items"][0]
    preview_line = result.json["items"][0]["matchingLinePreview"]["lines"][0]
    assert preview_line["text"] == "kur₂"
    assert preview_line["tokens"][0]["value"] == "kur₂"
    assert preview_line["tokens"][0]["cleanValue"] == "kur₂"
    assert preview_line["tokens"][0]["type"] == "Word"
    assert "parts" not in preview_line["tokens"][0]


@pytest.mark.parametrize(
    "lemma_operator,lemmas,expected_lines",
    [
        ("and", "ana I+ginâ I", [1]),
        ("or", "ginâ I+bamātu I+mu I", [1, 2, 3]),
        ("line", "u I+kīdu I", [2]),
        ("phrase", "mu I+tamalāku I", [3]),
    ],
)
def test_query_fragmentarium_lemmas(
    client, fragmentarium, lemma_operator, lemmas, expected_lines
):
    fragment = LemmatizedFragmentFactory.build()
    fragmentarium.create(fragment)

    result = client.simulate_get(
        "/fragments/query",
        params={"lemmaOperator": lemma_operator, "lemmas": lemmas},
    )

    assert result.status == falcon.HTTP_OK
    assert result.json == query_result_of(
        [query_item_of(fragment, matching_lines=expected_lines)],
        len(expected_lines),
    )


def test_query_fragmentarium_lemmas_not_found(client, fragmentarium):
    fragment = LemmatizedFragmentFactory.build()
    fragmentarium.create(fragment)

    result = client.simulate_get(
        "/fragments/query",
        params={"lemmaOperator": "phrase", "lemmas": "u I+u I+u I"},
    )
    assert result.status == falcon.HTTP_OK
    assert result.json == query_result_of([], 0)


def test_query_fragmentarium_combined_query(
    client, fragmentarium, sign_repository, signs, bibliography, user
):
    bib_entry_1 = BibliographyEntryFactory.build(id="RN.0", pages="254")
    bib_entry_2 = BibliographyEntryFactory.build(id="RN.1")
    bibliography.create(bib_entry_1, user)
    bibliography.create(bib_entry_2, user)

    fragment = LemmatizedFragmentFactory.build(
        references=(
            ReferenceFactory.build(id="RN.0", pages="254"),
            ReferenceFactory.build(id="RN.1"),
        )
    )
    fragmentarium.create(fragment)

    for sign in signs:
        sign_repository.create(sign)

    result = client.simulate_get(
        "/fragments/query",
        params={
            "number": str(fragment.number),
            "transliteration": "ma-tu₂",
            "bibId": fragment.references[0].id,
            "pages": fragment.references[0].pages,
            "lemmas": "ana I+mu I",
            "lemmaOperator": "or",
        },
    )

    assert result.status == falcon.HTTP_OK

    assert result.json == query_result_of(
        [query_item_of(fragment, matching_lines=[1, 3])], 2
    )


def test_query_fragmentarium_ignores_pagination_index(client, fragmentarium):
    genre = Genre(["CANONICAL", "Technical"], False)
    fragments = FragmentFactory.build_batch(2, genres=(genre,), script=Script())
    for index, fragment in enumerate(fragments):
        fragmentarium.create(fragment, sort_key=index)

    result = client.simulate_get(
        "/fragments/query",
        params={"genre": ":".join(genre.category), "paginationIndex": 999},
    )

    assert result.status == falcon.HTTP_OK
    assert result.json == query_result_of(
        [query_item_of(fragment) for fragment in fragments],
        0,
    )


def test_query_fragmentarium_limit_only_uses_no_filter_pagination(
    client, fragmentarium
):
    fragments = [
        FragmentFactory.build(number=MuseumNumber.of(f"X.{index}"), script=Script())
        for index in range(3)
    ]
    for index, fragment in enumerate(fragments):
        fragmentarium.create(fragment, sort_key=index)

    result = client.simulate_get("/fragments/query", params={"limit": "2"})

    assert result.status == falcon.HTTP_OK
    assert [item["museumNumber"] for item in result.json["items"]] == [
        MuseumNumberSchema().dump(fragment.number) for fragment in fragments[:2]
    ]
    assert result.json["matchCountTotal"] == 0
    assert result.json["isMatchCountTotalExact"] is True
    assert result.json["hasNextPage"] is None
    assert "matchingLinePreview" in result.json["items"][0]


def test_query_fragmentarium_offset_only_uses_no_filter_pagination(
    client, fragmentarium
):
    fragments = [
        FragmentFactory.build(number=MuseumNumber.of(f"X.{index}"), script=Script())
        for index in range(4)
    ]
    for index, fragment in enumerate(fragments):
        fragmentarium.create(fragment, sort_key=index)

    result = client.simulate_get("/fragments/query", params={"offset": "1"})

    assert result.status == falcon.HTTP_OK
    assert result.json == query_result_of(
        [query_item_of(fragment) for fragment in fragments[1:]],
        0,
    )
    assert "matchingLinePreview" not in result.json["items"][0]


def test_query_fragmentarium_count_page_without_limit_uses_no_filter_items(
    client, fragmentarium
):
    fragments = [
        FragmentFactory.build(number=MuseumNumber.of(f"X.{index}"), script=Script())
        for index in range(3)
    ]
    for index, fragment in enumerate(fragments):
        fragmentarium.create(fragment, sort_key=index)

    result = client.simulate_get("/fragments/query", params={"count": "page"})

    assert result.status == falcon.HTTP_OK
    assert result.json == query_result_of(
        [query_item_of(fragment) for fragment in fragments],
        None,
        False,
        False,
    )


def test_query_signs_invalid(client, fragmentarium, sign_repository, signs):
    result = client.simulate_get(
        "/fragments/query",
        params={"transliteration": "$ invalid"},
    )

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_random(client, fragmentarium):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    fragmentarium.create(transliterated_fragment)

    result = client.simulate_get("/fragments", params={"random": True})

    assert result.status == falcon.HTTP_OK
    assert result.json == [expected_fragment_info_dto(transliterated_fragment)]
    assert "Cache-Control" not in result.headers


def test_interesting(client, fragmentarium):
    interesting_fragment = InterestingFragmentFactory.build(
        number=MuseumNumber("K", "1")
    )
    fragmentarium.create(interesting_fragment)

    result = client.simulate_get("/fragments", params={"interesting": True})

    assert result.status == falcon.HTTP_OK
    assert result.json == [expected_fragment_info_dto(interesting_fragment)]
    assert "Cache-Control" not in result.headers


def test_needs_revision(client, fragmentarium):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    fragmentarium.create(transliterated_fragment)
    expected_fragment = attr.evolve(transliterated_fragment, genres=())
    result = client.simulate_get("/fragments", params={"needsRevision": True})
    expected_dto = [expected_fragment_info_dto(expected_fragment)]
    if "acquisition" in expected_dto[0]:
        del expected_dto[0]["acquisition"]
    assert result.status == falcon.HTTP_OK
    assert result.json == expected_dto
    assert result.headers["Cache-Control"] == "private, max-age=600"


def test_search_fragment_no_query(client):
    result = client.simulate_get("/fragments")

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


@pytest.mark.parametrize(
    "parameters",
    [
        {},
        {"random": True, "interesting": True},
        {"random": True, "interesting": True, "pages": "254"},
        {"invalid": "parameter"},
        {"a": "a", "b": "b", "c": "c"},
    ],
)
def test_search_invalid_params(client, parameters):
    result = client.simulate_get("/fragments", params=parameters)
    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


@pytest.mark.parametrize(
    "endpoint,expected",
    [
        ("/genres", list(map(list, genres))),
        (
            "/periods",
            [period.long_name for period in Period if period is not Period.NONE],
        ),
    ],
)
def test_get_options(client, endpoint, expected):
    result = client.simulate_get(endpoint)

    assert result.status == falcon.HTTP_OK
    assert result.json == expected


def test_search_with_scopes(client, guest_client, fragmentarium):
    fragment = FragmentFactory.build(
        authorized_scopes=[Scope.READ_ITALIANNINEVEH_FRAGMENTS]
    )
    params = {
        "number": str(fragment.number),
    }

    fragmentarium.create(fragment)

    result = client.simulate_get("/fragments/query", params=params)
    guest_result = guest_client.simulate_get("/fragments/query", params=params)

    assert result.status == falcon.HTTP_OK
    assert result.json == query_result_of([query_item_of(fragment)], 0)

    assert guest_result.status == falcon.HTTP_OK
    assert guest_result.json == query_result_of([], 0)


def test_search_with_scopes_limit_summary(client, guest_client, fragmentarium):
    fragment = FragmentFactory.build(
        number=MuseumNumber.of("X.404"),
        authorized_scopes=[Scope.READ_ITALIANNINEVEH_FRAGMENTS],
    )
    params = {
        "number": str(fragment.number),
        "limit": "1",
    }

    fragmentarium.create(fragment)

    result = client.simulate_get("/fragments/query", params=params)
    guest_result = guest_client.simulate_get("/fragments/query", params=params)

    assert result.status == falcon.HTTP_OK
    assert result.json == query_result_of([query_summary_of(fragment)], 0)

    assert guest_result.status == falcon.HTTP_OK
    assert guest_result.json == query_result_of([], 0)


@pytest.mark.parametrize(
    "params,expected",
    [
        ({"scriptPeriod": Period.NEO_BABYLONIAN.long_name}, [0]),
        ({"scriptPeriod": Period.OLD_ASSYRIAN.long_name}, [1, 2]),
        (
            {
                "scriptPeriod": Period.OLD_ASSYRIAN.long_name,
                "scriptPeriodModifier": PeriodModifier.LATE.value,
            },
            [2],
        ),
        ({"scriptPeriod": Period.NEO_BABYLONIAN.long_name}, [0]),
    ],
)
def test_search_script_period(client, fragmentarium, params, expected):
    scripts = [
        Script(Period.NEO_BABYLONIAN),
        Script(Period.OLD_ASSYRIAN, PeriodModifier.EARLY),
        Script(Period.OLD_ASSYRIAN, PeriodModifier.LATE),
    ]
    fragments = [FragmentFactory.build(script=script) for script in scripts]

    for fragment in fragments:
        fragmentarium.create(fragment)

    expected_json = query_result_of([query_item_of(fragments[i]) for i in expected], 0)

    result = client.simulate_get("/fragments/query", params=params)

    assert result.status == falcon.HTTP_OK
    assert result.json == expected_json


@pytest.mark.parametrize(
    "project",
    [
        ResearchProject.CAIC,
        ResearchProject.ALU_GENEVA,
        ResearchProject.AMPS,
        ResearchProject.RECC,
    ],
)
def test_search_project(client, fragmentarium, project):
    fragments = [
        FragmentFactory.build(projects=(project,)) for project in ResearchProject
    ]

    for fragment in fragments:
        fragmentarium.create(fragment)

    expected_json = query_result_of(
        [
            query_item_of(fragment)
            for fragment in fragments
            if project in fragment.projects
        ],
        0,
    )

    result = client.simulate_get(
        "/fragments/query", params={"project": project.abbreviation}
    )

    assert result.status == falcon.HTTP_OK
    assert result.json == expected_json


@pytest.mark.parametrize(
    "museum",
    [Museum.THE_BRITISH_MUSEUM, Museum.THE_IRAQ_MUSEUM, Museum.PENN_MUSEUM],
)
@pytest.mark.parametrize("attribute", ["name"])
def test_search_museum(client, fragmentarium, museum, attribute):
    print(f"Testing museum: {museum.name} with attribute: {attribute}")

    fragments = [
        FragmentFactory.build(museum=museum)
        for museum in [museum, Museum.YALE_PEABODY_COLLECTION]
    ]

    print(f"Fragments created: {fragments}")

    for fragment in fragments:
        fragmentarium.create(fragment)
        print(f"Fragment created in fragmentarium: {fragment}")

    expected_json = query_result_of(
        [
            query_item_of(fragment)
            for fragment in fragments
            if fragment.museum == museum
        ],
        0,
    )

    print(f"Expected JSON: {expected_json}")
    print(f"Requesting with museum attribute: {getattr(museum, attribute)}")

    result = client.simulate_get(
        "/fragments/query", params={"museum": getattr(museum, attribute)}
    )

    print(f"Result from client: {result.status}, {result.json}")

    assert result.status == falcon.HTTP_OK
    assert result.json == expected_json


@pytest.mark.parametrize(
    "site",
    [
        get_provenance_record("UR"),
        get_provenance_record("TELL_EL_AMARNA"),
        get_provenance_record("KIS"),
    ],
)
@pytest.mark.parametrize(
    "attribute",
    ["long_name", "id"],
)
def test_search_site(client, fragmentarium, site, attribute):
    fragments = [
        FragmentFactory.build(archaeology__site=site)
        for site in [site, get_provenance_record("ASSUR")]
    ]

    for fragment in fragments:
        fragmentarium.create(fragment)

    expected_json = query_result_of(
        [
            query_item_of(fragment)
            for fragment in fragments
            if fragment.archaeology.site == site
        ],
        0,
    )

    result = client.simulate_get(
        "/fragments/query", params={"site": getattr(site, attribute)}
    )

    assert result.status == falcon.HTTP_OK
    assert result.json == expected_json


@pytest.mark.parametrize(
    "parent_site",
    [
        get_provenance_record("ASSYRIA"),
        get_provenance_record("BABYLONIA"),
        get_provenance_record("PERIPHERY"),
    ],
)
@pytest.mark.parametrize(
    "attribute",
    ["long_name", "id"],
)
def test_search_parent_site_returns_no_results(
    client, fragmentarium, parent_site, attribute
):
    child = get_provenance_record("UR")
    fragment = FragmentFactory.build(archaeology__site=child)
    fragmentarium.create(fragment)

    result = client.simulate_get(
        "/fragments/query", params={"site": getattr(parent_site, attribute)}
    )

    assert result.status == falcon.HTTP_OK
    assert result.json == query_result_of([], 0)


def test_query_latest(client, fragmentarium):
    number_of_fragments = LATEST_TRANSLITERATION_LIMIT + 10
    start_date = date(2023, 5, 1)
    fragments = [
        TransliteratedFragmentFactory.build(
            record=RecordFactory.build(
                entries=(
                    RecordEntryFactory.build(
                        date=str(start_date + timedelta(i)),
                        type=RecordType.TRANSLITERATION,
                    ),
                )
            ),
        )
        for i in range(number_of_fragments)
    ]

    for fragment in fragments:
        fragmentarium.create(fragment)

    query_items_by_date = [
        query_item_of(
            fragment,
            list(range(LATEST_TRANSLITERATION_LINE_LIMIT)),
            0,
        )
        for fragment in reversed(fragments)
    ]
    expected = {
        "items": query_items_by_date[:LATEST_TRANSLITERATION_LIMIT],
        "matchCountTotal": 0,
    }

    result = client.simulate_get("/fragments/latest")

    assert result.status == falcon.HTTP_OK
    assert result.json == expected
