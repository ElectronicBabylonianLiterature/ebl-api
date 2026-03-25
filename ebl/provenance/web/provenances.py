from falcon import Request, Response

from ebl.provenance.application.provenance_repository import ProvenanceRepository
from ebl.provenance.application.provenance_schema import ApiProvenanceRecordSchema


class ProvenancesResource:
    def __init__(self, provenance_repository: ProvenanceRepository):
        self._provenance_repository = provenance_repository

    def on_get(self, _req: Request, resp: Response) -> None:
        provenances = self._provenance_repository.find_all()
        resp.media = ApiProvenanceRecordSchema(many=True).dump(provenances)


class ProvenanceResource:
    def __init__(self, provenance_repository: ProvenanceRepository):
        self._provenance_repository = provenance_repository

    def on_get(self, _req: Request, resp: Response, id_: str) -> None:
        provenance = self._provenance_repository.query_by_id(id_)
        resp.media = ApiProvenanceRecordSchema().dump(provenance)


class ProvenanceChildrenResource:
    def __init__(self, provenance_repository: ProvenanceRepository):
        self._provenance_repository = provenance_repository

    def on_get(self, _req: Request, resp: Response, id_: str) -> None:
        parent = self._provenance_repository.query_by_id(id_)
        children = self._provenance_repository.find_children(parent.long_name)
        resp.media = ApiProvenanceRecordSchema(many=True).dump(children)
