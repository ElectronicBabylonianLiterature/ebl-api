import hashlib
from io import BytesIO

import attr
from PIL import Image
from pymongo.database import Database
from pymongo import monitoring

from ebl.context import Context
from ebl.media.application.media_runtime import MediaRuntime
from ebl.media.application.media_stored import (
    OriginalRepresentationWriteRequest,
    StoredMedia,
    StoredMediaRepresentations,
)
from ebl.media.domain import MediaChecksum, MediaRepresentation, MediaRepresentations
from ebl.media.infrastructure.mongo_media_repository import MongoMediaRepository
from ebl.media.web.bootstrap import create_media_runtime
from ebl.tests.factories.fragment import FragmentFactory
from ebl.tests.media.factories import association, photo_media
from ebl.transliteration.domain.museum_number import MuseumNumber


def png_bytes() -> bytes:
    content = BytesIO()
    Image.new("RGB", (2, 3), "red").save(content, format="PNG")
    return content.getvalue()


def seed_runtime(
    database: Database, context: Context
) -> tuple[MediaRuntime, StoredMedia]:
    repository = MongoMediaRepository(database)
    repository.create_indexes()
    runtime = create_media_runtime(database)
    number = MuseumNumber.of("A/B.1")
    context.fragment_repository.create(
        FragmentFactory.build(number=number, references=())
    )
    content = png_bytes()
    representation = MediaRepresentation(
        "image/png",
        2,
        3,
        len(content),
        MediaChecksum(value=hashlib.sha256(content).hexdigest()),
    )
    media = photo_media(
        associations=(association(fragment_id=number, is_primary=False),),
        media_representations=MediaRepresentations(representation),
    )
    handle = runtime.store.write_original(
        OriginalRepresentationWriteRequest(media.id, BytesIO(content), representation)
    )
    stored = StoredMedia(media, StoredMediaRepresentations(handle))
    repository.create(stored)
    return runtime, stored


def context_with_media(context: Context, runtime: MediaRuntime) -> Context:
    return attr.evolve(context, media=runtime)


class MediaReadCounter(monitoring.CommandListener):
    def __init__(self) -> None:
        self.count = 0

    def started(self, event: monitoring.CommandStartedEvent) -> None:
        if event.command.get("find") == "media":
            self.count += 1

    def succeeded(self, event: monitoring.CommandSucceededEvent) -> None:
        pass

    def failed(self, event: monitoring.CommandFailedEvent) -> None:
        pass
