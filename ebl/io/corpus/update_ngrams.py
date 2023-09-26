import os

from pymongo import MongoClient
from ebl.common.infrastructure.ngrams import NGRAM_N_VALUES
from ebl.corpus.application.id_schemas import ChapterIdSchema

from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from tqdm import tqdm

from ebl.fragmentarium.infrastructure.mongo_fragment_repository import (
    MongoFragmentRepository,
)

from ebl.transliteration.application.museum_number_schema import MuseumNumberSchema

client = MongoClient(os.environ["MONGODB_URI"])
database = client.get_database(os.environ.get("MONGODB_DB"))

DO_CHAPTERS = False
DO_FRAGMENTS = True

text_repository = MongoTextRepository(database)
fragment_repository = MongoFragmentRepository(database)


def update_all_chapter_ngrams():
    chapters_with_signs = [
        ChapterIdSchema().load(id_)
        for id_ in text_repository._chapters.find_many(
            {"signs": {"$exists": 1}},
            projection={"_id": False, "textId": True, "stage": True, "name": True},
        )
    ]

    for id_ in tqdm(chapters_with_signs, total=len(chapters_with_signs)):
        text_repository._update_ngrams(id_)


def update_all_fragment_ngrams():
    fragments_with_signs = [
        MuseumNumberSchema().load(fragment["museumNumber"])
        for fragment in fragment_repository._fragments.find_many(
            {"signs": {"$exists": 1, "$ne": ""}, "ngrams": {"$exists": False}},
            projection={"museumNumber": True},
        )
    ]
    for number in tqdm(fragments_with_signs, total=len(fragments_with_signs)):
        fragment_repository._update_ngrams(number)


if __name__ == "__main__":
    if DO_CHAPTERS:
        print("Updating chapter ngrams with n ∈", NGRAM_N_VALUES)
        update_all_chapter_ngrams()

    if DO_FRAGMENTS:
        print(
            "\nUpdating fragment ngrams with n ∈",
            NGRAM_N_VALUES,
            "(This may take a while.)",
        )
        update_all_fragment_ngrams()
