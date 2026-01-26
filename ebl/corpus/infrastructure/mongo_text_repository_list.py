from typing import List, Sequence, Dict, Union
import pymongo
from ebl.bibliography.infrastructure.bibliography import join_reference_documents
from ebl.corpus.application.schemas import (
    TextSchema,
)
from ebl.corpus.domain.text import Text
from ebl.corpus.infrastructure.queries import (
    join_chapters,
)
from ebl.corpus.infrastructure.mongo_text_repository_base import MongoTextRepositoryBase


class MongoTextRepositoryList(MongoTextRepositoryBase):
    def list(self) -> List[Text]:
        return TextSchema().load(
            self._texts.aggregate(
                [
                    *join_reference_documents(),
                    *join_chapters(False),
                    {
                        "$sort": {
                            "category": pymongo.ASCENDING,
                            "index": pymongo.ASCENDING,
                        }
                    },
                ]
            ),
            many=True,
        )

    def list_all_texts(self) -> Sequence[Dict[str, Union[str, int]]]:
        return list(
            self._texts.aggregate(
                [
                    {
                        "$group": {
                            "_id": {
                                "index": "$index",
                                "category": "$category",
                                "genre": "$genre",
                            }
                        }
                    },
                    {"$replaceRoot": {"newRoot": "$_id"}},
                ]
            )
        )

    def list_all_chapters(self) -> Sequence[Dict[str, Union[str, int]]]:
        return list(
            self._chapters.aggregate(
                [
                    {
                        "$group": {
                            "_id": {
                                "chapter": "$name",
                                "stage": "$stage",
                                "index": "$textId.index",
                                "category": "$textId.category",
                                "genre": "$textId.genre",
                            }
                        }
                    },
                    {"$replaceRoot": {"newRoot": "$_id"}},
                ]
            )
        )
