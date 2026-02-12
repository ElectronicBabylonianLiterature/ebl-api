from ebl.corpus.infrastructure.mongo_text_repository_find import MongoTextRepositoryFind
from ebl.corpus.infrastructure.mongo_text_repository_get import MongoTextRepositoryGet
from ebl.corpus.infrastructure.mongo_text_repository_list import MongoTextRepositoryList
from ebl.corpus.infrastructure.mongo_text_repository_modify import (
    MongoTextRepositoryModify,
)
from ebl.corpus.infrastructure.mongo_text_repository_query import (
    MongoTextRepositoryQuery,
)


class MongoTextRepository(
    MongoTextRepositoryFind,
    MongoTextRepositoryGet,
    MongoTextRepositoryList,
    MongoTextRepositoryModify,
    MongoTextRepositoryQuery,
):
    def __init__(self, database, provenance_service):
        super().__init__(database, provenance_service)
