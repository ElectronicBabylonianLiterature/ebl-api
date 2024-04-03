import pymongo
from ebl.fragmentarium.infrastructure.mongo_fragment_repository_create import (
    MongoFragmentRepositoryCreate,
)
from ebl.fragmentarium.infrastructure.mongo_fragment_repository_get import (
    MongoFragmentRepositoryGet,
)
from ebl.fragmentarium.infrastructure.queries import (
    HAS_TRANSLITERATION,
    fragment_is,
)
from ebl.fragmentarium.application.fragment_schema import FragmentSchema


class MongoFragmentRepository(
    MongoFragmentRepositoryCreate, MongoFragmentRepositoryGet
):
    def __init__(self, database):
        super().__init__(database)

    def create_indexes(self) -> None:
        self._fragments.create_index(
            [
                ("museumNumber.prefix", pymongo.ASCENDING),
                ("museumNumber.number", pymongo.ASCENDING),
                ("museumNumber.suffix", pymongo.ASCENDING),
            ],
            unique=True,
        )
        self._fragments.create_index([("accession", pymongo.ASCENDING)])
        self._fragments.create_index(
            [("externalNumbers.cdliNumber", pymongo.ASCENDING)]
        )
        self._fragments.create_index([("folios.name", pymongo.ASCENDING)])
        self._fragments.create_index(
            [
                ("text.lines.content.value", pymongo.ASCENDING),
                ("text.lines.content.uniqueLemma.0", pymongo.ASCENDING),
            ]
        )
        self._fragments.create_index([("text.lines.type", pymongo.ASCENDING)])
        self._fragments.create_index([("record.type", pymongo.ASCENDING)])
        self._fragments.create_index(
            [
                ("publication", pymongo.ASCENDING),
                ("joins", pymongo.ASCENDING),
                ("collection", pymongo.ASCENDING),
            ]
        )
        self._fragments.create_index([("_sortKey", pymongo.ASCENDING)])
        self._joins.create_index(
            [
                ("fragments.museumNumber.prefix", pymongo.ASCENDING),
                ("fragments.museumNumber.number", pymongo.ASCENDING),
                ("fragments.museumNumber.suffix", pymongo.ASCENDING),
            ]
        )

    def count_transliterated_fragments(self, only_authorized=False) -> int:
        query = HAS_TRANSLITERATION
        if only_authorized:
            query = query | {"authorizedScopes": {"$exists": False}}
        return self._fragments.count_documents(query)

    def count_lines(self):
        result = self._fragments.aggregate(
            [{"$group": {"_id": None, "total": {"$sum": "$text.numberOfLines"}}}]
        )
        try:
            return next(result)["total"]
        except StopIteration:
            return 0

    def update_field(self, field, fragment):
        fields_to_update = {
            "introduction": ("introduction",),
            "lemmatization": ("text",),
            "genres": ("genres",),
            "references": ("references",),
            "script": ("script",),
            "notes": ("notes",),
            "archaeology": ("archaeology",),
            "transliteration": (
                "text",
                "signs",
                "record",
                "line_to_vec",
            ),
            "date": ("date",),
            "dates_in_text": ("dates_in_text",),
        }

        if field not in fields_to_update:
            raise ValueError(
                f"Unexpected update field {field}, must be one of {','.join(fields_to_update)}"
            )
        query = FragmentSchema(only=fields_to_update[field]).dump(fragment)
        self._fragments.update_one(
            fragment_is(fragment),
            {"$set": query if query else {field: None}},
        )
