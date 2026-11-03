from typing import Sequence, cast

from ebl.fragmentarium.domain.fragment import Fragment
from ebl.fragmentarium.domain.joins import Join
from ebl.fragmentarium.application.joins_schema import JoinSchema
from ebl.fragmentarium.infrastructure.mongo_fragment_repository_base import (
    MongoFragmentRepositoryBase,
)
from ebl.transliteration.application.storage_serialization import (
    storage_serialization,
)


class MongoFragmentRepositoryCreate(MongoFragmentRepositoryBase):
    def create(self, fragment, sort_key=None):
        with storage_serialization():
            document = cast(dict, self._schema(exclude=["joins"]).dump(fragment))
        return self._fragments.insert_one(
            {
                "_id": str(fragment.number),
                **document,
                **({} if sort_key is None else {"_sortKey": sort_key}),
            }
        )

    def create_many(self, fragments: Sequence[Fragment]) -> Sequence[str]:
        schema = self._schema(exclude=["joins"])
        with storage_serialization():
            documents = [
                {"_id": str(fragment.number), **cast(dict, schema.dump(fragment))}
                for fragment in fragments
            ]
        return self._fragments.insert_many(documents)

    def create_join(self, joins: Sequence[Sequence[Join]]) -> None:
        self._joins.insert_one(
            {
                "fragments": [
                    {
                        **cast(
                            dict, JoinSchema(exclude=["is_in_fragmentarium"]).dump(join)
                        ),
                        "group": index,
                    }
                    for index, group in enumerate(joins)
                    for join in group
                ]
            }
        )
