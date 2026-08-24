from abc import ABC, abstractmethod
from urllib.parse import quote

from ebl.transliteration.domain.museum_number import MuseumNumber


class FragmentIiifIdentity(ABC):
    @abstractmethod
    def identifier_of(self, number: MuseumNumber) -> str:
        raise NotImplementedError

    @abstractmethod
    def is_stable(self) -> bool:
        raise NotImplementedError


class ProvisionalMuseumNumberIdentity(FragmentIiifIdentity):
    def identifier_of(self, number: MuseumNumber) -> str:
        return quote(str(number), safe="")

    def is_stable(self) -> bool:
        return False
