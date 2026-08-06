import argparse
import json
import os
from datetime import date
from pathlib import Path


from ebl.app import create_context
from ebl.fragmentarium.domain.annotation import (
    AnnotationValueType,
)
from ebl.fragmentarium.retrieve_annotations_helpers import (
    create_annotations,
    create_directory,
    write_fragment_numbers,
)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-oa",
        "--output_annotations",
        type=str,
        default=None,
        help="Output Annotations Directory",
    )
    parser.add_argument(
        "-oi", "--output_imgs", type=str, default=None, help="Output Images Directory"
    )
    parser.add_argument(
        "-f",
        "--filter",
        type=str,
        help="filter from ./annotations.json has to 'finished', 'unfinished' or 'selected'",
    )
    parser.add_argument(
        "-c",
        "--classification",
        action="store_true",
        help="Get Signs for detection or classification",
    )
    args = parser.parse_args(argv)
    print("args:", args, "argv:", argv)

    if bool(args.output_annotations) ^ bool(args.output_imgs):
        raise argparse.ArgumentError(
            None, message="Either specify both argument options or none at all"
        )

    if args.output_annotations is None and args.output_imgs is None:
        create_directory("annotations")
        create_directory("annotations/annotations")
        create_directory("annotations/imgs")
        args.output_annotations = "./annotations/annotations"
        args.output_imgs = "./annotations/imgs"

    try:
        context = create_context()
        annotation_collection = context.annotations_repository.retrieve_all_non_empty()
        photo_repository = context.photo_repository
    except KeyError as e:
        print(
            f"Failed to create full context due to {type(e).__name__}: {e}. Using Mongo environment only."
        )
        from pymongo import MongoClient
        from ebl.fragmentarium.infrastructure.mongo_annotations_repository import (
            MongoAnnotationsRepository,
        )
        from ebl.files.infrastructure.grid_fs_file_repository import (
            GridFsFileRepository,
        )

        mongodb_uri = os.environ.get("MONGODB_URI")
        if not mongodb_uri:
            raise RuntimeError("Missing required environment variable: MONGODB_URI")
        mongodb_db = os.environ.get("MONGODB_DB", "ebl")
        client = MongoClient(mongodb_uri)
        database = client.get_database(mongodb_db)
        annotations_repository = MongoAnnotationsRepository(database)
        photo_repository = GridFsFileRepository(database, "photos")
        annotation_collection = annotations_repository.retrieve_all_non_empty()

    if args.filter:
        if args.filter not in ["finished", "unfinished", "selected"]:
            raise argparse.ArgumentError(
                None,
                message="Filter has to be either 'finished', 'unfinished' or 'selected'",
            )
        print(f"'{args.filter}' Fragments are filtered.")
        if args.filter == "selected" or args.filter == "finished":
            with open("ebl/fragmentarium/annotations.json") as f:
                filter_fragments = json.load(f)[args.filter]
            annotation_collection = list(
                filter(
                    lambda elem: str(elem.fragment_number) in filter_fragments,
                    annotation_collection,
                )
            )
        else:
            with open("ebl/fragmentarium/annotations.json") as f:
                filter_fragments = json.load(f)["finished"]
            annotation_collection = list(
                filter(
                    lambda elem: str(elem.fragment_number) not in filter_fragments,
                    annotation_collection,
                )
            )

    if args.classification:
        TO_FILTER = [
            AnnotationValueType.RULING_DOLLAR_LINE,
            AnnotationValueType.SURFACE_AT_LINE,
            AnnotationValueType.BLANK,
            AnnotationValueType.ColumnAtLine,
            AnnotationValueType.STRUCT,
        ]
    else:
        TO_FILTER = [
            AnnotationValueType.RULING_DOLLAR_LINE,
            AnnotationValueType.ColumnAtLine,
        ]
    print(f"Following Annotation Types are filtered: {TO_FILTER}")

    create_annotations(
        annotation_collection,
        args.output_annotations,
        args.output_imgs,
        photo_repository,
        to_filter=TO_FILTER,
    )
    annotations_parent = Path(args.output_annotations).parent
    annotations_file = annotations_parent / f"Annotations_{date.today()}.txt"
    write_fragment_numbers(
        annotation_collection,
        str(annotations_file),
    )
    print("Done")


if __name__ == "__main__":
    """
    # for detection finished fragments are filtered
    poetry run python -m ebl.fragmentarium.retrieve_annotations -f
    # for classification
    poetry run python -m ebl.fragmentarium.retrieve_annotations -c
    """
    main()
