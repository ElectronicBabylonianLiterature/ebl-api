import re
from typing import Iterator, Mapping

from bson import ObjectId, json_util
from pymongo.database import Database
from pymongo.read_preferences import ReadPreference

from ebl.media.application.backfill_plan import SourceRejected
from ebl.media.application.media_requests import BackfillRequest
from ebl.media.infrastructure.backfill_preflight import complete_filename_index
from ebl.transliteration.domain.museum_number import MuseumNumber


def encode_source_id(source_id: object) -> str:
    return json_util.dumps(
        {"id": source_id}, json_options=json_util.CANONICAL_JSON_OPTIONS, sort_keys=True
    )


def decode_source_id(source_id: str) -> object:
    return json_util.loads(source_id)["id"]


def metadata_snapshot(document: Mapping) -> str:
    return json_util.dumps(
        document, json_options=json_util.CANONICAL_JSON_OPTIONS, sort_keys=True
    )


class LegacyPhotoSources:
    def __init__(self, database: Database) -> None:
        self.database = database.with_options(read_preference=ReadPreference.PRIMARY)
        self.files = self.database["photos.files"]
        self._filename_index: str | None = None

    def filename_index(self) -> str:
        existing = self._filename_index
        if existing is not None:
            return existing
        name = complete_filename_index(self.files.index_information())
        if name is None:
            raise ValueError(
                "Legacy photos need a complete filename-leading index before scanning."
            )
        self._filename_index = name
        return name

    def batch(self, request: BackfillRequest) -> Iterator[dict]:
        query = (
            {
                "$expr": {
                    "$gt": [
                        "$_id",
                        {"$literal": decode_source_id(request.resume_after)},
                    ]
                }
            }
            if request.resume_after is not None
            else {}
        )
        yield from self.files.find(query).sort("_id", 1).limit(request.batch_size)

    def mapping(self, document: Mapping) -> MuseumNumber:
        if not isinstance(document.get("_id"), (str, ObjectId)):
            raise SourceRejected("blocked", "unsupported-source-id-type")
        filename = document.get("filename")
        if not isinstance(filename, str):
            raise SourceRejected("blocked", "missing-filename")
        match = re.fullmatch(r"(.+)\.(jpg|jpeg|png|webp)", filename, re.IGNORECASE)
        if match is None:
            raise SourceRejected("blocked", "unsupported-filename")
        try:
            fragment = MuseumNumber.of(match[1])
        except ValueError as error:
            raise SourceRejected("blocked", "ambiguous-filename") from error
        fragment_query = {
            "museumNumber.prefix": fragment.prefix,
            "museumNumber.number": fragment.number,
            "museumNumber.suffix": fragment.suffix,
        }
        if self.database["fragments"].count_documents(fragment_query, limit=2) != 1:
            raise SourceRejected("blocked", "unknown-or-ambiguous-fragment")
        competing = re.compile(rf"^{re.escape(str(fragment))}\.[^.]+$")
        if (
            self.files.count_documents(
                {"filename": competing},
                limit=2,
                hint=self.filename_index(),
                collation={"locale": "simple"},
            )
            != 1
        ):
            raise SourceRejected("review", "multiple-originals")
        return fragment

    def unchanged(self, document: Mapping) -> bool:
        current = self.files.find_one({"_id": document["_id"]})
        return current is not None and metadata_snapshot(current) == metadata_snapshot(
            document
        )
