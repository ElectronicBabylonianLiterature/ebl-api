from mockito import mock, when
import ebl.fragmentarium.migrate_cropped_images as module

from ebl.fragmentarium.application.cropped_sign_image import CroppedSignImage, Base64
from ebl.fragmentarium.migrate_cropped_images import (
    create_annotations_service,
    show_statistics,
    regenerate_images,
    migrate_cropped_images,
    main,
)
from ebl.transliteration.domain.museum_number import MuseumNumber


def test_create_annotations_service():
    context = mock()

    result = create_annotations_service(context)

    assert result.__class__.__name__ == "AnnotationsService"


def test_cleanup_existing_images(database):
    from ebl.fragmentarium.migrate_cropped_images import cleanup_existing_images

    context = mock()

    when(module).get_database().thenReturn(database)

    cleanup_existing_images(context)


def test_show_statistics():
    context = mock()
    database = mock()
    annotations_collection = mock()
    cropped_images_collection = mock()

    when(database).__getitem__("annotations").thenReturn(annotations_collection)
    when(database).__getitem__("cropped_sign_images").thenReturn(
        cropped_images_collection
    )
    when(annotations_collection).aggregate(...).thenReturn([{"total_annotations": 100}])
    when(cropped_images_collection).estimated_document_count().thenReturn(50)
    when(module).get_database().thenReturn(database)

    individual_count, cropped_count = show_statistics(context)

    assert individual_count == 100
    assert cropped_count == 50


def test_regenerate_images():
    context = mock()
    database = mock()
    annotations_collection = mock()
    annotation_doc = {"fragmentNumber": "K.123"}
    annotations_result = mock()
    annotations_repository = mock()

    when(database).__getitem__("annotations").thenReturn(annotations_collection)
    when(annotations_collection).find({}).thenReturn([annotation_doc])
    annotations_result.annotations = []
    when(annotations_repository).query_by_museum_number(
        MuseumNumber.of("K.123")
    ).thenReturn(annotations_result)
    context.annotations_repository = annotations_repository

    annotations_service = mock()
    when(module).get_database().thenReturn(database)
    when(module).create_annotations_service(context).thenReturn(annotations_service)

    regenerate_images(context)


def test_migrate_cropped_images():
    context = mock()

    when(module).create_context().thenReturn(context)
    when(module).show_statistics(context).thenReturn((0, 0))
    when(module).regenerate_images(context).thenReturn(None)
    when(module).cleanup_existing_images(context).thenReturn(None)

    migrate_cropped_images()


def test_main():
    when(module).migrate_cropped_images().thenReturn(None)

    main()


def test_main_keyboard_interrupt():
    when(module).migrate_cropped_images().thenRaise(KeyboardInterrupt)

    main()


def test_main_exception():
    when(module).migrate_cropped_images().thenRaise(Exception("test error"))

    main()


def test_cropped_sign_image_creation():
    fragment_number = MuseumNumber("K", "123")
    image_data = Base64("test_image_data")

    cropped_image = CroppedSignImage.create(image_data, fragment_number)

    assert cropped_image.image == image_data
    assert cropped_image.fragment_number == fragment_number
    assert cropped_image.image_id is not None


def test_cropped_sign_images_repository_delete_by_fragment_number(
    cropped_sign_images_repository, database
):
    fragment_number_1 = MuseumNumber("K", "1")
    fragment_number_2 = MuseumNumber("K", "2")

    images = [
        CroppedSignImage("image1", Base64("data1"), fragment_number_1),
        CroppedSignImage("image2", Base64("data2"), fragment_number_1),
        CroppedSignImage("image3", Base64("data3"), fragment_number_2),
    ]

    cropped_sign_images_repository.create_many(images)

    collection = database["cropped_sign_images"]
    assert collection.count_documents({}) == 3

    cropped_sign_images_repository.delete_by_fragment_number(fragment_number_1)

    assert collection.count_documents({}) == 1
    assert collection.count_documents({"fragment_number": str(fragment_number_2)}) == 1
