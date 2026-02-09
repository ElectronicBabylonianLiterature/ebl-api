from typing import Sequence, Dict, Callable
from ebl.common.query.query_result import LemmaQueryType
from ebl.errors import DataError
from ebl.transliteration.application.transliteration_query_factory import (
    TransliterationQueryFactory,
)


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
