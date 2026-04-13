import unicodedata

from falcon import Request, Response

from ebl.provenance.application.provenance_repository import ProvenanceRepository
from ebl.provenance.application.provenance_schema import ApiProvenanceRecordSchema
from ebl.provenance.domain.provenance_model import STANDARD_TEXT_PROVENANCE_ID

_IGNORABLE = str.maketrans("", "", "\u02bb\u02be\u02bf\u2018\u2019")


def _sort_key(record) -> str:
    cleaned = record.long_name.translate(_IGNORABLE)
    decomposed = unicodedata.normalize("NFD", cleaned)
    stripped = "".join(c for c in decomposed if unicodedata.category(c) != "Mn")
    return stripped.casefold()


class ProvenancesResource:
    def __init__(self, provenance_repository: ProvenanceRepository):
        self._provenance_repository = provenance_repository

    def on_get(self, _req: Request, resp: Response) -> None:
        provenances = [
            p
            for p in self._provenance_repository.find_all()
            if p.id != STANDARD_TEXT_PROVENANCE_ID
        ]
        parents = sorted([p for p in provenances if p.parent is None], key=_sort_key)
        children = sorted(
            [p for p in provenances if p.parent is not None], key=_sort_key
        )
        resp.media = ApiProvenanceRecordSchema(many=True).dump([*parents, *children])


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
        children = sorted(
            self._provenance_repository.find_children(parent.long_name),
            key=_sort_key,
        )
        resp.media = ApiProvenanceRecordSchema(many=True).dump([parent, *children])
