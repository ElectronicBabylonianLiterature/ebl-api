import falcon
import pytest

from ebl.common.domain.period import Period
from ebl.fragmentarium.application.fragment_query_preview import MAX_PREVIEW_LINES
from ebl.fragmentarium.domain.fragment import Script
from ebl.tests.factories.fragment import TransliteratedFragmentFactory
from ebl.transliteration.domain.atf_parsers.lark_parser import parse_atf_lark
from ebl.transliteration.domain.museum_number import MuseumNumber

MATCHING_LINE_INDEX = 3
MATCHING_LINE_COUNT = 12


@pytest.fixture
def matched_fragment(fragmentarium, sign_repository, signs):
    fragment = TransliteratedFragmentFactory.build(
        number=MuseumNumber.of("X.1"), script=Script(Period.LATE_BABYLONIAN)
    )
    fragmentarium.create(fragment)
    for sign in signs:
        sign_repository.create(sign)
    return fragment


def query_preview(client) -> dict:
    result = client.simulate_get(
        "/fragments/query", params={"transliteration": "ma-tu₂", "limit": "10"}
    )
    assert result.status == falcon.HTTP_OK
    return result.json["items"][0]["matchingLinePreview"]


def test_preview_line_identifies_the_detail_line_without_repeating_it(
    client, matched_fragment
):
    preview = query_preview(client)
    detail = client.simulate_get(f"/fragments/{matched_fragment.number}").json
    line = preview["lines"][0]

    assert line["index"] == MATCHING_LINE_INDEX
    assert line["prefix"] == (detail["text"]["lines"][MATCHING_LINE_INDEX]["prefix"])
    assert "content" not in line
    assert "lineNumber" not in line
    assert "type" not in line


def test_preview_contains_only_matching_lines(client, matched_fragment):
    preview = query_preview(client)

    assert len(matched_fragment.text.lines) > len(preview["lines"])
    assert len(preview["lines"]) == 1
    assert preview["lines"][0]["number"] == (
        matched_fragment.text.lines[MATCHING_LINE_INDEX].line_number.atf
    )


def test_query_response_omits_full_fragment_text(client, matched_fragment):
    result = client.simulate_get(
        "/fragments/query", params={"transliteration": "ma-tu₂", "limit": "10"}
    )

    assert "text" not in result.json["items"][0]
    assert "atf" not in result.json["items"][0]


@pytest.fixture
def heavily_matched_fragment(fragmentarium, sign_repository, signs):
    fragment = TransliteratedFragmentFactory.build(
        number=MuseumNumber.of("X.2"),
        script=Script(Period.LATE_BABYLONIAN),
        text=parse_atf_lark(
            "\n".join(f"{index}. ku" for index in range(1, MATCHING_LINE_COUNT + 1))
        ),
        signs="\n".join(["KU"] * MATCHING_LINE_COUNT),
    )
    fragmentarium.create(fragment)
    for sign in signs:
        sign_repository.create(sign)
    return fragment


def test_preview_is_capped_while_match_count_stays_complete(
    client, heavily_matched_fragment
):
    result = client.simulate_get(
        "/fragments/query", params={"transliteration": "ku", "limit": "10"}
    )
    item = result.json["items"][0]

    assert result.status == falcon.HTTP_OK
    assert MATCHING_LINE_COUNT > MAX_PREVIEW_LINES
    assert item["matchCount"] == MATCHING_LINE_COUNT
    assert len(item["matchingLines"]) == MATCHING_LINE_COUNT
    assert result.json["matchCountTotal"] == MATCHING_LINE_COUNT
    assert len(item["matchingLinePreview"]["lines"]) == MAX_PREVIEW_LINES
    assert [line["number"] for line in item["matchingLinePreview"]["lines"]] == [
        f"{index}." for index in range(1, MAX_PREVIEW_LINES + 1)
    ]


def test_preview_deduplicates_overlapping_multiline_matches(
    client, heavily_matched_fragment
):
    result = client.simulate_get(
        "/fragments/query", params={"transliteration": "ku\nku", "limit": "10"}
    )
    item = result.json["items"][0]

    assert result.status == falcon.HTTP_OK
    assert len(item["matchingLines"]) > len(set(item["matchingLines"]))
    assert [line["number"] for line in item["matchingLinePreview"]["lines"]] == [
        f"{index}." for index in range(1, MAX_PREVIEW_LINES + 1)
    ]


def test_preview_keeps_only_the_compact_fields(client, matched_fragment):
    line = query_preview(client)["lines"][0]

    assert set(line) == {"index", "number", "prefix", "text", "tokens"}
    assert line["text"].startswith(line["tokens"][0]["value"])


def test_preview_line_index_points_into_matching_lines(client, matched_fragment):
    result = client.simulate_get(
        "/fragments/query", params={"transliteration": "ma-tu₂", "limit": "10"}
    )
    item = result.json["items"][0]
    preview_indexes = [line["index"] for line in item["matchingLinePreview"]["lines"]]

    assert preview_indexes == item["matchingLines"][: len(preview_indexes)]
