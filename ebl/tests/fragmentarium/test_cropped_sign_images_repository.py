from ebl.fragmentarium.application.cropped_sign_image import (
    CroppedSignImage,
    Base64,
    CroppedSignImageSchema,
)
from ebl.fragmentarium.infrastructure.cropped_sign_images_repository import (
    MongoCroppedSignImagesRepository,
)
from ebl.transliteration.domain.museum_number import MuseumNumber


def test_delete_by_fragment_number(database):
    repository = MongoCroppedSignImagesRepository(database)
    fragment_number_1 = MuseumNumber("K", "1")
    fragment_number_2 = MuseumNumber("K", "2")

    images = [
        CroppedSignImage("image1", Base64("data1"), fragment_number_1),
        CroppedSignImage("image2", Base64("data2"), fragment_number_1),
        CroppedSignImage("image3", Base64("data3"), fragment_number_2),
    ]

    repository.create_many(images)

    collection = database["cropped_sign_images"]
    assert collection.count_documents({}) == 3
    assert collection.count_documents({"fragment_number": str(fragment_number_1)}) == 2
    assert collection.count_documents({"fragment_number": str(fragment_number_2)}) == 1

    repository.delete_by_fragment_number(fragment_number_1)

    assert collection.count_documents({}) == 1
    assert collection.count_documents({"fragment_number": str(fragment_number_1)}) == 0
    assert collection.count_documents({"fragment_number": str(fragment_number_2)}) == 1

    remaining_doc = collection.find_one({"fragment_number": str(fragment_number_2)})
    assert remaining_doc["_id"] == "image3"


def test_cropped_sign_image_schema_with_fragment_number():
    fragment_number = MuseumNumber("BM", "12345")
    image = CroppedSignImage("test-id", Base64("test-data"), fragment_number)
    schema = CroppedSignImageSchema()

    dumped = schema.dump(image)
    expected = {
        "_id": "test-id",
        "image": "test-data",
        "fragment_number": "BM.12345"
    }
    assert dumped == expected

    loaded = schema.load(expected)
    assert loaded.image_id == "test-id"
    assert loaded.image == "test-data"
    assert loaded.fragment_number == fragment_number
