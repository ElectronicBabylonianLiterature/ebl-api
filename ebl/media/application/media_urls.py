"""URL builders for the future fragment-scoped media routes.

The media routes these build are not registered yet:

    GET /fragments/{number}/media/{mediaId}/file
    GET /fragments/{number}/media/{mediaId}/display
    GET /fragments/{number}/media/{mediaId}/thumbnail/{size}

Every builder here is the single place a media path is spelled, so the
templates cannot drift copy by copy. That does not remove the drift risk, it
concentrates it: when the routes are registered, add a test asserting the
registered Falcon templates and these builders agree.

Encoding policy: the media builders percent-encode every dynamic path segment.
`legacy_fragment_thumbnail_url` deliberately does not, because it reproduces an
existing public contract byte for byte. The two therefore disagree for a museum
number containing a slash — `MuseumNumber("A/B", "1")` yields
`/fragments/A/B.1/thumbnail/small`, an extra path segment that will not
round-trip through a `{museum_number}` template. That asymmetry is load-bearing
and must be settled by whoever migrates the legacy `thumbnailPath` contract, not
silently corrected here.
"""

from urllib.parse import quote

from ebl.media.domain import MediaId, ThumbnailSize
from ebl.transliteration.domain.museum_number import MuseumNumber


def _path_segment(value: object) -> str:
    return quote(str(value), safe="")


def fragment_media_original_url(fragment_id: MuseumNumber, media_id: MediaId) -> str:
    return (
        f"/fragments/{_path_segment(fragment_id)}/media/{_path_segment(media_id)}/file"
    )


def fragment_media_display_url(fragment_id: MuseumNumber, media_id: MediaId) -> str:
    return (
        f"/fragments/{_path_segment(fragment_id)}/media/"
        f"{_path_segment(media_id)}/display"
    )


def fragment_media_thumbnail_url(
    fragment_id: MuseumNumber, media_id: MediaId, size: ThumbnailSize
) -> str:
    return (
        f"/fragments/{_path_segment(fragment_id)}/media/{_path_segment(media_id)}"
        f"/thumbnail/{_path_segment(size.value)}"
    )


def legacy_fragment_thumbnail_url(
    fragment_id: MuseumNumber, size: ThumbnailSize
) -> str:
    return f"/fragments/{fragment_id}/thumbnail/{size.value}"
