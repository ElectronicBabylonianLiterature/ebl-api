import logging
import os
import multiprocessing
from functools import partial

from pymongo import MongoClient
from ebl.app import create_context
from ebl.context import Context
from ebl.fragmentarium.application.annotations_service import AnnotationsService
from ebl.transliteration.domain.museum_number import MuseumNumber

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

worker_context: Context = None


def get_database():
    client = MongoClient(os.environ["MONGODB_URI"])
    return client.get_database(os.environ.get("MONGODB_DB"))


def create_annotations_service(context: Context) -> AnnotationsService:
    return AnnotationsService(
        context.ebl_ai_client,
        context.annotations_repository,
        context.photo_repository,
        context.changelog,
        context.fragment_repository,
        context.photo_repository,
        context.cropped_sign_images_repository,
    )


def init_worker():
    global worker_context
    worker_context = create_context()


def process_single_fragment(fragment_number_str: str):
    try:
        global worker_context
        if worker_context is None:
            worker_context = create_context()

        repo = worker_context.annotations_repository
        images_repo = worker_context.cropped_sign_images_repository
        service = create_annotations_service(worker_context)

        fragment_number = MuseumNumber.of(fragment_number_str)
        annotations = repo.query_by_museum_number(fragment_number)

        if not annotations.annotations:
            return 0
        annotations_with_ids, cropped_images = service._cropped_image_from_annotations(
            annotations)

        if cropped_images:
            images_repo.create_many(cropped_images)

        repo.create_or_update(annotations_with_ids)

        return 1

    except Exception as e:
        logger.error(f"Error processing {fragment_number_str}: {e}")
        return 0


def show_statistics(context: Context) -> tuple:
    database = get_database()
    annotations_collection = database["annotations"]
    cropped_images_collection = database["cropped_sign_images"]

    logger.info("Counting annotations and cropped images...")

    pipeline = [
        {"$project": {"annotation_count": {"$size": "$annotations"}}},
        {"$group": {"_id": None, "total_annotations": {"$sum": "$annotation_count"}}},
    ]
    result = list(annotations_collection.aggregate(pipeline))
    individual_annotations_count = result[0]["total_annotations"] if result else 0

    try:
        cropped_images_count = cropped_images_collection.estimated_document_count()
    except Exception:
        cropped_images_count = cropped_images_collection.count_documents({})

    ratio = (
        cropped_images_count / individual_annotations_count
        if individual_annotations_count > 0
        else 0
    )

    logger.info(f"Individual annotations: {individual_annotations_count:,}")
    logger.info(f"Cropped images: {cropped_images_count:,}")
    logger.info(f"Ratio (images:annotations): {ratio:.1f}:1")

    return individual_annotations_count, cropped_images_count


def cleanup_existing_images(context: Context):
    logger.info("Removing all existing cropped sign images...")
    database = get_database()
    database.drop_collection("cropped_sign_images")
    logger.info("All cropped sign images removed.")


def regenerate_images(context: Context):
    database = get_database()
    annotations_collection = database["annotations"]

    logger.info("Fetching list of fragments to process...")
    cursor = annotations_collection.find({}, {"fragmentNumber": 1})

    fragment_numbers = [
        doc["fragmentNumber"]
        for doc in cursor
        if "fragmentNumber" in doc
    ]

    total_fragments = len(fragment_numbers)
    logger.info(
        f"Found {total_fragments} fragments. Starting parallel processing...")

    cpu_count = os.cpu_count() or 4
    logger.info(f"Using {cpu_count} worker processes.")

    processed_count = 0

    with multiprocessing.Pool(processes=cpu_count, initializer=init_worker) as pool:
        for result in pool.imap_unordered(process_single_fragment, fragment_numbers, chunksize=10):
            processed_count += result
            if processed_count % 100 == 0:
                logger.info(
                    f"Progress: {processed_count} fragments processed successfully...")

    logger.info(f"Regeneration completed.")


def migrate_cropped_images():
    context = create_context()

    logger.info("eBL Cropped Sign Images Migration")
    logger.info("=" * 40)

    logger.info("BEFORE migration:")
    individual_annotations_count, cropped_images_count = show_statistics(
        context)

    if cropped_images_count > 0:
        cleanup_existing_images(context)
    else:
        logger.info("No existing images found, skipping cleanup.")

    logger.info("Starting regeneration...")
    regenerate_images(context)

    logger.info("\nAFTER migration:")
    show_statistics(context)

    logger.info("Migration completed successfully!")


def main():
    try:
        migrate_cropped_images()
    except KeyboardInterrupt:
        logger.info("\nMigration cancelled by user.")
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")


if __name__ == "__main__":
    main()
