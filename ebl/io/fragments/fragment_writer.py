from typing import List, Sequence, cast

from ebl.mongo_collection import MongoCollection
from ebl.transliteration.application.storage_serialization import (
    storage_serialization,
)
from ebl.transliteration.application.text_schema import TextSchema


def stored_fragment_of(fragment: dict) -> dict:
    if "text" not in fragment:
        return fragment
    schema = TextSchema()
    with storage_serialization():
        text = cast(dict, schema.dump(schema.load(fragment["text"])))
    return {**fragment, "text": text}


def write_to_db(
    fragments: Sequence[dict], fragments_collection: MongoCollection
) -> List:
    return fragments_collection.insert_many(
        [stored_fragment_of(fragment) for fragment in fragments], ordered=False
    )
