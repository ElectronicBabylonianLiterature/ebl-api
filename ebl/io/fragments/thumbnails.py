import argparse
from pymongo import MongoClient
from gridfs import GridFS
import os
from PIL import Image
import io

from tqdm import tqdm

from ebl.fragmentarium.application.fragment_finder import ThumbnailSize


def resize(original: Image, size: ThumbnailSize):
    width = size.value
    resolution = (width, original.size[1])
    resized = original.copy()
    resized.thumbnail(resolution)

    return resized


def clear_thumbnails(collection: GridFS) -> None:
    all_thumbnails = list(collection.find())
    for old_thumbnail in tqdm(
        all_thumbnails, desc="Clearing thumbnails", total=len(all_thumbnails)
    ):
        collection.delete(old_thumbnail._id)


def create_thumbnails(originals: list, total: int, size: ThumbnailSize):
    for item in tqdm(
        originals,
        desc=f"Creating {size.name.lower()} thumbnails",
        total=total,
    ):
        filename, extension = os.path.splitext(item.filename)
        original = Image.open(item)
        thumbnail = resize(original, size)

        with io.BytesIO() as stream:
            thumbnail.save(stream, format="jpeg")
            stream.seek(0)
            thumbnail_collection.put(
                stream,
                content_type="image/jpeg",
                filename=f"{filename}_{size.value}{extension}",
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Create thumbnails for the fragment photos."
            "MONGODB_URI environment variable must be set."
        )
    )
    args = parser.parse_args()

    client = MongoClient(os.environ["MONGODB_URI"])
    database = client.get_database(os.environ["MONGODB_DB"])

    original_photos_collection = GridFS(database, "photos")
    original_photos = list(original_photos_collection.find())
    total = len(original_photos)

    thumbnail_collection = GridFS(database, "thumbnails")

    clear_thumbnails(thumbnail_collection)

    for size in ThumbnailSize:
        create_thumbnails(original_photos, total, size)
