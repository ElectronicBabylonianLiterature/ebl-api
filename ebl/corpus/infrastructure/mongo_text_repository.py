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
    pass
