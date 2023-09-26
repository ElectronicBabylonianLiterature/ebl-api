import os

from pymongo import MongoClient
from ebl.corpus.application.id_schemas import ChapterIdSchema

from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from tqdm import tqdm


client = MongoClient(os.environ["MONGODB_URI"])
database = client.get_database(os.environ.get("MONGODB_DB"))

text_repository = MongoTextRepository(database)


chapters_with_signs = [
    ChapterIdSchema().load(id_)
    for id_ in text_repository._chapters.find_many(
        {"signs": {"$exists": 1, "$ne": ""}},
        projection={"_id": False, "textId": True, "stage": True, "name": True},
    )
]

for id_ in tqdm(chapters_with_signs, total=len(chapters_with_signs)):
    text_repository._update_ngrams(id_)
