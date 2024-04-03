from typing import Sequence

from ebl.fragmentarium.domain.fragment import Fragment
from ebl.fragmentarium.domain.joins import Join
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.application.fragment_schema import FragmentSchema
from ebl.fragmentarium.application.joins_schema import JoinSchema


class MongoFragmentRepositoryCreate(FragmentRepository):
    def create(self, fragment, sort_key=None):
        return self._fragments.insert_one(
            {
                "_id": str(fragment.number),
                **FragmentSchema(exclude=["joins"]).dump(fragment),
                **({} if sort_key is None else {"_sortKey": sort_key}),
            }
        )

    def create_many(self, fragments: Sequence[Fragment]) -> Sequence[str]:
        schema = FragmentSchema(exclude=["joins"])
        return self._fragments.insert_many(
            [
                {"_id": str(fragment.number), **schema.dump(fragment)}
                for fragment in fragments
            ]
        )

    def create_join(self, joins: Sequence[Sequence[Join]]) -> None:
        self._joins.insert_one(
            {
                "fragments": [
                    {
                        **JoinSchema(exclude=["is_in_fragmentarium"]).dump(join),
                        "group": index,
                    }
                    for index, group in enumerate(joins)
                    for join in group
                ]
            }
        )
