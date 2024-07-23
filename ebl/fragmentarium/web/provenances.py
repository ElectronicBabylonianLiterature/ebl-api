from falcon import Response, Request
from ebl.common.domain.provenance import Provenance


class ProvenancesResource:
    def on_get(self, _req: Request, resp: Response) -> None:
        provenances_data = tuple(
            (
                (prov.long_name, prov.parent)
                if prov.parent is None
                else (prov.long_name, f"[{prov.parent}]")
            )
            for prov in Provenance
            if prov.long_name != "Standard Text"
        )
        resp.media = provenances_data
