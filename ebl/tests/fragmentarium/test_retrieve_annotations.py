from PIL import Image
from mockito import mock, verify, when

from ebl.fragmentarium import retrieve_annotations
from ebl.fragmentarium.retrieve_annotations import create_annotations, BoundingBox
from ebl.tests.factories.annotation import (
    AnnotationsFactory,
    GeometryFactory,
)


def test_create_annotations(photo_repository, when, photo):
    annotation = AnnotationsFactory.build()

    image = mock({"save": lambda _: None, "size": (640, 480, 3)})
    when(photo_repository).query_by_file_name(
        f"{annotation.fragment_number}.jpg"
    ).thenReturn(photo)
    when(Image).open(...).thenReturn(image)
    when(retrieve_annotations).write_annotations(...).thenReturn(None)

    create_annotations([annotation], "", "", photo_repository)
    verify(image).save(f"{annotation.fragment_number}.jpg")


def test_from_relative_to_absolute_coordinates():
    geometry = GeometryFactory.build(x=0, y=0, width=100, height=100)
    shape = (640, 480)
    assert BoundingBox.from_relative_coordinates(
        geometry.x,
        geometry.y,
        geometry.width,
        geometry.height,
        image_width=shape[0],
        image_height=shape[1],
    ) == (BoundingBox(0, 0, 640, 480))


def test_write_annotations(tmp_path):
    dir = tmp_path / "annotations"
    dir.mkdir()
    file_name = dir / "annotation_1.txt"
    bounding_boxes = [BoundingBox(0.1, 1, 2, 100.543), BoundingBox(10, 11, 12, 13)]
    retrieve_annotations.write_annotations(
        file_name, bounding_boxes, ["KUR", "A.GUD×KUR"]
    )
    assert file_name.read_text() == "0,1,2,100,KUR\n10,11,12,13,A.GUD×KUR\n"


def test_write_fragment_numbers(tmp_path):
    annotations = AnnotationsFactory.build_batch(5)
    dir = tmp_path / "annotations"
    dir.mkdir()
    file_name = dir / "Annotation_numbers.txt"
    retrieve_annotations.write_fragment_numbers(annotations, file_name)
    result = "\n".join([str(annotation.fragment_number) for annotation in annotations])
    assert file_name.read_text() == f"Total of 5 Annotations\n{result}\n"


def test_argument_parsing_only_one_argument():
    import argparse

    try:
        retrieve_annotations.main(["--output_annotations", "/some/path"])
        raise AssertionError("Should have raised ArgumentError")
    except argparse.ArgumentError as e:
        assert "Either specify both argument options or none at all" in str(e)


def test_argument_parsing_defaults():
    mock_context = mock()
    mock_context.annotations_repository = mock()
    mock_context.photo_repository = mock()
    when(mock_context.annotations_repository).retrieve_all_non_empty().thenReturn([])
    when(retrieve_annotations).create_context().thenReturn(mock_context)

    created_dirs = []

    def track_create_directory(path):
        created_dirs.append(path)

    when(retrieve_annotations).create_directory(...).thenAnswer(
        lambda path: track_create_directory(path)
    )
    when(retrieve_annotations).create_annotations(...).thenReturn(None)
    when(retrieve_annotations).write_fragment_numbers(...).thenReturn(None)

    retrieve_annotations.main([])

    assert "annotations" in created_dirs
    assert "annotations/annotations" in created_dirs
    assert "annotations/imgs" in created_dirs
    verify(retrieve_annotations, times=3).create_directory(...)


def test_context_fallback_to_mongo(monkeypatch):
    import pymongo
    import ebl.fragmentarium.infrastructure.mongo_annotations_repository as mongo_anno_module
    import ebl.files.infrastructure.grid_fs_file_repository as gridfs_module

    monkeypatch.setenv("MONGODB_URI", "mongodb://test:27017")
    monkeypatch.setenv("MONGODB_DB", "test_db")

    when(retrieve_annotations).create_context().thenRaise(KeyError("DB failed"))

    # Mock MongoDB components
    mock_client = mock()
    mock_db = mock()
    mock_annotations_repo = mock()
    mock_photo_repo = mock()

    when(mock_client).get_database("test_db").thenReturn(mock_db)
    when(mock_annotations_repo).retrieve_all_non_empty().thenReturn([])

    # Mock the class constructors at module level
    when(pymongo).MongoClient("mongodb://test:27017").thenReturn(mock_client)
    when(mongo_anno_module).MongoAnnotationsRepository(mock_db).thenReturn(
        mock_annotations_repo
    )
    when(gridfs_module).GridFsFileRepository(mock_db, "photos").thenReturn(
        mock_photo_repo
    )
    when(retrieve_annotations).create_directory(...).thenReturn(None)
    when(retrieve_annotations).create_annotations(...).thenReturn(None)
    when(retrieve_annotations).write_fragment_numbers(...).thenReturn(None)

    # Should not raise, should use fallback
    retrieve_annotations.main([])
    # verify
    verify(pymongo).MongoClient("mongodb://test:27017")
    verify(mongo_anno_module).MongoAnnotationsRepository(mock_db)
    verify(gridfs_module).GridFsFileRepository(mock_db, "photos")
