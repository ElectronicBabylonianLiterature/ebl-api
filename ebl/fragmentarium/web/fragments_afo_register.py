from falcon import Request, Response

from ebl.errors import DataError
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.application.fragment_finder import FragmentFinder

from marshmallow import ValidationError
from ebl.common.query.query_schemas import AfORegisterToFragmentQueryResultSchema


class AfoRegisterFragmentsQueryResource:
    def __init__(self, fragment_repository: FragmentRepository, finder: FragmentFinder):
        self._repository = fragment_repository
        self._finder = finder

    def on_post(self, req: Request, resp: Response) -> None:
        try:
            result = self._repository.query_by_traditional_references(
                req.media["traditionalReferences"],
                req.context.user.get_scopes(prefix="read:", suffix="-fragments"),
            )
            resp.media = AfORegisterToFragmentQueryResultSchema().dump(result)
        except ValidationError as error:
            raise DataError(
                f"Invalid datesInText data: '{req.media['traditionalReferences']}'"
            ) from error
