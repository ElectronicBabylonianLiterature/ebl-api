from typing import Mapping

from pymongo.database import Database


def complete_filename_index(indexes: Mapping[str, Mapping]) -> str | None:
    return next(
        (name for name, information in indexes.items() if _complete_index(information)),
        None,
    )


def _complete_index(information: Mapping) -> bool:
    keys = information.get("key", [])
    filename_leading = bool(keys) and keys[0][0] == "filename"
    btree = all(
        direction in (1, -1) and "$**" not in field for field, direction in keys
    )
    complete = "partialFilterExpression" not in information and not any(
        information.get(option) for option in ("sparse", "hidden")
    )
    simple = information.get("collation", {}).get("locale", "simple") == "simple"
    return filename_leading and btree and complete and simple


def prepare_legacy_indexes(database: Database) -> None:
    if not {"fragments", "photos.files"}.issubset(database.list_collection_names()):
        raise ValueError(
            "The explicit database must contain legacy fragments and photos."
        )
    indexes = database["photos.files"].index_information()
    if complete_filename_index(indexes) is None:
        database["photos.files"].create_index(
            "filename",
            name="media_legacy_photo_filename",
            collation={"locale": "simple"},
        )


def assert_apply_ready(database: Database) -> None:
    required = {
        "media": {"media_import_source", "media_fragment_state"},
        "mediaSources": {"media_source_owner"},
        "mediaFiles": {"media_file_recovery"},
        "media.files": {"filename_1_uploadDate_1"},
        "media.chunks": {"files_id_1_n_1"},
    }
    for collection, indexes in required.items():
        if not indexes.issubset(database[collection].index_information()):
            raise ValueError("Run prepare-indexes before applying a media plan.")
    lock = database["mediaLocks"].find_one({"_id": "writes"})
    if lock is None or not isinstance(lock.get("revision"), int):
        raise ValueError("Media transaction coordination must be initialized.")
