from typing import Optional, Sequence

import pydash

from ebl.transliteration.application.sign_repository import SignRepository
from ebl.transliteration.domain.sign import Sign, SignName


class MemoizingSignRepository(SignRepository):
    def __init__(self, delegate: SignRepository):
        self._create = delegate.create
        self._find = pydash.memoize(delegate.find)
        self._search = pydash.memoize(delegate.search)
        self._query = pydash.memoize(delegate.query)

    def create(self, sign: Sign) -> str:
        return self._create(sign)

    def find(self, name: SignName) -> Sign:
        return self._find(name)

    def query(self, query: str) -> Sequence[Sign]:
        return self._query(query)

    def search(self, reading, sub_index) -> Optional[Sign]:
        return self._search(reading, sub_index)
