from typing import Optional, Sequence, cast

from ebl.media.application.media_schemas import FragmentMediaSummaryDtoSchema
from ebl.media.application.media_service import MediaService
from ebl.media.application.media_summary_dtos import FragmentMediaSummaryDto
from ebl.media.domain import Media
from ebl.transliteration.application.museum_number_schema import MuseumNumberSchema
from ebl.transliteration.domain.museum_number import MuseumNumber


class FragmentMediaEnricher:
    def __init__(self, service: Optional[MediaService] = None) -> None:
        self._service = service

    def enrich(self, document: dict, number: MuseumNumber) -> dict:
        service = self._service
        if service is None:
            return document
        return self._with_media(
            document,
            number,
            service.list_fragment_media(number),
            suppress_legacy=not service.legacy_fallback_allowed(number),
        )

    def enrich_rows(self, documents: Sequence[dict]) -> list[dict]:
        service = self._service
        if service is None or not documents:
            return list(documents)
        numbers = [
            cast(MuseumNumber, MuseumNumberSchema().load(document["museumNumber"]))
            for document in documents
        ]
        media_by_fragment = service.find_media_by_fragments(numbers)
        suppressed = service.suppressed_legacy_fragments(numbers)
        return [
            self._with_media(
                document,
                numbers[index],
                media_by_fragment[numbers[index]],
                suppress_legacy=numbers[index] in suppressed,
            )
            for index, document in enumerate(documents)
        ]

    @staticmethod
    def _with_media(
        document: dict,
        number: MuseumNumber,
        media: Sequence[Media],
        *,
        suppress_legacy: bool = False,
    ) -> dict:
        summary = FragmentMediaSummaryDto.of(number, media)
        result = {
            **document,
            **cast(
                dict,
                FragmentMediaSummaryDtoSchema(only=("media_summary",)).dump(summary),
            ),
        }
        if suppress_legacy:
            primary = summary.media_summary.primary
            result.update(
                legacyHasPhoto=False,
                hasPhoto=summary.has_photo,
                thumbnailPath=(
                    primary.thumbnail.url
                    if primary is not None and primary.thumbnail is not None
                    else None
                ),
            )
        return result
