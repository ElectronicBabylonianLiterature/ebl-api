from typing import List, Optional

import pydash

from ebl.transliteration_search.application.sign_repository import \
    SignRepository
from ebl.transliteration_search.domain.sign import Sign, SignName
from ebl.transliteration_search.domain.sign_map import SignKey


class MemoizingSignRepository(SignRepository):

    def __init__(self, delegate: SignRepository):
        self._create = delegate.create
        self._find = pydash.memoize(delegate.find)
        self._search = pydash.memoize(delegate.search)
        self._search_many = pydash.memoize(delegate.search_many)

    def create(self, sign: Sign) -> str:
        return self._create(sign)

    def find(self, name: SignName) -> Sign:
        return self._find(name)

    def search(self, reading, sub_index) -> Optional[Sign]:
        return self._search(reading, sub_index)

    def search_many(self, readings: List[SignKey]) -> List[Sign]:
        return self._search_many(readings)
