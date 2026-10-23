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
        if self._service is None:
            return document
        return self._with_media(
            document, number, self._service.list_fragment_media(number)
        )

    def enrich_rows(self, documents: Sequence[dict]) -> list[dict]:
        if self._service is None or not documents:
            return list(documents)
        numbers = [
            cast(MuseumNumber, MuseumNumberSchema().load(document["museumNumber"]))
            for document in documents
        ]
        media_by_fragment = self._service.find_media_by_fragments(numbers)
        return [
            self._with_media(
                document, numbers[index], media_by_fragment[numbers[index]]
            )
            for index, document in enumerate(documents)
        ]

    @staticmethod
    def _with_media(
        document: dict, number: MuseumNumber, media: Sequence[Media]
    ) -> dict:
        summary = FragmentMediaSummaryDto.of(number, media)
        result = {
            **document,
            **cast(dict, FragmentMediaSummaryDtoSchema().dump(summary)),
        }
        result["legacyHasPhoto"] = bool(document.get("hasPhoto"))
        result["hasPhoto"] = result["legacyHasPhoto"] or summary.has_photo
        result["thumbnailPath"] = document.get("thumbnailPath", summary.thumbnail_path)
        return result
