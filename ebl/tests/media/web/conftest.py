from io import BytesIO
from typing import Callable

import attr
import pytest
from falcon import testing
from falcon_auth import NoneAuthBackend
from pymongo.database import Database

from ebl.app import create_app
from ebl.context import Context
from ebl.media.application.default_media_service import DefaultMediaService
from ebl.media.application.media_runtime import MediaRuntime
from ebl.media.application.media_stored import (
    DisplayRepresentationWriteRequest,
    OriginalRepresentationWriteRequest,
    StoredMedia,
    StoredMediaRepresentations,
    StoredThumbnailRepresentation,
    ThumbnailRepresentationWriteRequest,
)
from ebl.media.domain import MediaRepresentations, ThumbnailSize
from ebl.tests.factories.fragment import FragmentFactory
from ebl.tests.media.factories import (
    association,
    copy_media,
    original_representation,
    photo_media,
)
from ebl.tests.media.in_memory_media import (
    InMemoryMediaRepository,
    InMemoryRepresentationStore,
)
from ebl.tests.media.representation_helpers import representation_for_content
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.users.domain.user import Guest


@pytest.fixture
def database(media_database: Database) -> Database:
    return media_database


@pytest.fixture
def media_store() -> InMemoryRepresentationStore:
    return InMemoryRepresentationStore()


@pytest.fixture
def media_repository() -> InMemoryMediaRepository:
    return InMemoryMediaRepository()


@pytest.fixture
def media_context(
    context: Context,
    media_repository: InMemoryMediaRepository,
    media_store: InMemoryRepresentationStore,
) -> Context:
    return attr.evolve(
        context,
        media=MediaRuntime(
            DefaultMediaService(media_repository, media_store), media_store
        ),
    )


@pytest.fixture
def media_client(media_context: Context) -> testing.TestClient:
    return testing.TestClient(create_app(media_context))


@pytest.fixture
def guest_media_client(media_context: Context) -> testing.TestClient:
    return testing.TestClient(
        create_app(attr.evolve(media_context, auth_backend=NoneAuthBackend(Guest)))
    )


@pytest.fixture
def create_media(
    media_context: Context,
    media_repository: InMemoryMediaRepository,
    media_store: InMemoryRepresentationStore,
) -> Callable[..., StoredMedia]:
    def create(
        number: str = "K.1", *, svg: bool = False, previews: bool = True
    ) -> StoredMedia:
        fragment_number = MuseumNumber.of(number)
        media_context.fragment_repository.create(
            FragmentFactory.build(number=fragment_number, references=())
        )
        representation = representation_for_content(
            b"original",
            original_representation("image/svg+xml" if svg else "image/png"),
        )
        preview = representation_for_content(b"preview", original_representation())
        factory = copy_media if svg else photo_media
        media = factory(
            associations=(association(fragment_id=fragment_number),),
            media_representations=MediaRepresentations(
                representation,
                ((ThumbnailSize.SMALL, preview),) if previews else (),
                display=preview if previews else None,
            ),
        )
        original = media_store.write_original(
            OriginalRepresentationWriteRequest(
                media.id, BytesIO(b"original"), representation
            )
        )
        thumbnails = (
            (
                StoredThumbnailRepresentation(
                    ThumbnailSize.SMALL,
                    media_store.write_thumbnail(
                        ThumbnailRepresentationWriteRequest(
                            media.id, BytesIO(b"preview"), preview, ThumbnailSize.SMALL
                        )
                    ),
                ),
            )
            if previews
            else ()
        )
        display = (
            media_store.write_display(
                DisplayRepresentationWriteRequest(
                    media.id, BytesIO(b"preview"), preview
                )
            )
            if previews
            else None
        )
        stored = StoredMedia(
            media, StoredMediaRepresentations(original, thumbnails, display=display)
        )
        media_repository.create(stored)
        return stored

    return create
