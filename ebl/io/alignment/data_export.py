from pymongo import MongoClient
from ebl.mongo_collection import MongoCollection
from ebl.transliteration.infrastructure.collections import (
    FRAGMENTS_COLLECTION,
    CHAPTERS_COLLECTION,
)
from ebl.corpus.domain.manuscript import (
    ManuscriptType,
    Provenance,
)
from ebl.common.domain.period import Period
import os
import tarfile
import pandas as pd
import datetime

# disable false positive SettingsWithCopyWarning
pd.options.mode.chained_assignment = None

client = MongoClient(os.environ["MONGODB_URI"])
DB = os.environ.get("MONGODB_DB")
database = client.get_database(DB)
fragments = MongoCollection(database, FRAGMENTS_COLLECTION)
chapters = MongoCollection(database, CHAPTERS_COLLECTION)

tmp_path = "/tmp/alignment_output"
os.makedirs(tmp_path, exist_ok=True)


def enum_mapping(enum):
    return {enum_item.long_name: enum_item.abbreviation for enum_item in enum}


if __name__ == "__main__":
    df_fragments = None
    df_chapters = None

    print(f"Writing data to {tmp_path}...")
    print("Exporting fragments...")

    fragment_signs = fragments.find_many(
        {"signs": {"$exists": True, "$ne": ""}}, projection={"signs": True}
    )
    df_fragments = pd.DataFrame.from_records(fragment_signs)

    # exclude signs without clear signs
    df_fragments = df_fragments[~df_fragments.signs.str.fullmatch(r"[X\s]*")]

    df_fragments.to_csv(
        os.path.join(tmp_path, "fragment_signs.tsv"), index=False, sep="\t"
    )

    print("Exporting chapters...")

    siglum_columns = ["provenance", "period", "type", "disambiguator"]
    siglum_enums = [Provenance, Period, ManuscriptType]

    abbreviation_mappings = dict(zip(siglum_columns, siglum_enums))

    chapter_signs = chapters.aggregate(
        [
            {
                "$project": {
                    "manuscripts": {"$zip": {"inputs": ["$manuscripts", "$signs"]}}
                }
            },
            {"$unwind": "$manuscripts"},
            {
                "$project": {
                    "manuscript": {"$first": "$manuscripts"},
                    "signs": {"$last": "$manuscripts"},
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "id": {"$toString": "$_id"},
                    "provenance": "$manuscript.provenance",
                    "period": "$manuscript.period",
                    "type": "$manuscript.type",
                    "disambiguator": "$manuscript.siglumDisambiguator",
                    "signs": 1,
                }
            },
        ]
    )
    df_chapters = pd.DataFrame.from_records(chapter_signs)

    # exclude signs without clear signs
    df_chapters["signs"] = df_chapters["signs"].fillna("")
    df_chapters = df_chapters[~df_chapters.signs.str.fullmatch(r"[X\s]*")]

    # map long names to abbreviations
    for column, enum in abbreviation_mappings.items():
        df_chapters[column] = df_chapters[column].map(enum_mapping(enum))

    df_chapters["siglum"] = df_chapters[siglum_columns].agg("".join, axis=1)
    df_chapters = df_chapters[
        [
            "id",
            "siglum",
            "signs",
        ]
    ]

    df_chapters.to_csv(
        os.path.join(tmp_path, "chapter_signs.tsv"), index=False, sep="\t"
    )

    tar_path = os.path.join(
        os.path.dirname(__file__), f"alignment_data_{datetime.date.today()}.tar.gz"
    )

    print(f"Storing archive in '{tar_path}'...")

    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(tmp_path, arcname=os.path.basename(tmp_path))

    print("Done.")
