import copy

import attr
import falcon
import pytest

from ebl.signs.infrastructure.mongo_sign_repository import SignDtoSchema
from ebl.transliteration.domain.sign import Sign, SignName, Fossey


def test_signs_get(client, sign_repository):
    sign = Sign(
        SignName("test"),
        fossey=[
            Fossey(
                sign="""<svg height="10" width="10">
                <circle cx="5" cy="5" r="4" stroke="black" stroke-width="3" fill="red" />
                </svg> """
            ),
            Fossey(number=1),
        ],
    )
    sign_repository.create(sign)
    result = client.simulate_get(f"/signs/{sign.name}")

    assert result.json == SignDtoSchema().dump(
        attr.evolve(
            sign,
            fossey=[
                Fossey(
                    sign="iVBORw0KGgoAAAANSUhEUgAAAGQAAABkCAYAAABw4pVUAAAABmJLR0QA/wD/AP+gvaeTAAAGFElEQVR4nO2dW2yUR"
                    "RTHf0XaxFjwQiQgaelFxZjY2ouKTwbFaLw/AMagxCd98ckng0Z91ARjGgyGF5WGGFHwhtIYbTBGrESMxkSgVagSE6C05VJMM"
                    "LY7Ppxd3dZud/e7nDPft/tP/g/ttjlzzn/nm2/OzJwBHbQBvcAk4BLGKWA3cFPkUTFAN7AH+6BGwQzwCdAZaYSUcBnQQzJ7R"
                    "Ck9phdYFFm0YkQNsAE4iX3g4uYo8ETWZy+xHPgK+0Bpcy/QGEH8IsUDwBj2wbHiGWBN6ChGgPnAS8iAZx0Ua2aQcbMuVERDYB"
                    "mwf44GVioHgKUh4hoILcCvIRueZg4D1waObpnopjLeosJyFFgZMMYlYxVw1tjRJPE8cHegSJeAO4G/PHAyabwArA4Q7znRDUx"
                    "44FxS+Sdwa9lRL4CrgRMeOJV0ngJWlBn7/+Eq5I3B2pm08BjQUJYCeagFvvHAibRxP3NMHi8q9AHwCrB2js+rCIZlwMXA5+X8"
                    "031U0yFxMgM8VKoYDcikxrrRaec40FRMjBoqM4VuxS8psp7yuAeNrDQ+mi9AvjqXA4eBxVShiZPAdciayrS3rFeB2yxaVOGoz"
                    "7Iv/5fdyOK9dfetVE4CHfmCpGWrTpL5EcgY0gkcwOPdEzk0I/n/LmT1pxm4AunvILnuMeA3YAhxam/25wTAke0lO7H/dhRkC7"
                    "gXwA2BcwE5CO55cM0e+FOEO8DTsaMT3C5wUyGEmMkpcDvBdXjgXwFO4kEjpnEJuO3gMhEKMZMZcNvALfbA31lo3oB/+Qi40zE"
                    "KMZPj4NZ54Ld3gtSB26ooxExuybbBOg5eCHIJuD5DMXLsB7fQXgxbQerBfeuBGDkOZNtkGZN5GKEOeB+4xaoBs2AlsAvDvaBZ"
                    "mHwTLMeMYnzdtpfoG13nQdCLcb2RIDU5VbSwBDiEHLHyGaeRnPiIsl31MWQT/osBsjj0soFd1R7SBXxHArKYWTgk8/qjok3VH"
                    "rKR5IgB0taNBjZVekgL8AsGz8iQyACt6KXw1eLzmKaxCDEPWK9oT62HDAHXaBiKAYeA65VsqQjSDByN20jMaAJ+V7Cj8hRZpW"
                    "EkZmj5oCJIl4aRmKFV4ERFkNCnVDyAlg8qgrRoGIkZrUp2VAS5VMNIzNBK96gIUl/8T7zHAiU7SZyrmUAr4aciyHkNIzFjQsm"
                    "OiiBnNIzEjLNKdlQEGdYwEjOOKNlREWRQw0jM0PJBRZADGkZihpYPKsnFRnQSc3GiAfhDwY5KDzmGpN+TioPoiAGK85C3tQzF"
                    "AM22qy1QNSM1AZM2E03tEu4w8IGWsQjxHrpH4lS3AXUA35OcnScOuBH4SdGm6hPkB2C7psGQeBNdMUC5h4CUiTiM7Az0GePIV"
                    "tJTynbVx9gR4EltowHwFPpi5GCyy3uLBzvcC3GzUUyytDFcB+4zD4I/k33gaitREJDjYwMeiJCjD0faTAUBOfS5xwMxvgC3wF"
                    "4Me0FAHl+WY8prmD+m/BIkx4eRw/xaQoyBW+OB394KAlLu4i3iL63xBrgrPfB3NkG8LD7TDu5doi8+swNcmwf+FeAkSP7MuiE"
                    "F2QTuOXAHQwjxM7hnwS33wJ8ifKeGBOX8GoDbkXqEK5AjAouYXsBsFMnODiJO9aO3uBQSDsllAvAp9t+OSueH+ep0ks5bOZPC"
                    "v4F2+K9M7HEkEXszVVhgM7ANpo8bC5HMuPqVbxWOaYWU89Pv54BnLFpU4XiaOXbb1iCVVa2fqZXCfkp4u21A1masG5t2jiMXO"
                    "peEe6he6BInM8CDpYqRwyYPGp5WBio0VItctGvd+LRxXza2gbAY2ZZr7URaeASp4RYKrVQvloyCI0R4g3QbUvXO2qmk8hwxFI"
                    "NYjVy0a+1c0ngBuCNAvEtC9fru8jgB3BUo0mWgi+oF96XwBIp1d3IV+6yd9pVHiXAALxVLqc5TZuPXRPBqGxTzgRfxdKOEMjN"
                    "ADyEmfVHifuQ+LuugWHEUuDd0FCNGI3K3q3VwtNlPiEvrNbCWypjZHwc2kIDdOiA1y3pI58aJKWArCa3L1gF8TDrWVjLIVp32"
                    "SCNkhBuAXpLZY6aA3ShN8v4BjGtvFJDr/+AAAAAASUVORK5CYII="
                ),
                Fossey(number=1),
            ],
        )
    )

    assert result.status == falcon.HTTP_OK


