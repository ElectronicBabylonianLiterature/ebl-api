import argparse
from pymongo import MongoClient
from gridfs import GridFS
import os
from PIL import Image, ImageFile
import io
from tqdm import tqdm
from ebl.fragmentarium.application.fragment_finder import ThumbnailSize
from itertools import islice
from concurrent.futures import ThreadPoolExecutor
from functools import partial

Image.MAX_IMAGE_PIXELS = None  # pyre-ignore[9]
ImageFile.LOAD_TRUNCATED_IMAGES = True


def resize(original: Image.Image, size: ThumbnailSize):
    width = size.value
    resolution = (width, original.size[1])
    resized = original.copy()
    resized.thumbnail(resolution)

    return resized


def clear_thumbnails(collection) -> None:
    all_thumbnails = list(collection.find())
    for old_thumbnail in tqdm(
        all_thumbnails, desc="Clearing thumbnails", total=len(all_thumbnails)
    ):
        collection.delete(old_thumbnail._id)


def add_infix(filename, size: ThumbnailSize):
    name, extension = os.path.splitext(filename)
    return f"{name}_{size.value}{extension}"


def load_batch(collection, batch):
    return collection.find({"filename": {"$in": batch}})


def create_thumbnail(item, size: ThumbnailSize):
    original = Image.open(item)
    filename = add_infix(item.filename, size)

    return filename, resize(original, size)


def save_thumbnails(collection, thumbnails):
    for filename, thumbnail in thumbnails:
        with io.BytesIO() as stream:
            thumbnail.save(stream, format="jpeg")
            stream.seek(0)
            collection.put(
                stream,
                content_type="image/jpeg",
                filename=filename,
            )


def batched(iterable, n):
    it = iter(iterable)
    while True:
        batch = tuple(islice(it, n))
        if not batch:
            return
        yield batch


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Create thumbnails for the fragment photos. "
            "MONGODB_URI environment variable must be set."
        )
    )
    parser.add_argument(
        "command", default="update", nargs="?", choices=["update", "clear"]
    )
    parser.add_argument(
        "-s",
        "--sizes",
        nargs="+",
        choices=[size.name.lower() for size in ThumbnailSize],
        default=["small"],
    )
    parser.add_argument(
        "-db",
        "--db",
        "--database",
        choices=["ebl", "ebldev"],
        default="ebldev",
        dest="database",
    )
    parser.add_argument("-bs", "--batch-size", default=500, dest="batchsize", type=int)
    args = parser.parse_args()

    print(f"Processing db {args.database!r}...")

    client = MongoClient(os.environ["MONGODB_URI"])
    database = client.get_database(args.database)

    original_photos_collection = GridFS(database, "photos")
    thumbnail_collection = GridFS(database, "thumbnails")

    all_photos = set(original_photos_collection.list())
    all_thumbnails = set(thumbnail_collection.list())

    if args.command == "update":
        for size in args.sizes:
            thumbnail_size = ThumbnailSize.from_string(size)
            width = thumbnail_size.value
            needs_thumbnail = [
                file
                for file in all_photos
                if add_infix(file, thumbnail_size) not in all_thumbnails
            ]
            total = len(needs_thumbnail)

            if total:
                print(f"Found {total:,} photos without a {size} thumbnail.")
                batches = batched(needs_thumbnail, args.batchsize)
                batchcount = total // args.batchsize

                for i, batch in enumerate(batches, start=1):
                    print(f"Creating thumbnails (batch {i} of {batchcount})...")
                    originals = load_batch(original_photos_collection, batch)

                    if batchcount > 1:
                        with ThreadPoolExecutor() as executor:
                            thumbnails = list(
                                tqdm(
                                    executor.map(
                                        partial(create_thumbnail, size=thumbnail_size),
                                        originals,
                                    ),
                                    total=len(batch),
                                )
                            )
                    else:
                        thumbnails = [
                            create_thumbnail(item, thumbnail_size)
                            for item in tqdm(originals, total=len(needs_thumbnail))
                        ]
                    print("Saving thumbnails...")
                    save_thumbnails(thumbnail_collection, thumbnails)
            else:
                print("All thumbnails up to date.")
        print("Done.")

    elif args.command == "clear":
        clear_thumbnails(thumbnail_collection)
        print("Done.")
