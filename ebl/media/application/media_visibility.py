from typing import Protocol, Sequence

from ebl.transliteration.domain.museum_number import MuseumNumber


class LegacyMediaVisibility(Protocol):
    def suppressed_legacy_fragments(
        self, fragment_ids: Sequence[MuseumNumber]
    ) -> frozenset[MuseumNumber]: ...

    def legacy_fallback_allowed(self, fragment_id: MuseumNumber) -> bool: ...
