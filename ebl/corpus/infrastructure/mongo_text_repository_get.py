from typing import Sequence
from ebl.corpus.domain.chapter import ChapterId
from ebl.corpus.infrastructure.queries import (
    chapter_id_query,
)
from ebl.corpus.infrastructure.mongo_text_repository_base import (
    MongoTextRepositoryBase,
    chapter_not_found,
)
from ebl.errors import NotFoundError


class MongoTextRepositoryGet(MongoTextRepositoryBase):
    def get_sign_data(self, id_: ChapterId) -> dict:
        try:
            return self._chapters.find_one(
                chapter_id_query(id_),
                projection={
                    "_id": False,
                    "signs": True,
                    "manuscripts": True,
                    "textId": True,
                    "stage": True,
                    "name": True,
                },
            )
        except NotFoundError as error:
            raise chapter_not_found(id_) from error

    def get_all_sign_data(self) -> Sequence[dict]:
        return list(
            self._chapters.find_many(
                {"signs": {"$regex": "."}, "textId.category": {"$ne": 99}},
                projection={
                    "_id": False,
                    "signs": True,
                    "manuscripts": True,
                    "textId": True,
                    "stage": True,
                    "name": True,
                },
            )
        )
