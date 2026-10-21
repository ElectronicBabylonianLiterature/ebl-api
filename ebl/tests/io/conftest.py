import pytest

from ebl.fragmentarium.application.fragment_schema import FragmentSchema
from ebl.fragmentarium.domain.fragment import Fragment
from ebl.mongo_collection import MongoCollection
from ebl.tests.factories.fragment import LemmatizedFragmentFactory


@pytest.fixture
def fragment() -> Fragment:
    return LemmatizedFragmentFactory.build()


@pytest.fixture
def fragment_schema(seeded_provenance_service) -> FragmentSchema:
    return FragmentSchema(context={"provenance_service": seeded_provenance_service})


@pytest.fixture
def valid_fragment_data(fragment, fragment_schema) -> dict:
    return fragment_schema.dump(fragment)


@pytest.fixture
def fragments_collection(fragment_repository) -> MongoCollection:
    return fragment_repository._fragments
