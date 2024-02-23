from falcon import Response, Request
from ebl.corpus.domain.provenance import Provenance


class ProvenancesResource:
    def on_get(self, _req: Request, resp: Response) -> None:
        provenances_data = tuple((prov.long_name, prov.parent) for prov in Provenance)
        resp.media = provenances_data
