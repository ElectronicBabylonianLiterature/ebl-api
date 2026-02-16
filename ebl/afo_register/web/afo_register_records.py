from falcon import Request, Response
from ebl.errors import NotFoundError

from ebl.afo_register.application.afo_register_repository import AfoRegisterRepository
from ebl.afo_register.infrastructure.mongo_afo_register_repository import (
    AfoRegisterRecordSchema,
    AfoRegisterRecordSuggestionSchema,
)


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
        try:
            response = self._afoRegisterRepository.search_by_texts_and_numbers(
                req.media
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
