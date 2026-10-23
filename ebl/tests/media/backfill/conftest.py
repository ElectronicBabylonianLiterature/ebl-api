import io
from collections.abc import Callable, Iterator

import pytest
from bson import ObjectId
from gridfs import GridFS
from PIL import Image
from pymongo.database import Database

from ebl.media.application.backfill_plan import BackfillPolicy
from ebl.media.infrastructure.backfill_runner import LegacyPhotoMigration
from ebl.media.infrastructure.backfill_sources import LegacyPhotoSources
from ebl.media.infrastructure.grid_fs_media_representation_store import (
    GridFsMediaRepresentationStore,
)
from ebl.media.infrastructure.mongo_media_repository import MongoMediaRepository


def image_bytes(
    format_: str = "JPEG", size: tuple[int, int] = (16, 12), exif: bytes = b""
) -> bytes:
    with Image.new("RGB", size, "red") as image:
        content = io.BytesIO()
        image.save(content, format=format_, exif=exif)
        return content.getvalue()


@pytest.fixture
def legacy_photo(database: Database) -> Callable:
    def create(
        filename: str = "K.1.jpg",
        content: bytes | None = None,
        file_id: ObjectId | str | int | None = None,
        create_fragment: bool = True,
    ) -> dict:
        if create_fragment:
            database["fragments"].update_one(
                {"_id": "K.1"},
                {
                    "$setOnInsert": {
                        "museumNumber": {"prefix": "K", "number": "1", "suffix": ""}
                    }
                },
                upsert=True,
            )
        identifier = GridFS(database, "photos").put(
            image_bytes() if content is None else content,
            filename=filename,
            _id=ObjectId() if file_id is None else file_id,
        )
        document = database["photos.files"].find_one({"_id": identifier})
        assert document is not None
        return document

    return create


@pytest.fixture
def migration_factory(database: Database) -> Callable:
    def create(
        policy: BackfillPolicy | None = None, initialize: bool = True
    ) -> LegacyPhotoMigration:
        repository = MongoMediaRepository(database)
        store = GridFsMediaRepresentationStore(database)
        if initialize:
            repository.create_indexes()
            store.create_indexes()
        return LegacyPhotoMigration(
            LegacyPhotoSources(database), repository, store, policy or BackfillPolicy()
        )

    return create


@pytest.fixture
def command_output() -> Iterator[io.StringIO]:
    with io.StringIO() as output:
        yield output
