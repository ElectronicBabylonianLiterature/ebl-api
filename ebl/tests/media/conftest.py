from typing import Callable, List, Sequence

import pytest

from ebl.common.domain.scopes import Scope
from ebl.tests.factories.fragment import TransliteratedFragmentFactory

from ebl.media.application import (
    MediaRepository,
    MediaRepresentationStore,
    StoredMedia,
)
from ebl.tests.media.in_memory_media import (
    InMemoryMediaRepository,
    InMemoryRepresentationStore,
)

MediaRepositoryFactory = Callable[[Sequence[StoredMedia]], MediaRepository]
RepresentationStoreFactory = Callable[[], MediaRepresentationStore]


@pytest.fixture
def call_log() -> List[str]:
    return []


@pytest.fixture
def media_repository_factory(call_log: List[str]) -> MediaRepositoryFactory:
    """Build a repository under test.

    Contract tests depend on this fixture rather than on a concrete class, so a
    future Mongo adapter can reuse the same contract modules by overriding the
    fixture in its own conftest.
    """

    def factory(media: Sequence[StoredMedia] = ()) -> MediaRepository:
        return InMemoryMediaRepository(media, call_log)

    return factory


@pytest.fixture
def representation_store_factory(call_log: List[str]) -> RepresentationStoreFactory:
    """Build a representation store under test. See `media_repository_factory`."""

    def factory() -> MediaRepresentationStore:
        return InMemoryRepresentationStore(call_log)

    return factory


@pytest.fixture
def public_fragment(fragmentarium):
    fragment = TransliteratedFragmentFactory.build(authorized_scopes=[])
    fragmentarium.create(fragment)
    return fragment


@pytest.fixture
def other_public_fragment(fragmentarium):
    fragment = TransliteratedFragmentFactory.build(authorized_scopes=[])
    fragmentarium.create(fragment)
    return fragment


@pytest.fixture
def restricted_fragment(fragmentarium):
    fragment = TransliteratedFragmentFactory.build(
        authorized_scopes=[Scope.READ_COPENHAGEN_FRAGMENTS]
    )
    fragmentarium.create(fragment)
    return fragment


@pytest.fixture
def readable_restricted_fragment(fragmentarium):
    fragment = TransliteratedFragmentFactory.build(
        authorized_scopes=[Scope.READ_CAIC_FRAGMENTS]
    )
    fragmentarium.create(fragment)
    return fragment