def test_signs_not_found(client):
    result = client.simulate_get("/words/not found")

    assert result.status == falcon.HTTP_NOT_FOUND


sign_data = {
    "lists": [{"name": "ABZ", "number": "377n1"}],
    "logograms": [
        {
            "logogram": "P₂",
            "atf": "P₂",
            "wordId": ["lemmatu I"],
            "schrammLogogramme": "P₂",
            "unicode": "",
        }
    ],
    "fossey": [],
    "mesZl": "",
    "LaBaSi": "",
    "reverseOrder": "12",
    "name": "P₂",
    "unicode": [74865],
    "values": [{"subIndex": 1, "value": ":"}],
}

sign_data2 = copy.deepcopy(sign_data)
sign_data2["logograms"][0]["unicode"] = "?"


@pytest.mark.parametrize(
    "params, expected",
    [
        (
            {"listsName": "ABZ", "listsNumber": "377n1"},
            [sign_data],
        ),
        (
            {"value": ":", "subIndex": "1"},
            [sign_data],
        ),
        (
            {"value": ":", "isIncludeHomophones": "true", "subIndex": "2"},
            [sign_data],
        ),
        (
            {"value": "ku", "subIndex": "1", "isComposite": "true"},
            [sign_data],
        ),
        (
            {"wordId": "lemmatu I"},
            [sign_data2],
        ),
    ],
)
def test_signs_search_route(params, expected, client, sign_repository, signs):
    for sign in signs:
        sign_repository.create(sign)
    get_result = client.simulate_get("/signs", params=params)
    assert get_result.status == falcon.HTTP_OK
    assert get_result.json == expected


def test_signs_search_route_error(client, sign_repository, signs):
    for sign in signs:
        sign_repository.create(sign)
    get_result = client.simulate_get("/signs", params={"signs": "P₂"})
    assert get_result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_all_signs_route(client, sign_repository, signs):
    for sign in signs:
        sign_repository.create(sign)
    get_result = client.simulate_get("/signs/all")
    assert get_result.status == falcon.HTTP_OK
    assert get_result.json == sorted([sign.name for sign in signs])
