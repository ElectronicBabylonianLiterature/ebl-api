import falcon
from falcon import Request, Response

from ebl.signs.application.mes_zl_kap2_repository import MesZlKap2Repository
from ebl.transliteration.application.sign_repository import SignRepository
from ebl.transliteration.domain.sign import Sign
from ebl.users.web.require_scope import require_scope

READ_SCOPE = "read:meszl-kap2"
MES_ZL_LIST = "MZL"


def mes_zl_numbers(sign: Sign) -> list[str]:
    return [record.number for record in sign.lists if record.name == MES_ZL_LIST]


class MesZlKap2Resource:
    """Borger, MesZL² Kapitel II for a sign; restricted to Full Editors.

    A sign may have several MesZL numbers; all their entries are returned.
    """

    def __init__(self, signs: SignRepository, entries: MesZlKap2Repository):
        self._signs = signs
        self._entries = entries

    @falcon.before(require_scope, READ_SCOPE)
    def on_get(self, _req: Request, resp: Response, sign_name: str) -> None:
        sign = self._signs.find(sign_name)
        entries = self._entries.find_many(mes_zl_numbers(sign))
        resp.cache_control = ["private", "no-store"]
        resp.media = [{"number": entry.number, "text": entry.text} for entry in entries]


class MesZlKap2SectionResource:
    """The Einleitung and the two Anhänge of Kapitel II."""

    def __init__(self, entries: MesZlKap2Repository):
        self._entries = entries

    @falcon.before(require_scope, READ_SCOPE)
    def on_get(self, _req: Request, resp: Response, section: str) -> None:
        text = self._entries.find_section(section)
        resp.cache_control = ["private", "no-store"]
        resp.media = {"section": section, "text": text}
