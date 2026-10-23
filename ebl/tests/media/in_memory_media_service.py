from typing import Optional

from ebl.media.application.default_media_service import DefaultMediaService
from ebl.media.application.media_repository import MediaRepository
from ebl.media.application.media_store import MediaRepresentationStore
from ebl.tests.media.in_memory_media import InMemoryRepresentationStore


class InMemoryMediaService(DefaultMediaService):
    def __init__(
        self,
        repository: MediaRepository,
        representation_store: Optional[MediaRepresentationStore] = None,
    ) -> None:
        super().__init__(
            repository, representation_store or InMemoryRepresentationStore()
        )
