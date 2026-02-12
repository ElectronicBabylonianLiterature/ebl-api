from falcon import Request, Response
from urllib.parse import parse_qs
from ebl.errors import NotFoundError
from marshmallow import EXCLUDE

from ebl.dossiers.application.dossiers_repository import DossiersRepository
from ebl.dossiers.infrastructure.mongo_dossiers_repository import (
    DossierRecordSchema,
    DossierRecordSuggestionSchema,
)


class DossiersResource:
    def __init__(self, _dossiersRepository: DossiersRepository):
        self._dossiersRepository = _dossiersRepository

    def on_get(self, req: Request, resp: Response) -> None:
        parsed_params = parse_qs(req.query_string)
        ids = parsed_params.get("ids[]", [])
        if ids:
            try:
                dossiers = self._dossiersRepository.query_by_ids(ids)
            except ValueError as error:
                raise NotFoundError(
                    f"No dossier records matching {req.params} found."
                ) from error
        else:
            dossiers = self._dossiersRepository.find_all()

        resp.media = DossierRecordSchema(unknown=EXCLUDE, many=True).dump(dossiers)


class DossiersSearchResource:
    def __init__(self, _dossiersRepository: DossiersRepository):
        self._dossiersRepository = _dossiersRepository

    def on_get(self, req: Request, resp: Response) -> None:
        query = req.get_param("query", default="")
        provenance = req.get_param("provenance")
        script_period = req.get_param("scriptPeriod")

        dossiers = self._dossiersRepository.search(
            query, provenance=provenance, script_period=script_period
        )

        resp.media = DossierRecordSchema(unknown=EXCLUDE, many=True).dump(dossiers)


class DossiersFilterResource:
    def __init__(self, _dossiersRepository: DossiersRepository):
        self._dossiersRepository = _dossiersRepository

    def on_get(self, req: Request, resp: Response) -> None:
        provenance = req.get_param("provenance")
        script_period = req.get_param("scriptPeriod")
        genre = req.get_param("genre")

        dossiers = self._dossiersRepository.filter_by_fragment_criteria(
            provenance=provenance, script_period=script_period, genre=genre
        )

        resp.media = DossierRecordSchema(unknown=EXCLUDE, many=True).dump(dossiers)


class DossiersSuggestionsResource:
    def __init__(self, _dossiersRepository: DossiersRepository):
        self._dossiersRepository = _dossiersRepository

    def on_get(self, req: Request, resp: Response) -> None:
        query = req.get_param("q", default="")
        suggestions = self._dossiersRepository.search_suggestions(query)
        resp.media = DossierRecordSuggestionSchema(many=True).dump(suggestions)
