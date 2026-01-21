import multiprocessing
from mockito import mock, when, verify, any_
import pytest

import ebl.fragmentarium.migrate_cropped_images as module
from ebl.fragmentarium.application.cropped_sign_image import CroppedSignImage, Base64
from ebl.transliteration.domain.museum_number import MuseumNumber


def test_create_annotations_service():
    context = mock()
    service = module.create_annotations_service(context)
    assert service.__class__.__name__ == "AnnotationsService"


def test_process_single_fragment_success():
    worker_context = mock()
    module.worker_context = worker_context

    annotations_repository = mock()
    images_repository = mock()
    worker_context.annotations_repository = annotations_repository
    worker_context.cropped_sign_images_repository = images_repository

    fragment_number_str = "K.123"
    fragment_number = MuseumNumber.of(fragment_number_str)
    annotations_data = mock()
    annotations_data.annotations = ["annotation"]

    service = mock()
    when(module).create_annotations_service(worker_context).thenReturn(service)
    when(annotations_repository).query_by_museum_number(
        fragment_number).thenReturn(annotations_data)

    cropped_images = [mock()]
    annotations_with_ids = mock()
    when(service)._cropped_image_from_annotations(
        annotations_data).thenReturn((annotations_with_ids, cropped_images))

    result = module.process_single_fragment(fragment_number_str)

    verify(images_repository).create_many(cropped_images)
    verify(annotations_repository).create_or_update(annotations_with_ids)
    assert result == 1


def test_process_single_fragment_no_annotations():
    worker_context = mock()
    module.worker_context = worker_context

    annotations_repository = mock()
    worker_context.annotations_repository = annotations_repository

    fragment_number_str = "K.123"
    fragment_number = MuseumNumber.of(fragment_number_str)
    annotations_data = mock()
    annotations_data.annotations = []

    when(annotations_repository).query_by_museum_number(
        fragment_number).thenReturn(annotations_data)

    result = module.process_single_fragment(fragment_number_str)

    assert result == 0


def test_process_single_fragment_error():
    worker_context = mock()
    module.worker_context = worker_context

    when(module).create_annotations_service(
        worker_context).thenRaise(Exception("Database Error"))

    result = module.process_single_fragment("K.123")

    assert result == 0


def test_show_statistics():
    context = mock()
    database = mock()
    annotations_collection = mock()
    cropped_images_collection = mock()

    when(module).get_database().thenReturn(database)
    when(database).__getitem__("annotations").thenReturn(annotations_collection)
    when(database).__getitem__("cropped_sign_images").thenReturn(
        cropped_images_collection)

    when(annotations_collection).aggregate(
        any_).thenReturn([{"total_annotations": 100}])
    when(cropped_images_collection).estimated_document_count().thenReturn(50)

    individual_count, cropped_count = module.show_statistics(context)

    assert individual_count == 100
    assert cropped_count == 50


def test_cleanup_existing_images():
    context = mock()
    database = mock()

    when(module).get_database().thenReturn(database)

    module.cleanup_existing_images(context)

    verify(database).drop_collection("cropped_sign_images")


def test_regenerate_images():
    context = mock()
    database = mock()
    annotations_collection = mock()
    pool_mock = mock()

    when(module).get_database().thenReturn(database)
    when(database).__getitem__("annotations").thenReturn(annotations_collection)

    cursor_data = [{"fragmentNumber": "K.1"}, {"fragmentNumber": "K.2"}]
    when(annotations_collection).find(any_, any_).thenReturn(cursor_data)

    when(multiprocessing).Pool(processes=any_,
                               initializer=any_).thenReturn(pool_mock)
    when(pool_mock).__enter__().thenReturn(pool_mock)
    when(pool_mock).__exit__(any_, any_, any_).thenReturn(None)
    when(pool_mock).imap_unordered(any_, any_,
                                   chunksize=any_).thenReturn(iter([1, 1]))

    module.regenerate_images(context)

    verify(multiprocessing).Pool(processes=any_, initializer=any_)
    verify(pool_mock).imap_unordered(
        module.process_single_fragment, ["K.1", "K.2"], chunksize=10)


def test_migrate_cropped_images_with_cleanup():
    context = mock()
    when(module).create_context().thenReturn(context)
    when(module).show_statistics(context).thenReturn((100, 50))
    when(module).cleanup_existing_images(context).thenReturn(None)
    when(module).regenerate_images(context).thenReturn(None)

    module.migrate_cropped_images()

    verify(module).cleanup_existing_images(context)
    verify(module).regenerate_images(context)


def test_migrate_cropped_images_skip_cleanup():
    context = mock()
    when(module).create_context().thenReturn(context)
    when(module).show_statistics(context).thenReturn((100, 0))
    when(module).regenerate_images(context).thenReturn(None)

    module.migrate_cropped_images()

    verify(module, times=0).cleanup_existing_images(context)
    verify(module).regenerate_images(context)


def test_main_success():
    when(module).migrate_cropped_images().thenReturn(None)
    module.main()
    verify(module).migrate_cropped_images()


def test_main_keyboard_interrupt():
    when(module).migrate_cropped_images().thenRaise(KeyboardInterrupt)
    module.main()


def test_main_general_exception():
    when(module).migrate_cropped_images().thenRaise(
        Exception("Critical Failure"))
    module.main()


def test_cropped_sign_image_model():
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
        CroppedSignImage.create(Base64("data1"), fragment_number_1),
        CroppedSignImage.create(Base64("data2"), fragment_number_1),
        CroppedSignImage.create(Base64("data3"), fragment_number_2),
    ]

    cropped_sign_images_repository.create_many(images)

    collection = database["cropped_sign_images"]
    assert collection.count_documents({}) == 3

    cropped_sign_images_repository.delete_by_fragment_number(fragment_number_1)

    assert collection.count_documents({}) == 1
    assert collection.count_documents(
        {"fragmentNumber": str(fragment_number_2)}) == 1
