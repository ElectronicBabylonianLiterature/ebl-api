from typing import Sequence

import attr
from pymongo.database import Database


@attr.s(auto_attribs=True, frozen=True)
class MediaIndexDefinition:
    collection: str
    name: str
    keys: tuple[tuple[str, int], ...]
    unique: bool = False
    implicit: bool = False
    collation: str = "simple"


MEDIA_REPOSITORY_INDEXES = (
    MediaIndexDefinition("media", "media_import_source", (("sourceKey", 1),)),
    MediaIndexDefinition(
        "media",
        "media_fragment_state",
        (("associations.fragmentId", 1), ("state", 1)),
    ),
    MediaIndexDefinition("mediaSources", "media_source_owner", (("mediaId", 1),)),
)
MEDIA_STORE_INDEXES = (
    MediaIndexDefinition(
        "mediaFiles", "media_file_recovery", (("ownership", 1), ("ready", 1))
    ),
    MediaIndexDefinition(
        "media.files", "filename_1_uploadDate_1", (("filename", 1), ("uploadDate", 1))
    ),
    MediaIndexDefinition(
        "media.chunks", "files_id_1_n_1", (("files_id", 1), ("n", 1)), unique=True
    ),
)
MEDIA_REQUIRED_INDEXES = (
    *MEDIA_REPOSITORY_INDEXES,
    *MEDIA_STORE_INDEXES,
    *(
        MediaIndexDefinition(
            collection, "_id_", (("_id", 1),), unique=True, implicit=True
        )
        for collection in (
            "media",
            "mediaSources",
            "mediaLocks",
            "mediaFiles",
            "media.files",
            "media.chunks",
        )
    ),
)


def create_media_indexes(
    database: Database, definitions: Sequence[MediaIndexDefinition]
) -> None:
    for definition in definitions:
        if not definition.implicit:
            database[definition.collection].create_index(
                list(definition.keys),
                name=definition.name,
                unique=definition.unique,
                collation={"locale": definition.collation},
            )
