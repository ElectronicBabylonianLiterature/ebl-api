import falcon
from falcon import Request, Response

from ebl.errors import NotFoundError
from ebl.signs.application.mes_zl_kap2_repository import MesZlKap2Repository
from ebl.transliteration.application.sign_repository import SignRepository
from ebl.transliteration.domain.sign import Sign
from ebl.users.web.require_scope import require_scope

READ_SCOPE = "read:meszl-kap2"
MES_ZL_LIST = "MZL"


def mes_zl_number(sign: Sign) -> str:
    try:
        return next(
            record.number for record in sign.lists if record.name == MES_ZL_LIST
        )
    except StopIteration as error:
        raise NotFoundError(f"Sign {sign.name} has no MesZL number.") from error


class MesZlKap2Resource:
    """Borger, MesZL² Kapitel II for a sign; restricted to Full Editors."""

    def __init__(self, signs: SignRepository, entries: MesZlKap2Repository):
        self._signs = signs
        self._entries = entries

    @falcon.before(require_scope, READ_SCOPE)
    def on_get(self, _req: Request, resp: Response, sign_name: str) -> None:
        entry = self._entries.find(mes_zl_number(self._signs.find(sign_name)))
        resp.cache_control = ["private", "no-store"]
        resp.media = {"number": entry.number, "text": entry.text}
