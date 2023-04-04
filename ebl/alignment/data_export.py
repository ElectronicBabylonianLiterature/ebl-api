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
import pandas as pd
import numpy as np

# disable false positive SettingsWithCopyWarning
pd.options.mode.chained_assignment = None

client = MongoClient(os.environ["MONGODB_URI"])
DB = os.environ.get("MONGODB_DB")
database = client.get_database(DB)
fragments = MongoCollection(database, FRAGMENTS_COLLECTION)
chapters = MongoCollection(database, CHAPTERS_COLLECTION)

output_path = "/workspace/ebl-api/ebl/alignment/output"

os.makedirs(output_path, exist_ok=True)


def enum_mapping(enum):
    return {enum_item.long_name: enum_item.abbreviation for enum_item in enum}


if __name__ == "__main__":
    df_fragments = None
    df_chapters = None

    print("Exporting fragments...")

    fragment_signs = fragments.find_many(
        {"signs": {"$exists": True, "$ne": ""}}, projection={"signs": True}
    )
    df_fragments = pd.DataFrame.from_records(fragment_signs)

    # exclude signs without clear signs
    df_fragments = df_fragments[~df_fragments.signs.str.fullmatch(r"[X\s]*")]

    df_fragments.to_csv(
        os.path.join(output_path, "fragment_signs.tsv"), index=False, sep="\t"
    )

    print("Exporting chapters...")

    siglum_columns = ["provenance", "period", "type", "disambiguator"]
    siglum_enums = [Provenance, Period, ManuscriptType]

    abbreviation_mappings = {
        column_name: enum for column_name, enum in zip(siglum_columns, siglum_enums)
    }

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
        os.path.join(output_path, "chapter_signs.tsv"), index=False, sep="\t"
    )

    print("Creating vocabulary...")
    frames = [frame for frame in (df_fragments, df_chapters) if frame is not None]

    all_signs = pd.concat(frames)["signs"].str.split().explode().unique()
    _, codes = np.unique(all_signs, return_inverse=True)

    df = pd.DataFrame({"sign": all_signs, "code": codes})
    df.to_csv(os.path.join(output_path, "vocabulary.tsv"), index=False, sep="\t")
