from typing import Optional, Sequence

from ebl.iiif.application.iiif_identifiers import IiifIdentifierFactory
from ebl.iiif.application.image_service import ImageServiceLocator
from ebl.iiif.application.manifest_sources import (
    ImageSource,
    MediaSource,
    RenderingSource,
)
from ebl.iiif.domain.canvas import AnnotationPage, Canvas, PaintingAnnotation
from ebl.iiif.domain.language_map import LanguageMap
from ebl.iiif.domain.resources import (
    ExternalResource,
    ImageResource,
    ImageService,
)
from ebl.transliteration.domain.museum_number import MuseumNumber

RENDERING_TYPE = "Image"


class CanvasBuilder:
    def __init__(
        self,
        identifiers: IiifIdentifierFactory,
        image_services: ImageServiceLocator,
    ):
        self._identifiers = identifiers
        self._image_services = image_services

    def build(self, number: MuseumNumber, media: MediaSource) -> Canvas:
        canvas_id = self._identifiers.canvas(number, media.media_id)
        return Canvas(
            id=canvas_id,
            width=media.canvas_width,
            height=media.canvas_height,
            items=[self._painting_page(number, media, canvas_id)],
            label=LanguageMap.optional(media.label),
            thumbnail=self._thumbnail(media.thumbnail_image),
            rendering=self._rendering(media.rendering),
            rights=media.rights,
        )

    def _painting_page(
        self, number: MuseumNumber, media: MediaSource, canvas_id: str
    ) -> AnnotationPage:
        return AnnotationPage(
            id=self._identifiers.painting_page(number, media.media_id),
            items=[
                PaintingAnnotation(
                    id=self._identifiers.painting_annotation(number, media.media_id),
                    target=canvas_id,
                    body=self._painting_body(media),
                )
            ],
        )

    def _painting_body(self, media: MediaSource) -> ImageResource:
        painting_image = media.painting_image
        if painting_image is None:
            raise ValueError(
                f"Media {media.media_id} has no paintable image representation."
            )
        return ImageResource(
            id=painting_image.url,
            format=painting_image.mime_type,
            width=painting_image.width,
            height=painting_image.height,
            service=self._image_services_for(media.media_id),
        )

    def _image_services_for(self, media_id: str) -> Sequence[ImageService]:
        service = self._image_services.service_for(media_id)
        return () if service is None else [service]

    @staticmethod
    def _thumbnail(thumbnail: Optional[ImageSource]) -> Sequence[ImageResource]:
        return (
            ()
            if thumbnail is None
            else [
                ImageResource(
                    id=thumbnail.url,
                    format=thumbnail.mime_type,
                    width=thumbnail.width,
                    height=thumbnail.height,
                )
            ]
        )

    @staticmethod
    def _rendering(rendering: Optional[RenderingSource]) -> Sequence[ExternalResource]:
        return (
            ()
            if rendering is None
            else [
                ExternalResource(
                    id=rendering.url,
                    type=RENDERING_TYPE,
                    label=LanguageMap.of(rendering.label, "en"),
                    format=rendering.mime_type,
                )
            ]
        )
