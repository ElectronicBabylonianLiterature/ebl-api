import pytest

from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.dictionary.application.dictionary_service import Dictionary
from ebl.fragmentarium.infrastructure.mongo_fragment_repository import (
    MongoFragmentRepository,
)
from ebl.tests.lemmatization.lemma_batch_support import (
    WORD_IDS,
    create_chapter,
    create_fragments,
)


@pytest.fixture
def seeded_tokens(
    fragment_repository: MongoFragmentRepository, text_repository: MongoTextRepository
) -> None:
    fragment_repository.create_many(create_fragments())
    text_repository.create_chapter(create_chapter())


@pytest.fixture
def seeded_lemmas(seeded_tokens: None, dictionary: Dictionary, word: dict) -> None:
    for word_id in WORD_IDS:
        dictionary.create({**word, "_id": word_id, "guideWord": word_id})
