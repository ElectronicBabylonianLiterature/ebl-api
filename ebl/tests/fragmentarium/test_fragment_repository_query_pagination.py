from ebl.common.domain.period import Period
from ebl.common.domain.scopes import Scope
from ebl.fragmentarium.application.fragment_query_summary_schema import (
    FragmentQueryResultSchema,
)
from ebl.fragmentarium.domain.fragment import Script
from ebl.tests.factories.fragment import FragmentFactory, TransliteratedFragmentFactory
from ebl.tests.fragmentarium.fragment_query_test_helpers import query_summary_of
from ebl.tests.fragmentarium.fragment_repository_test_helpers import (
    COLLECTION,
    create_transliteration_query_lines,
)
from ebl.transliteration.domain.museum_number import MuseumNumber


def test_query_fragmentarium_transliteration_limit_summary_preserves_order(
    fragment_repository, sign_repository, signs
):
    for sign in signs:
        sign_repository.create(sign)

    fragments = [
        TransliteratedFragmentFactory.build(
            number=MuseumNumber.of(f"X.{index}"),
            script=Script(Period.LATE_BABYLONIAN),
        )
        for index in range(4)
    ]
    for index, fragment in enumerate(fragments):
        fragment_repository.create(fragment, sort_key=index)

    result = fragment_repository.query(
        {
            "transliteration": create_transliteration_query_lines(
                "KU", sign_repository
            ),
            "limit": 2,
            "offset": 1,
        }
    )

    assert result == FragmentQueryResultSchema().load(
        {
            "items": [
                query_summary_of(fragment, matching_lines=[0])
                for fragment in fragments[1:3]
            ],
            "matchCountTotal": 4,
        }
    )


def test_query_fragmentarium_transliteration_limit_count_none(
    fragment_repository, sign_repository, signs
):
    for sign in signs:
        sign_repository.create(sign)

    fragments = [
        TransliteratedFragmentFactory.build(
            number=MuseumNumber.of(f"X.{index}"),
            script=Script(Period.LATE_BABYLONIAN),
        )
        for index in range(3)
    ]
    fragment_repository.create_many(fragments)

    result = fragment_repository.query(
        {
            "transliteration": create_transliteration_query_lines(
                "KU", sign_repository
            ),
            "limit": 2,
            "count": "none",
        }
    )

    assert result.match_count_total is None
    assert result.is_match_count_total_exact is False
    assert result.has_next_page is None
    assert len(result.items) == 2


def test_query_fragmentarium_transliteration_limit_count_page(
    fragment_repository, sign_repository, signs
):
    for sign in signs:
        sign_repository.create(sign)

    fragments = [
        TransliteratedFragmentFactory.build(
            number=MuseumNumber.of(f"X.{index}"),
            script=Script(Period.LATE_BABYLONIAN),
        )
        for index in range(3)
    ]
    for index, fragment in enumerate(fragments):
        fragment_repository.create(fragment, sort_key=index)

    result = fragment_repository.query(
        {
            "transliteration": create_transliteration_query_lines(
                "KU", sign_repository
            ),
            "limit": 2,
            "count": "page",
        }
    )
    last_page_result = fragment_repository.query(
        {
            "transliteration": create_transliteration_query_lines(
                "KU", sign_repository
            ),
            "limit": 2,
            "offset": 2,
            "count": "page",
        }
    )

    assert result.match_count_total is None
    assert result.is_match_count_total_exact is False
    assert result.has_next_page is True
    assert [item.museum_number for item in result.items] == [
        fragment.number for fragment in fragments[:2]
    ]
    assert last_page_result.match_count_total is None
    assert last_page_result.is_match_count_total_exact is False
    assert last_page_result.has_next_page is False
    assert [item.museum_number for item in last_page_result.items] == [
        fragments[2].number
    ]


def test_query_fragmentarium_limit_summary_hydrates_only_phase_one_ids(
    monkeypatch, fragment_repository, sign_repository, signs
):
    for sign in signs:
        sign_repository.create(sign)

    visible_fragment = TransliteratedFragmentFactory.build(
        number=MuseumNumber.of("X.1")
    )
    hidden_fragment = TransliteratedFragmentFactory.build(
        number=MuseumNumber.of("X.2"),
        authorized_scopes=[Scope.READ_ITALIANNINEVEH_FRAGMENTS],
    )
    fragment_repository.create(visible_fragment, sort_key=0)
    fragment_repository.create(hidden_fragment, sort_key=1)

    summary_queries = []
    original_find_many = fragment_repository._fragments.find_many

    def find_many(query, *args, **kwargs):
        summary_queries.append(query)
        return original_find_many(query, *args, **kwargs)

    monkeypatch.setattr(fragment_repository._fragments, "find_many", find_many)

    result = fragment_repository.query(
        {
            "transliteration": create_transliteration_query_lines(
                "KU", sign_repository
            ),
            "limit": 10,
        },
        user_scopes=(),
    )

    assert result == FragmentQueryResultSchema().load(
        {
            "items": [query_summary_of(visible_fragment, matching_lines=[0])],
            "matchCountTotal": 1,
        }
    )
    assert summary_queries == [{"_id": {"$in": [str(visible_fragment.number)]}}]


def test_query_fragmentarium_number_limit_summary_parser_version_fallback(
    database, fragment_repository
):
    fragment = FragmentFactory.build(number=MuseumNumber.of("X.500"))
    fragment_repository.create(fragment)
    database[COLLECTION].update_one(
        {"_id": str(fragment.number)}, {"$set": {"text.parser_version": None}}
    )

    dumped = FragmentQueryResultSchema().dump(
        fragment_repository.query({"number": str(fragment.number), "limit": 1})
    )

    assert dumped["items"][0]["matchingLinePreview"]["parserVersion"] is not None


def test_query_fragmentarium_number_limit_summary_uses_bulk_photo_lookup(
    database, fragment_repository
):
    fragment = FragmentFactory.build(number=MuseumNumber.of("X.501"))
    fragment_repository.create(fragment)
    database["photos.files"].insert_one({"filename": f"{fragment.number}.jpg"})

    assert fragment_repository.query(
        {"number": str(fragment.number), "limit": 1}
    ) == FragmentQueryResultSchema().load(
        {
            "items": [query_summary_of(fragment, has_photo=True)],
            "matchCountTotal": 0,
        }
    )
