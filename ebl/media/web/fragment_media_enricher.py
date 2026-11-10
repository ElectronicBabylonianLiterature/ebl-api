from typing import Optional, Sequence, cast

from ebl.media.application.media_schemas import FragmentMediaSummaryDtoSchema
from ebl.media.application.media_service import MediaService
from ebl.media.application.media_visibility import LegacyMediaVisibility
from ebl.media.application.media_summary_dtos import FragmentMediaSummaryDto
from ebl.media.domain import Media
from ebl.transliteration.application.museum_number_schema import MuseumNumberSchema
from ebl.transliteration.domain.museum_number import MuseumNumber


class FragmentMediaEnricher:
    def __init__(
        self,
        service: Optional[MediaService] = None,
        legacy_visibility: Optional[LegacyMediaVisibility] = None,
    ) -> None:
        self._service = service
        self._legacy_visibility = (
            legacy_visibility if legacy_visibility is not None else service
        )

    def enrich(self, document: dict, number: MuseumNumber) -> dict:
        service = self._service
        visibility = self._legacy_visibility
        if service is None and visibility is None:
            return document
        return self._with_media(
            document,
            number,
            service.list_fragment_media(number) if service is not None else None,
            suppress_legacy=visibility is not None
            and not visibility.legacy_fallback_allowed(number),
        )

    def enrich_rows(self, documents: Sequence[dict]) -> list[dict]:
        service = self._service
        visibility = self._legacy_visibility
        if not documents or (service is None and visibility is None):
            return list(documents)
        numbers = [
            cast(MuseumNumber, MuseumNumberSchema().load(document["museumNumber"]))
            for document in documents
        ]
        media_by_fragment = (
            service.find_media_by_fragments(numbers) if service is not None else None
        )
        suppressed = (
            visibility.suppressed_legacy_fragments(numbers)
            if visibility is not None
            else frozenset()
        )
        return [
            self._with_media(
                document,
                numbers[index],
                media_by_fragment[numbers[index]]
                if media_by_fragment is not None
                else None,
                suppress_legacy=numbers[index] in suppressed,
            )
            for index, document in enumerate(documents)
        ]

    @staticmethod
    def _with_media(
        document: dict,
        number: MuseumNumber,
        media: Optional[Sequence[Media]],
        *,
        suppress_legacy: bool = False,
    ) -> dict:
        result = document
        if media is not None:
            summary = FragmentMediaSummaryDto.of(number, media)
            result = {
                **document,
                **cast(
                    dict,
                    FragmentMediaSummaryDtoSchema(only=("media_summary",)).dump(
                        summary
                    ),
                ),
            }
        if suppress_legacy:
            result = {**result, "hasPhoto": False}
        return result
