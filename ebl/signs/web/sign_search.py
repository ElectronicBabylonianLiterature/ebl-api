from typing import Dict, FrozenSet, List, Mapping, Sequence

from ebl.dispatcher import Command, create_dispatcher
from ebl.errors import DataError
from ebl.signs.infrastructure.mongo_sign_repository import SignDtoSchema
from ebl.transliteration.application.sign_repository import SignRepository
from ebl.signs.web.logograms_injector import inject_logograms_unicode
from ebl.transliteration.domain.sign import Sign

LIST_ALL = frozenset(["listAll"])


def sub_index_of(params: Mapping[str, str]) -> int:
    value = params["subIndex"]
    try:
        return int(value)
    except ValueError:
        raise DataError(f"subIndex '{value}' has to be a number")


class SignsSearch:
    def __init__(self, signs: SignRepository):
        self.sign_repository = signs
        commands: Dict[FrozenSet[str], Command[str, Sequence[Sign]]] = {
            frozenset(["listsName", "listsNumber"]): lambda params: (
                signs.search_by_lists_name(params["listsName"], params["listsNumber"])
            ),
            frozenset(["value", "subIndex"]): lambda params: signs.search_all(
                params["value"], sub_index_of(params)
            ),
            frozenset(["value", "isIncludeHomophones", "subIndex"]): lambda params: (
                signs.search_include_homophones(params["value"])
            ),
            frozenset(["value", "subIndex", "isComposite"]): lambda params: (
                signs.search_composite_signs(params["value"], sub_index_of(params))
            ),
            frozenset(["wordId"]): lambda params: signs.search_by_lemma(
                params["wordId"]
            ),
        }
        self._dispatch = create_dispatcher(commands)

    @staticmethod
    def _validate_sub_index(params: Mapping[str, str]) -> Mapping[str, str]:
        if "subIndex" in params:
            sub_index_of(params)
        return params

    def _search(self, params: Mapping[str, str]) -> Sequence[Sign]:
        signs = self._dispatch(params)
        return (
            inject_logograms_unicode(signs, params["wordId"], self.sign_repository)
            if "wordId" in params
            else signs
        )

    def _list_all_sign_names(self) -> List[str]:
        return list(self.sign_repository.list_all_signs())

    def on_get(self, req, resp) -> None:
        params = self._validate_sub_index(req.params)
        resp.media = (
            self._list_all_sign_names()
            if frozenset(params) == LIST_ALL
            else SignDtoSchema().dump(self._search(params), many=True)
        )
