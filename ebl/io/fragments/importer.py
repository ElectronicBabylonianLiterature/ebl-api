from itertools import count
from typing import Optional, Sequence, cast
import json
from marshmallow import ValidationError
import pymongo
from ebl.common.query.util import sort_by_museum_number
from ebl.fragmentarium.application.fragment_schema import FragmentSchema
from ebl.provenance.application.provenance_service import ProvenanceService
from ebl.mongo_collection import MongoCollection
from ebl.transliteration.application.token_schemas import WORD_SCHEMAS
from ebl.transliteration.domain.museum_number import MuseumNumber
import csv
from copy import deepcopy

WORD_TYPES = set(WORD_SCHEMAS)


def _load_json(path: str):
    with open(path) as jsonfile:
        try:
            return json.load(jsonfile)
        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid JSON: {path}") from error


def assert_type(obj, expected_type, prefix=""):
    if not isinstance(obj, expected_type):
        prefix = f"{prefix} " if prefix else ""
        raise ValueError(
            f"{prefix}Expected {expected_type} but got {type(obj)} instead"
        )


def load_data(paths: Sequence[str]) -> dict:
    return {file: _load_json(file) for file in paths if file.endswith(".json")}


def load_collection(path: str) -> dict:
    fragments: dict = {}

    if not path.endswith(".json"):
        return fragments

    collection = _load_json(path)

    assert_type(collection, list)

    for index, data in enumerate(collection):
        assert_type(data, dict)
        fragments[f"{path}[{index}]"] = data

    return fragments


def _fragment_schema(
    provenance_service: Optional[ProvenanceService] = None,
) -> FragmentSchema:
    if provenance_service is not None:
        return FragmentSchema(
            unknown="exclude",
            context={"provenance_service": provenance_service},
        )
    return FragmentSchema(unknown="exclude")


def validate(
    data: dict,
    filename: str = "",
    provenance_service: Optional[ProvenanceService] = None,
) -> None:
    if isinstance(data, dict) and "acquisition" in data:
        errors = {
            "acquisition": [
                "Legacy singular field is no longer supported; use 'acquisitions'."
            ]
        }
        raise ValidationError(f"Invalid data in {filename}: {errors}")
    try:
        schema = _fragment_schema(provenance_service)
        validation_errors = schema.validate(data)
    except Exception as error:
        raise ValidationError(f"Invalid data in {filename}: {error}") from error
    if validation_errors:
        raise ValidationError(f"Invalid data in {filename}: {validation_errors}")


def canonicalize(
    data: dict, provenance_service: Optional[ProvenanceService] = None
) -> dict:
    """Round-trip validated data through the schema so the persisted
    document matches what a standard GET would produce (coerced types,
    stripped unknown fields, computed defaults filled in)."""
    schema = _fragment_schema(provenance_service)
    canonical = cast(dict, schema.dump(schema.load(data)))
    canonical["_id"] = data["_id"]
    return canonical


def validate_id(data: dict, filename="") -> None:
    if "_id" not in data:
        raise ValidationError(f"Missing _id in {filename}")

    try:
        MuseumNumber.of(data["_id"])
    except ValueError:
        raise ValidationError(
            f"id {data['_id']!r} of {filename} is not a valid museum number"
        )


def ensure_unique(
    data: dict, fragments_collection: MongoCollection, filename=""
) -> None:
    data_by_id = (
        data["_id"]
        for data in fragments_collection.find_many(
            {"_id": data["_id"]}, projection={"_id": True}
        )
    )
    if existing := next(
        data_by_id,
        False,
    ):
        raise ValidationError(f"ID {existing} of file {filename} already exists")


def update_sort_keys(fragments_collection: MongoCollection) -> None:
    fragments_collection.aggregate(
        [
            {"$project": {"museumNumber": True}},
            *sort_by_museum_number(),
            {
                "$group": {
                    "_id": None,
                    "sorted": {"$push": "$_id"},
                }
            },
            {"$unwind": {"path": "$sorted", "includeArrayIndex": "sortKey"}},
            {"$project": {"_id": "$sorted", "_sortKey": "$sortKey"}},
            {"$merge": "fragments"},
        ],
        allowDiskUse=True,
    )


def create_sort_index(fragments_collection: MongoCollection) -> None:
    fragments_collection.create_index([("_sortKey", pymongo.ASCENDING)])


def set_word_ids(fragment: dict) -> dict:
    lines = deepcopy(fragment).get("text", {}).get("lines", [])

    if not lines:
        return fragment

    word_id = count(1)

    def set_ids(line: dict) -> dict:
        if line["type"] != "TextLine":
            return line

        content = []

        for word in line["content"]:
            if word.get("type") in WORD_TYPES:
                word["id"] = f"Word-{next(word_id)}"
            content.append(word)

        return {**line, "content": content}

    return {
        **fragment,
        "text": {**fragment["text"], "lines": [set_ids(line) for line in lines]},
    }


def write_to_tsv(
    filepath: str,
    data: Sequence[Sequence[str]],
    column_names: Optional[Sequence[str]] = None,
) -> None:
    with open(filepath, "w", newline="") as csvfile:
        writer = csv.writer(csvfile, delimiter="\t")  # pyre-ignore[6]
        if column_names:
            writer.writerow(column_names)
        writer.writerows(data)


if __name__ == "__main__":
    from ebl.io.fragments.importer_cli import main

    main()
