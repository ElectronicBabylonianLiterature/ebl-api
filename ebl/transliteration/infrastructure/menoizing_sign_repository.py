from typing import Optional

import pydash  # pyre-ignore[21]

from ebl.transliteration.application.sign_repository import SignRepository
from ebl.transliteration.domain.sign import Sign, SignName


class MemoizingSignRepository(SignRepository):
    def __init__(self, delegate: SignRepository):
        self._create = delegate.create
        self._find = pydash.memoize(delegate.find)
        self._search = pydash.memoize(delegate.search)

    def create(self, sign: Sign) -> str:
        return self._create(sign)

    def find(self, name: SignName) -> Sign:
        return self._find(name)

    def search(self, reading, sub_index) -> Optional[Sign]:
        return self._search(reading, sub_index)
