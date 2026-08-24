from typing import Optional, Sequence

import attr

from ebl.common.domain.scopes import Scope
from ebl.transliteration.domain.museum_number import MuseumNumber


@attr.attrs(auto_attribs=True, frozen=True)
class ImageSource:
    url: str
    mime_type: str
    width: int
    height: int


@attr.attrs(auto_attribs=True, frozen=True)
class RenderingSource:
    url: str
    mime_type: str
    label: str


@attr.attrs(auto_attribs=True, frozen=True)
class MetadataSource:
    label: str
    value: str


@attr.attrs(auto_attribs=True, frozen=True)
class MediaSource:
    media_id: str
    sort_order: int
    canvas_width: int
    canvas_height: int
    painting_image: Optional[ImageSource] = None
    thumbnail_image: Optional[ImageSource] = None
    rendering: Optional[RenderingSource] = None
    label: Optional[str] = None
    attribution: Optional[str] = None
    rights: Optional[str] = None
    is_public: bool = False
    is_primary: bool = False


@attr.attrs(auto_attribs=True, frozen=True)
class FragmentSource:
    number: MuseumNumber
    authorized_scopes: Sequence[Scope] = ()
    media: Sequence[MediaSource] = ()
    metadata: Sequence[MetadataSource] = ()
    summary: Optional[str] = None
    homepage_url: Optional[str] = None
    record_url: Optional[str] = None
