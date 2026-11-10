import attr
from typing import Optional

from ebl.media.application.media_service import MediaService
from ebl.media.application.media_store import MediaRepresentationStore
from ebl.media.application.media_management import MediaManagementService


@attr.s(auto_attribs=True, frozen=True)
class MediaRuntime:
    service: MediaService
    store: MediaRepresentationStore
    management: Optional[MediaManagementService] = None
