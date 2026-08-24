from typing import Iterable, Optional, Sequence, Set

from ebl.common.domain.scopes import Scope
from ebl.iiif.application.manifest_sources import FragmentSource, MediaSource
from ebl.iiif.domain.image_formats import is_paintable


def is_fragment_publicly_readable(authorized_scopes: Sequence[Scope]) -> bool:
    return not authorized_scopes


def has_paintable_representation(media: MediaSource) -> bool:
    painting_image = media.painting_image
    return (
        painting_image is not None
        and is_paintable(painting_image.mime_type)
        and media.canvas_width > 0
        and media.canvas_height > 0
    )


def is_media_publishable(media: MediaSource) -> bool:
    return (
        media.is_public
        and media.rights is not None
        and has_paintable_representation(media)
    )


def _distinct(values: Iterable[Optional[str]]) -> Set[Optional[str]]:
    return set(values)


def _single(values: Iterable[Optional[str]]) -> Optional[str]:
    distinct = _distinct(values)
    return distinct.pop() if len(distinct) == 1 else None


class IiifPublicationPolicy:
    def publishable_media(self, fragment: FragmentSource) -> Sequence[MediaSource]:
        if not is_fragment_publicly_readable(fragment.authorized_scopes):
            return ()
        return tuple(
            sorted(
                (media for media in fragment.media if is_media_publishable(media)),
                key=lambda media: (media.sort_order, media.media_id),
            )
        )

    def has_uniform_terms(self, media: Sequence[MediaSource]) -> bool:
        return (
            len(_distinct(item.rights for item in media)) == 1
            and len(_distinct(item.attribution for item in media)) == 1
        )

    def is_fragment_published(self, fragment: FragmentSource) -> bool:
        publishable = self.publishable_media(fragment)
        return bool(publishable) and self.has_uniform_terms(publishable)

    def common_rights(self, media: Sequence[MediaSource]) -> Optional[str]:
        return _single(item.rights for item in media)

    def common_attribution(self, media: Sequence[MediaSource]) -> Optional[str]:
        return _single(item.attribution for item in media)
