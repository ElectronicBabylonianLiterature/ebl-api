from typing import Sequence, Dict, Callable
from ebl.common.query.query_result import LemmaQueryType
from ebl.errors import DataError
from ebl.transliteration.application.transliteration_query_factory import (
    TransliterationQueryFactory,
)

COUNT_MODES = ("exact", "none", "page")
MAX_FINDSPOT_ID = 2**63 - 1
MAX_FINDSPOT_ID_RAW_LENGTH = 64
MAX_FINDSPOT_IDS = 200
MAX_FINDSPOT_IDS_RAW_LENGTH = 4096


def parse_integer_field(field: str) -> Callable[[Dict], Dict]:
    def parse_integer(parameters: Dict) -> Dict:
        if field not in parameters:
            return parameters

        value = parameters[field]

        try:
            return {**parameters, field: int(value)}
        except ValueError as error:
            raise DataError(
                f"{field} must be integer, got {value!r} instead"
            ) from error

    return parse_integer


def parse_non_negative_integer_field(field: str) -> Callable[[Dict], Dict]:
    parse_integer = parse_integer_field(field)

    def parse_non_negative_integer(parameters: Dict) -> Dict:
        parameters = parse_integer(parameters)
        if parameters.get(field, 0) < 0:
            raise DataError(f"{field} must be non-negative")
        return parameters

    return parse_non_negative_integer


def parse_lines(lines: Sequence[str]) -> Sequence[int]:
    try:
        return [int(line) for line in lines]
    except ValueError as error:
        raise DataError(
            f"lines must be a list of integers, got {lines} instead"
        ) from error


def parse_transliteration(
    transliteration_query_factory: TransliterationQueryFactory,
) -> Callable[[Dict], Dict]:
    def _parse(parameters: Dict) -> Dict:
        if "transliteration" not in parameters:
            return parameters

        return {
            **parameters,
            "transliteration": [
                transliteration_query_factory.create(line).regexp
                for line in parameters["transliteration"].strip().split("\n")
                if line
            ],
        }

    return _parse


def parse_lemmas(parameters: Dict) -> Dict:
    if "lemmas" not in parameters:
        return parameters

    lemmas = parameters["lemmas"].split("+")

    try:
        lemma_operator = LemmaQueryType[
            (
                "AND"
                if len(lemmas) == 1
                else parameters.get("lemmaOperator", "and").upper()
            )
        ]
    except KeyError as error:
        raise DataError(
            f"unexpected lemmaOperator {parameters['lemmaOperator']!r}"
        ) from error

    return {
        **parameters,
        "lemmas": lemmas,
        "lemmaOperator": lemma_operator,
    }


def parse_pages(parameters: Dict) -> Dict:
    if "pages" not in parameters:
        return parameters

    if "bibId" not in parameters:
        raise DataError("Name, Year or Title required")
    pages = parameters["pages"]

    return {**parameters, "pages": pages}


def parse_genre(parameters: Dict) -> Dict:
    genre = parameters.get("genre", "").split(":")

    return {**parameters, "genre": genre} if any(genre) else parameters


def _parse_findspot_id(value: str, field: str) -> int:
    if len(value) > MAX_FINDSPOT_ID_RAW_LENGTH:
        raise DataError(
            f"{field} must not exceed {MAX_FINDSPOT_ID_RAW_LENGTH} characters"
        )
    normalized = value.strip()
    if not normalized or not normalized.isascii() or not normalized.isdecimal():
        raise DataError(f"{field} must be a non-negative decimal integer")

    if len(normalized) > len(str(MAX_FINDSPOT_ID)):
        raise DataError(f"{field} must not exceed {MAX_FINDSPOT_ID}")
    parsed = int(normalized)
    if parsed > MAX_FINDSPOT_ID:
        raise DataError(f"{field} must not exceed {MAX_FINDSPOT_ID}")
    return parsed


def parse_findspot_id(parameters: Dict) -> Dict:
    if "findspotId" not in parameters:
        return parameters

    return {
        **parameters,
        "findspotId": _parse_findspot_id(parameters["findspotId"], "findspotId"),
    }


def parse_findspot_ids(parameters: Dict) -> Dict:
    if "findspotIds" not in parameters:
        return parameters

    raw = parameters["findspotIds"]
    if len(raw) > MAX_FINDSPOT_IDS_RAW_LENGTH:
        raise DataError(
            f"findspotIds must not exceed {MAX_FINDSPOT_IDS_RAW_LENGTH} characters."
        )
    values = [item.strip() for item in raw.split(",")]
    if len(values) > MAX_FINDSPOT_IDS:
        raise DataError(
            f"findspotIds must not contain more than {MAX_FINDSPOT_IDS} values."
        )
    if not values or any(not value for value in values):
        raise DataError("findspotIds must not contain empty values.")

    ids = [_parse_findspot_id(value, "findspotIds") for value in values]
    selected_ids = set(ids)
    if (findspot_id := parameters.get("findspotId")) is not None:
        selected_ids.add(findspot_id)
    if len(selected_ids) > MAX_FINDSPOT_IDS:
        raise DataError(
            f"findspotId and findspotIds must not select more than "
            f"{MAX_FINDSPOT_IDS} values."
        )

    return {**parameters, "findspotIds": sorted(set(ids))}


def parse_count(parameters: Dict) -> Dict:
    if "count" not in parameters:
        return parameters

    count = parameters["count"]
    if count not in COUNT_MODES:
        raise DataError(f"unexpected count {count!r}")
    return parameters
