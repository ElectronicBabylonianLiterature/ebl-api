from typing import Optional, Sequence

import attr

from ebl.common.domain.scopes import Scope
from ebl.iiif.application.fragment_identity import ProvisionalMuseumNumberIdentity
from ebl.iiif.application.iiif_identifiers import IiifIdentifierFactory
from ebl.iiif.application.image_service import LEVEL_TWO, ImageServiceLocator
from ebl.iiif.application.manifest_sources import (
    FragmentSource,
    ImageSource,
    MediaSource,
    MetadataSource,
    RenderingSource,
)
from ebl.iiif.domain.resources import ImageService
from ebl.transliteration.domain.museum_number import MuseumNumber

BASE_URL = "https://api.example.org"
RIGHTS = "http://rightsstatements.org/vocab/InC-EDU/1.0/"
ATTRIBUTION = "The British Museum"
MEDIA_ID = "550e8400-e29b-41d4-a716-446655440000"
OTHER_MEDIA_ID = "550e8400-e29b-41d4-a716-446655440001"


def identifiers(base_url: str = BASE_URL) -> IiifIdentifierFactory:
    return IiifIdentifierFactory(base_url, ProvisionalMuseumNumberIdentity())


def image_source(
    url: str = f"{BASE_URL}/image.jpg",
    mime_type: str = "image/jpeg",
    width: int = 2000,
    height: int = 1500,
) -> ImageSource:
    return ImageSource(url=url, mime_type=mime_type, width=width, height=height)


def rendering_source() -> RenderingSource:
    return RenderingSource(
        url=f"{BASE_URL}/copy.svg",
        mime_type="image/svg+xml",
        label="Original SVG hand copy",
    )


def media_source(media_id: str = MEDIA_ID, **overrides) -> MediaSource:
    media = MediaSource(
        media_id=media_id,
        sort_order=0,
        canvas_width=4000,
        canvas_height=3000,
        painting_image=image_source(),
        thumbnail_image=image_source(f"{BASE_URL}/thumb.jpg", width=240, height=180),
        label="Obverse",
        attribution=ATTRIBUTION,
        rights=RIGHTS,
        is_public=True,
        is_primary=True,
    )
    return attr.evolve(media, **overrides) if overrides else media


def fragment_source(
    number: str = "K.1",
    media: Optional[Sequence[MediaSource]] = None,
    authorized_scopes: Sequence[Scope] = (),
    metadata: Sequence[MetadataSource] = (),
    summary: Optional[str] = None,
    homepage_url: Optional[str] = None,
    record_url: Optional[str] = None,
) -> FragmentSource:
    return FragmentSource(
        number=MuseumNumber.of(number),
        authorized_scopes=authorized_scopes,
        media=(media_source(),) if media is None else tuple(media),
        metadata=tuple(metadata),
        summary=summary,
        homepage_url=homepage_url,
        record_url=record_url,
    )


class StubImageService(ImageServiceLocator):
    def service_for(self, media_id: str) -> Optional[ImageService]:
        return ImageService(id=f"{BASE_URL}/iiif/3/image/{media_id}", profile=LEVEL_TWO)


class MissingImageService(ImageServiceLocator):
    def service_for(self, media_id: str) -> Optional[ImageService]:
        return None
