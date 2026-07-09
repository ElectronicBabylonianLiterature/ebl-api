import falcon
import pytest

from ebl.common.domain.period import Period
from ebl.fragmentarium.domain.fragment import Script
from ebl.tests.factories.fragment import (
    LemmatizedFragmentFactory,
    TransliteratedFragmentFactory,
)
from ebl.tests.fragmentarium.fragment_query_test_helpers import (
    query_item_of,
    query_result_of,
    query_summary_of,
)
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.sign import Sign, Value
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.word_tokens import Word


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
