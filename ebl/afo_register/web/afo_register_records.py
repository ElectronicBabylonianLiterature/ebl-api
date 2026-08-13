from typing import List, Optional, Sequence
from falcon import Request, Response
from ebl.errors import DataError, NotFoundError

from ebl.afo_register.application.afo_register_repository import AfoRegisterRepository
from ebl.afo_register.infrastructure.mongo_afo_register_repository import (
    MAX_CANDIDATES,
    NON_STRING_QUERY_MESSAGE,
    TOO_MANY_CANDIDATES_MESSAGE,
    AfoRegisterRecordSchema,
    AfoRegisterRecordSuggestionSchema,
)

MAX_TEXTS_AND_NUMBERS_QUERIES = 1000
MAX_QUERY_BYTES = 500
MAX_QUERY_TOKENS = 24
MAX_JSON_ESCAPE_EXPANSION = 6
MAX_REQUEST_BYTES = (
    MAX_TEXTS_AND_NUMBERS_QUERIES * (MAX_QUERY_BYTES * MAX_JSON_ESCAPE_EXPANSION + 3)
    + 2
)
REQUEST_TOO_LARGE_MESSAGE = (
    f"Request too large: at most {MAX_REQUEST_BYTES} bytes allowed."
)


def validate_request_size(content_length: Optional[int]) -> None:
    if content_length and content_length > MAX_REQUEST_BYTES:
        raise DataError(REQUEST_TOO_LARGE_MESSAGE)


def validate_query(query: object) -> str:
    if not isinstance(query, str):
        raise DataError(NON_STRING_QUERY_MESSAGE)
    if len(query.encode("utf-8")) > MAX_QUERY_BYTES:
        raise DataError(f"Query too long: at most {MAX_QUERY_BYTES} bytes allowed.")
    if len(query.split()) > MAX_QUERY_TOKENS:
        raise DataError(
            f"Query has too many words: at most {MAX_QUERY_TOKENS} allowed."
        )
    return query


def count_candidate_splits(queries: Sequence[str]) -> int:
    return sum(max(len(query.split()) - 1, 0) for query in queries)


def validate_candidate_budget(queries: List[str]) -> List[str]:
    if count_candidate_splits(queries) > MAX_CANDIDATES:
        raise DataError(TOO_MANY_CANDIDATES_MESSAGE)
    return queries


def validate_texts_and_numbers_query(body: object) -> List[str]:
    if not isinstance(body, list):
        raise DataError("Request body must be a list of strings.")
    if len(body) > MAX_TEXTS_AND_NUMBERS_QUERIES:
        raise DataError(
            f"Too many queries: at most {MAX_TEXTS_AND_NUMBERS_QUERIES} allowed."
        )
    return validate_candidate_budget([validate_query(query) for query in body])


class AfoRegisterResource:
    def __init__(self, afoRegisterRepository: AfoRegisterRepository):
        self._afoRegisterRepository = afoRegisterRepository

    def on_get(self, req: Request, resp: Response) -> None:
        try:
            response = self._afoRegisterRepository.search(req.params)
        except ValueError as error:
            raise NotFoundError(
                f"No AfO registry entries matching {str(req.params)} found."
            ) from error
        resp.media = AfoRegisterRecordSchema().dump(response, many=True)


class AfoRegisterTextsAndNumbersResource:
    def __init__(self, afoRegisterRepository: AfoRegisterRepository):
        self._afoRegisterRepository = afoRegisterRepository

    def on_post(self, req: Request, resp: Response) -> None:
        validate_request_size(req.content_length)
        query_list = validate_texts_and_numbers_query(req.media)
        try:
            response = self._afoRegisterRepository.search_by_texts_and_numbers(
                query_list
            )
        except ValueError as error:
            raise NotFoundError(
                f"No AfO registry entries matching the {len(query_list)} "
                "submitted queries found."
            ) from error
        resp.media = AfoRegisterRecordSchema().dump(response, many=True)


class AfoRegisterSuggestionsResource:
    def __init__(self, afoRegisterRepository: AfoRegisterRepository):
        self._afoRegisterRepository = afoRegisterRepository

    def on_get(self, req: Request, resp: Response) -> None:
        response = self._afoRegisterRepository.search_suggestions(
            req.params["text_query"]
        )
        resp.media = AfoRegisterRecordSuggestionSchema().dump(response, many=True)
