import json
from typing import Callable, cast

import attr
import pytest
from falcon import testing
from pymongo.database import Database

from ebl.corpus.application.text_repository import TextRepository
from ebl.corpus.domain.text import Text
from ebl.fragmentarium.infrastructure.mongo_fragment_repository import (
    MongoFragmentRepository,
)
from ebl.tests.factories.fragment import FragmentFactory
from ebl.tests.corpus.mongo_text_repository_fixtures import (
    CHAPTER_WITH_QUERY_LEMMA,
    CHAPTERS_COLLECTION,
    LITERATURE_TEXT,
    QUERY_LEMMA,
    when_chapter_in_collection,
    when_text_in_collection,
)
from ebl.transliteration.domain.tokens import NullSignsCollectingVisitor
from ebl.transliteration.domain.transliteration_query import TransliterationQuery
from ebl.transliteration.domain.museum_number import MuseumNumber


CHAPTER = attr.evolve(
    CHAPTER_WITH_QUERY_LEMMA,
    manuscripts=tuple(
        attr.evolve(
            manuscript,
            siglum_disambiguator="",
            accession="",
            notes="",
            references=(),
            museum_number=MuseumNumber("X", "42"),
        )
        for manuscript in CHAPTER_WITH_QUERY_LEMMA.manuscripts
    ),
    signs=("KU",),
)
READS: dict[str, Callable[[TextRepository], object]] = {
    "text": lambda repository: repository.find(CHAPTER.text_id),
    "chapter": lambda repository: repository.find_chapter(CHAPTER.id_),
    "chapter_with_revision": lambda repository: repository.find_chapter_with_revision(
        CHAPTER.id_
    ),
    "outline": lambda repository: repository.find_chapter_outline(CHAPTER.id_),
    "line_snapshot": lambda repository: repository.find_line_with_revision(
        CHAPTER.id_, 0
    ),
    "display": lambda repository: repository.find_chapter_for_display(CHAPTER.id_),
    "manuscripts": lambda repository: repository.query_manuscripts_by_chapter(
        CHAPTER.id_
    ),
    "joins": lambda repository: repository.query_manuscripts_with_joins_by_chapter(
        CHAPTER.id_
    ),
    "attestations": lambda repository: repository.query_corpus_by_manuscripts(
        [MuseumNumber("X", "42")]
    ),
    "lemma": lambda repository: repository.query_by_lemma(QUERY_LEMMA),
    "transliteration": lambda repository: repository.query_by_transliteration(
        TransliterationQuery("", NullSignsCollectingVisitor()),
        0,
    ),
}


@pytest.mark.parametrize("operation", READS)
def test_all_repository_reads_accept_legacy_manuscripts_without_rewriting_storage(
    database: Database,
    text_repository: TextRepository,
    operation: str,
) -> None:
    when_text_in_collection(database, text=attr.evolve(LITERATURE_TEXT, references=()))
    when_chapter_in_collection(database, chapter=CHAPTER)
    expected = READS[operation](text_repository)
    assert expected
    if operation == "text":
        assert cast(Text, expected).chapters
    elif operation == "transliteration":
        assert isinstance(expected, tuple) and expected[0]
    database[CHAPTERS_COLLECTION].update_many(
        {},
        {
            "$unset": {
                f"manuscripts.$[].{field}": ""
                for field in ("siglumDisambiguator", "accession", "notes", "references")
            }
        },
    )
    original = database[CHAPTERS_COLLECTION].find_one()
    assert READS[operation](text_repository) == expected
    assert database[CHAPTERS_COLLECTION].find_one() == original


def test_fragment_corpus_route_accepts_legacy_manuscript(
    database: Database,
    client: testing.TestClient,
    fragment_repository: MongoFragmentRepository,
) -> None:
    when_text_in_collection(database, text=attr.evolve(LITERATURE_TEXT, references=()))
    when_chapter_in_collection(database, chapter=CHAPTER)
    database[CHAPTERS_COLLECTION].update_many(
        {},
        {
            "$unset": {
                f"manuscripts.$[].{field}": ""
                for field in ("siglumDisambiguator", "accession", "notes", "references")
            }
        },
    )
    fragment_repository.create(FragmentFactory.build(number=MuseumNumber("X", "42")))
    response = cast(testing.Result, client.simulate_get("/fragments/X.42/corpus"))
    assert response.status_code == 200
    payload = json.loads(response.content)
    assert len(payload["manuscriptAttestations"]) == 1
