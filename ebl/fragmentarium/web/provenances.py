from falcon import Response, Request

from ebl.common.application.provenance_service import ProvenanceService


class ProvenancesResource:
    def __init__(self, provenance_service: ProvenanceService):
        self._provenance_service = provenance_service

    def on_get(self, _req: Request, resp: Response) -> None:
        provenances = self._provenance_service.find_all()
        provenances_data = tuple(
            (
                (record.long_name, record.parent)
                if record.parent is None
                else (record.long_name, f"[{record.parent}]")
            )
            for record in provenances
            if record.long_name != "Standard Text"
        )
        resp.media = provenances_data
