import falcon
from falcon import Request, Response

from ebl.cache.application.cache import cache_control
from ebl.common.domain.scopes import Scope
from ebl.signs.application.mes_zl_kap2_repository import MesZlKap2Repository
from ebl.signs.domain.mes_zl_kap2 import MES_ZL_LIST
from ebl.signs.infrastructure.mes_zl_kap2_schemas import MesZlKap2EntrySchema
from ebl.transliteration.application.sign_repository import SignRepository
from ebl.transliteration.domain.sign import Sign, SignName
from ebl.users.web.require_scope import require_scope

READ_SCOPE = str(Scope.READ_MESZL_KAP2)


def mes_zl_numbers(sign: Sign) -> list[str]:
    return [record.number for record in sign.lists if record.name == MES_ZL_LIST]


class MesZlKap2Resource:
    def __init__(self, signs: SignRepository, entries: MesZlKap2Repository) -> None:
        self._signs = signs
        self._entries = entries

    @falcon.before(require_scope, READ_SCOPE)
    @cache_control(["private", "no-store"])
    def on_get(self, _request: Request, response: Response, sign_name: str) -> None:
        sign = self._signs.find(SignName(sign_name))
        entries = self._entries.find_by_numbers(mes_zl_numbers(sign))
        response.media = MesZlKap2EntrySchema(many=True).dump(entries)
