import logging
import os

from pymongo import MongoClient
from ebl.app import create_context
from ebl.context import Context
from ebl.fragmentarium.application.annotations_service import AnnotationsService
from ebl.transliteration.domain.museum_number import MuseumNumber

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
    annotations_repository = context.annotations_repository
    cropped_sign_images_repository = context.cropped_sign_images_repository
    annotations_service = create_annotations_service(context)
    database = get_database()

    logger.info("Fetching all annotations...")
    annotations_collection = database["annotations"]
    annotations_cursor = annotations_collection.find({})

    processed_count = 0
    error_count = 0

    for annotation_doc in annotations_cursor:
        try:
            fragment_number = MuseumNumber.of(annotation_doc["fragmentNumber"])
            annotations = annotations_repository.query_by_museum_number(fragment_number)

            if annotations.annotations:
                logger.info(
                    f"Processing fragment {fragment_number} with {len(annotations.annotations)} annotations"
                )

                (
                    annotations_with_image_ids,
                    cropped_sign_images,
                ) = annotations_service._cropped_image_from_annotations(annotations)

                if cropped_sign_images:
                    cropped_sign_images_repository.create_many(cropped_sign_images)
                    logger.info(
                        f"Created {len(cropped_sign_images)} cropped images for fragment {fragment_number}"
                    )

                annotations_repository.create_or_update(annotations_with_image_ids)
                processed_count += 1

                if processed_count % 100 == 0:
                    logger.info(f"Processed {processed_count} fragments so far...")

        except Exception as e:
            error_count += 1
            logger.error(
                f"Error processing fragment {annotation_doc.get('fragmentNumber', 'unknown')}: {str(e)}"
            )
            continue

    logger.info(
        f"Regeneration completed. Processed {processed_count} fragments, {error_count} errors."
    )


def migrate_cropped_images():
    context = create_context()

    logger.info("eBL Cropped Sign Images Migration")
    logger.info("=" * 40)

    logger.info("BEFORE migration:")
    individual_annotations_count, cropped_images_count = show_statistics(context)

    if cropped_images_count == 0:
        logger.info("No cropped images found. Nothing to clean up.")
        logger.info("Proceeding with regeneration...")
    else:
        cleanup_existing_images(context)

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
