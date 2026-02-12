from falcon import Request, Response
import falcon

from ebl.common.application.provenance_repository import ProvenanceRepository
from ebl.common.application.provenance_schema import (
    ApiProvenanceRecordSchema,
    ProvenanceRecordSchema,
)
from ebl.marshmallowschema import validate
from ebl.users.web.require_scope import require_scope


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

    @falcon.before(require_scope, "write:provenances")
    @validate(ProvenanceRecordSchema())
    def on_put(self, req: Request, resp: Response, id_: str) -> None:
        provenance = ProvenanceRecordSchema().load({**req.media, "_id": id_})
        self._provenance_repository.update(provenance)
        resp.media = ApiProvenanceRecordSchema().dump(provenance)


class ProvenanceChildrenResource:
    def __init__(self, provenance_repository: ProvenanceRepository):
        self._provenance_repository = provenance_repository

    def on_get(self, _req: Request, resp: Response, id_: str) -> None:
        children = self._provenance_repository.find_children(id_)
        resp.media = ApiProvenanceRecordSchema(many=True).dump(children)
