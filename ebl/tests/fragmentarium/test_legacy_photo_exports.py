"""Offline tooling must not export or re-crop removed legacy originals."""

from typing import cast

from mockito import mock, verify
from PIL import Image

import ebl.fragmentarium.migrate_cropped_images as migrate
from ebl.context import Context
from ebl.fragmentarium import retrieve_annotations, retrieve_annotations_helpers
from ebl.fragmentarium.retrieve_annotations_helpers import (
    create_annotations,
    without_removed_legacy_photos,
)
from ebl.media.application.media_runtime import MediaRuntime
from ebl.media.infrastructure.mongo_media_reader import MongoMediaReader
from ebl.tests.factories.annotation import AnnotationsFactory
from ebl.transliteration.domain.museum_number import MuseumNumber

REMOVED = MuseumNumber.of("K.1")
KEPT = MuseumNumber.of("K.2")


def _suppress(database, number: MuseumNumber) -> None:
    database["mediaLegacyVisibility"].insert_one(
        {"_id": str(number), "suppressed": True}
    )


def test_removed_legacy_photos_are_dropped_from_exports(database):
    _suppress(database, REMOVED)
    database["mediaLegacyVisibility"].insert_one({"_id": "K.3", "suppressed": False})
    collection = [
        AnnotationsFactory.build(fragment_number=number)
        for number in (REMOVED, KEPT, MuseumNumber.of("K.3"))
    ]

    kept = without_removed_legacy_photos(collection, MongoMediaReader(database))

    assert [item.fragment_number for item in kept] == [
        KEPT,
        MuseumNumber.of("K.3"),
    ]


def test_exports_are_unchanged_without_visibility_records(database):
    collection = AnnotationsFactory.build_batch(3)

    assert (
        without_removed_legacy_photos(collection, MongoMediaReader(database))
        == collection
    )


def test_create_annotations_never_reads_a_removed_original(
    database, photo_repository, when, photo
):
    _suppress(database, REMOVED)
    removed = AnnotationsFactory.build(fragment_number=REMOVED)
    kept = AnnotationsFactory.build(fragment_number=KEPT)
    image = mock({"save": lambda _: None, "size": (640, 480, 3)})
    when(photo_repository).query_by_file_name("K.2.jpg").thenReturn(photo)
    when(Image).open(...).thenReturn(image)
    when(retrieve_annotations_helpers).write_annotations(...).thenReturn(None)

    create_annotations(
        [removed, kept],
        "",
        "",
        photo_repository,
        legacy_visibility=MongoMediaReader(database),
    )

    verify(photo_repository, times=0).query_by_file_name("K.1.jpg")
    verify(image).save("K.2.jpg")
    verify(image, times=0).save("K.1.jpg")


def test_retrieve_annotations_cli_skips_removed_legacy_photos(database, monkeypatch):
    _suppress(database, REMOVED)
    removed = AnnotationsFactory.build(fragment_number=REMOVED)
    kept = AnnotationsFactory.build(fragment_number=KEPT)
    exported = []
    listed = []

    class _Context:
        annotations_repository = type(
            "Repo",
            (),
            {"retrieve_all_non_empty": staticmethod(lambda: [removed, kept])},
        )()
        photo_repository = object()

    monkeypatch.setattr(retrieve_annotations, "create_context", lambda: _Context())
    monkeypatch.setattr(
        retrieve_annotations,
        "legacy_photo_visibility",
        lambda _database=None: MongoMediaReader(database),
    )
    monkeypatch.setattr(
        retrieve_annotations,
        "create_annotations",
        lambda collection, *_args, **_kwargs: exported.append(list(collection)),
    )
    monkeypatch.setattr(
        retrieve_annotations,
        "write_fragment_numbers",
        lambda collection, _path: listed.append(list(collection)),
    )
    monkeypatch.setattr(retrieve_annotations, "create_directory", lambda _path: None)

    retrieve_annotations.main(["-oa", "/out/a", "-oi", "/out/i"])

    assert exported == [[kept]]
    assert listed == [[kept]]


def _regenerate(when, database, fragment_numbers):
    annotations_collection = mock()
    when(annotations_collection).find({}).thenReturn(
        [{"fragmentNumber": str(number)} for number in fragment_numbers]
    )
    annotations_database = mock()
    when(annotations_database).__getitem__("annotations").thenReturn(
        annotations_collection
    )
    annotations_repository = mock()
    cropped_repository = mock()
    service = mock()
    for number in fragment_numbers:
        annotations = AnnotationsFactory.build(fragment_number=number)
        when(annotations_repository).query_by_museum_number(number).thenReturn(
            annotations
        )
        when(service)._cropped_image_from_annotations(annotations).thenReturn(
            (annotations, [mock()])
        )
    context = cast(
        Context,
        mock(
            {
                "annotations_repository": annotations_repository,
                "cropped_sign_images_repository": cropped_repository,
            }
        ),
    )
    when(migrate).get_database().thenReturn(annotations_database)
    when(migrate).legacy_photo_visibility(annotations_database).thenReturn(
        MongoMediaReader(database)
    )
    when(migrate).create_annotations_service(context).thenReturn(service)

    migrate.regenerate_images(context)
    return annotations_repository, cropped_repository, service


def test_regeneration_produces_no_crops_for_removed_legacy_photos(when, database):
    _suppress(database, REMOVED)

    annotations_repository, cropped_repository, service = _regenerate(
        when, database, [REMOVED, KEPT]
    )

    verify(annotations_repository, times=0).query_by_museum_number(REMOVED)
    verify(service, times=1)._cropped_image_from_annotations(...)
    verify(cropped_repository, times=1).create_many(...)
    verify(annotations_repository, times=1).create_or_update(...)


def test_regeneration_is_unchanged_without_visibility_records(when, database):
    annotations_repository, cropped_repository, service = _regenerate(
        when, database, [REMOVED, KEPT]
    )

    verify(service, times=2)._cropped_image_from_annotations(...)
    verify(cropped_repository, times=2).create_many(...)


def test_migration_service_receives_media_visibility_when_enabled():
    media_service = mock()
    context = cast(
        Context, mock({"media": MediaRuntime(service=media_service, store=mock())})
    )

    assert migrate.create_annotations_service(context)._media is media_service


def test_migration_service_works_with_media_disabled():
    context = cast(Context, mock({"media": None}))

    assert migrate.create_annotations_service(context)._media is None
