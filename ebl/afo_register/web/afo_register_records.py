from typing import List
from falcon import Request, Response
from ebl.errors import DataError, NotFoundError

from ebl.afo_register.application.afo_register_repository import AfoRegisterRepository
from ebl.afo_register.infrastructure.mongo_afo_register_repository import (
    AfoRegisterRecordSchema,
    AfoRegisterRecordSuggestionSchema,
)

MAX_TEXTS_AND_NUMBERS_QUERIES = 1000
MAX_QUERY_LENGTH = 500


def validate_texts_and_numbers_query(body: object) -> List[str]:
    if not isinstance(body, list):
        raise DataError("Request body must be a list of strings.")
    if len(body) > MAX_TEXTS_AND_NUMBERS_QUERIES:
        raise DataError(
            f"Too many queries: at most {MAX_TEXTS_AND_NUMBERS_QUERIES} allowed."
        )
    validated_queries: List[str] = []
    for query in body:
        if not isinstance(query, str):
            raise DataError("Each query must be a string.")
        if len(query) > MAX_QUERY_LENGTH:
            raise DataError(
                f"Query too long: at most {MAX_QUERY_LENGTH} characters allowed."
            )
        validated_queries.append(query)
    return validated_queries


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
        query_list = validate_texts_and_numbers_query(req.media)
        try:
            response = self._afoRegisterRepository.search_by_texts_and_numbers(
                query_list
            )
        except ValueError as error:
            raise NotFoundError(
                f"No AfO registry entries matching {str(req.media)} found."
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
