from urllib.parse import quote

import falcon

KU = {"unicode": [74154]}
BA = {"unicode": [73792]}
NU = {"unicode": [74337]}
IGI = {"unicode": [74054]}
WHITESPACE = {"unicode": [9999]}

ERASURE_LINE = "°nu : ši\\ku°"
DOLLAR_LINE = "nu\n$ blank"


def _get(client, line: str):
    return client.simulate_get(f"/signs/transliteration/{quote(line, safe='')}")


def _seed(sign_repository, signs) -> None:
    for sign in signs:
        sign_repository.create(sign)


def test_every_sign_carrying_the_reading_is_returned(
    client, sign_repository, signs
) -> None:
    _seed(sign_repository, signs)

    result = _get(client, "ku-nu")

    assert result.status == falcon.HTTP_OK
    assert result.json == [KU, BA, NU]


def test_words_are_separated_by_a_whitespace_marker(
    client, sign_repository, signs
) -> None:
    _seed(sign_repository, signs)

    result = _get(client, "nu nu")

    assert result.status == falcon.HTTP_OK
    assert result.json == [NU, WHITESPACE, NU]


def test_a_broken_away_name_part_contributes_nothing(
    client, sign_repository, signs
) -> None:
    _seed(sign_repository, signs)

    result = _get(client, "nu-[nu]-nu")

    assert result.status == falcon.HTTP_OK
    assert result.json == [NU, NU, NU]


def test_a_reading_broken_in_the_middle_is_looked_up_whole(
    client, sign_repository, signs
) -> None:
    _seed(sign_repository, signs)

    result = _get(client, "[k]u")

    assert result.status == falcon.HTTP_OK
    assert result.json == [KU, BA]


def test_a_reading_broken_in_the_middle_matches_the_unbroken_reading(
    client, sign_repository, signs
) -> None:
    _seed(sign_repository, signs)

    assert _get(client, "[k]u").json == _get(client, "ku").json


def test_an_unknown_reading_yields_nothing(client, sign_repository, signs) -> None:
    _seed(sign_repository, signs)

    result = _get(client, "szi")

    assert result.status == falcon.HTTP_OK
    assert result.json == []


def test_unparsable_transliteration_is_unprocessable(client) -> None:
    result = _get(client, "$$$")

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert "Invalid transliteration" in result.json["description"]


def test_an_erasure_yields_both_the_erased_and_the_over_erased_signs(
    client, sign_repository, signs
) -> None:
    _seed(sign_repository, signs)

    result = _get(client, ERASURE_LINE)

    assert result.status == falcon.HTTP_OK
    assert result.json == [
        WHITESPACE,
        NU,
        WHITESPACE,
        WHITESPACE,
        IGI,
        WHITESPACE,
        WHITESPACE,
        KU,
        BA,
        WHITESPACE,
    ]


def test_a_line_that_is_not_a_text_line_contributes_nothing(
    client, sign_repository, signs
) -> None:
    _seed(sign_repository, signs)

    result = _get(client, DOLLAR_LINE)

    assert result.status == falcon.HTTP_OK
    assert result.json == [NU]
