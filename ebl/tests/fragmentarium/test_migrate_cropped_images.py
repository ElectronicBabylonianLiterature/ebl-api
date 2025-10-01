from mockito import mock

from ebl.fragmentarium.application.cropped_sign_image import CroppedSignImage, Base64
from ebl.fragmentarium.migrate_cropped_images import create_annotations_service
from ebl.transliteration.domain.museum_number import MuseumNumber


def test_create_annotations_service():
    context = mock()

    result = create_annotations_service(context)

    assert result.__class__.__name__ == "AnnotationsService"


def test_cleanup_existing_images(database):
    from ebl.fragmentarium.migrate_cropped_images import cleanup_existing_images
    from unittest.mock import patch

    context = mock()

    with patch(
        "ebl.fragmentarium.migrate_cropped_images.get_database", return_value=database
    ):
        cleanup_existing_images(context)


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
