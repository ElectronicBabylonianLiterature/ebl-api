from typing import Optional, Sequence

import pydash

from ebl.transliteration.application.sign_repository import SignRepository
from ebl.transliteration.domain.sign import Sign, SignName


class MemoizingSignRepository(SignRepository):
    def __init__(self, delegate: SignRepository):
        self._create = delegate.create
        self._find = pydash.memoize(delegate.find)
        self._find_many = delegate.find_many
        self._search = pydash.memoize(delegate.search)
        self._search_by_id = pydash.memoize(delegate.search_by_id)
        self._search_all = pydash.memoize(delegate.search_all)
        self._search_composite_signs = pydash.memoize(delegate.search_composite_signs)
        self._search_include_homophones = pydash.memoize(
            delegate.search_include_homophones
        )
        self._search_by_lists_name = pydash.memoize(delegate.search_by_lists_name)

    def create(self, sign: Sign) -> str:
        return self._create(sign)

    def find(self, name: SignName) -> Sign:
        return self._find(name)

    def find_many(self, query, *args, **kwargs) -> Sign:
        return self._find_many(self, query, *args, **kwargs)

    def search_by_lists_name(self, name: str, number: str) -> Sequence[Sign]:
        return self._search_by_lists_name(name, number)

    def search_include_homophones(self, reading) -> Sequence[Sign]:
        return self._search_include_homophones(reading)

    def search_composite_signs(
        self, reading: str, sub_index: Optional[int] = None
    ) -> Sequence[Sign]:
        return self._search_composite_signs(reading, sub_index)

    def search_by_id(self, query: str) -> Sequence[Sign]:
        return self._search_by_id(query)

    def search_all(self, reading: str, sub_index: int) -> Sequence[Sign]:
        return self._search_all(reading, sub_index)

    def search(self, reading, sub_index) -> Optional[Sign]:
        return self._search(reading, sub_index)
