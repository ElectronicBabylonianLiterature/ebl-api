from typing import Optional, Sequence

import attr

from ebl.iiif.domain.language_map import LanguageMap
from ebl.iiif.domain.resources import ExternalResource, ImageResource

CANVAS_TYPE = "Canvas"
ANNOTATION_PAGE_TYPE = "AnnotationPage"
ANNOTATION_TYPE = "Annotation"
PAINTING_MOTIVATION = "painting"


@attr.attrs(auto_attribs=True, frozen=True)
class PaintingAnnotation:
    id: str
    target: str
    body: ImageResource
    motivation: str = PAINTING_MOTIVATION
    type: str = ANNOTATION_TYPE


@attr.attrs(auto_attribs=True, frozen=True)
class AnnotationPage:
    id: str
    items: Sequence[PaintingAnnotation]
    type: str = ANNOTATION_PAGE_TYPE


@attr.attrs(auto_attribs=True, frozen=True)
class Canvas:
    id: str
    width: int
    height: int
    items: Sequence[AnnotationPage]
    label: Optional[LanguageMap] = None
    thumbnail: Sequence[ImageResource] = ()
    rendering: Sequence[ExternalResource] = ()
    rights: Optional[str] = None
    type: str = CANVAS_TYPE
