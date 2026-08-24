from typing import Optional, Sequence

import attr

from ebl.iiif.domain.language_map import LanguageMap

IMAGE_SERVICE_TYPE = "ImageService3"
IMAGE_TYPE = "Image"
AGENT_TYPE = "Agent"


@attr.attrs(auto_attribs=True, frozen=True)
class ImageService:
    id: str
    profile: str
    type: str = IMAGE_SERVICE_TYPE


@attr.attrs(auto_attribs=True, frozen=True)
class ImageResource:
    id: str
    format: str
    width: int
    height: int
    service: Sequence[ImageService] = ()
    type: str = IMAGE_TYPE


@attr.attrs(auto_attribs=True, frozen=True)
class ExternalResource:
    id: str
    type: str
    label: Optional[LanguageMap] = None
    format: Optional[str] = None


@attr.attrs(auto_attribs=True, frozen=True)
class Agent:
    id: str
    label: LanguageMap
    homepage: Sequence[ExternalResource] = ()
    type: str = AGENT_TYPE


@attr.attrs(auto_attribs=True, frozen=True)
class MetadataEntry:
    label: LanguageMap
    value: LanguageMap


@attr.attrs(auto_attribs=True, frozen=True)
class RequiredStatement:
    label: LanguageMap
    value: LanguageMap
