import attr

from ebl.media.application.media_service import MediaService
from ebl.media.application.media_store import MediaRepresentationStore


@attr.s(auto_attribs=True, frozen=True)
class MediaRuntime:
    service: MediaService
    store: MediaRepresentationStore
