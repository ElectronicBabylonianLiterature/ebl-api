from typing import cast
import attr
import pytest

from ebl.corpus.domain.text import UncertainFragment
from ebl.errors import NotFoundError
from ebl.fragmentarium.application.joins_schema import JoinSchema
from ebl.fragmentarium.domain.joins import Join, Joins
from ebl.tests.corpus.mongo_text_repository_fixtures import (
    CHAPTER,
    CHAPTER_SIGN_SCHEMA,
    JOINS_COLLECTION,
    MUSEUM_NUMBER,
    TEXT,
    UNCERTAIN_FRAGMENT,
    when_chapter_in_collection,
    when_text_in_collection,
)
from ebl.tests.factories.corpus import (
    ManuscriptAttestationFactory,
    UncertainFragmentAttestationFactory,
)
from ebl.tests.factories.fragment import FragmentFactory


def test_query_manuscripts_by_chapter(database, text_repository) -> None:
    when_chapter_in_collection(database)

    assert text_repository.query_manuscripts_by_chapter(CHAPTER.id_) == list(
        CHAPTER.manuscripts
    )


def test_query_manuscripts_by_chapter_not_found(database, text_repository) -> None:
    with pytest.raises(NotFoundError):
        assert text_repository.query_manuscripts_by_chapter(CHAPTER.id_)


def test_query_manuscripts_with_joins_by_chapter_no_joins(
    database, text_repository
) -> None:
    when_chapter_in_collection(database)

    assert text_repository.query_manuscripts_with_joins_by_chapter(CHAPTER.id_) == list(
        CHAPTER.manuscripts
    )


def test_query_manuscripts_with_joins_is_in_fragmentarium(
    database, text_repository, fragment_repository
) -> None:
    fragment_repository.create(FragmentFactory.build(number=MUSEUM_NUMBER))
    when_chapter_in_collection(database)

    assert text_repository.query_manuscripts_with_joins_by_chapter(CHAPTER.id_) == [
        attr.evolve(CHAPTER.manuscripts[0], is_in_fragmentarium=True)
    ]


def test_query_manuscripts_with_joins_by_chapter(database, text_repository) -> None:
    when_chapter_in_collection(database)
    join = Join(MUSEUM_NUMBER)
    database[JOINS_COLLECTION].insert_one(
        {
            "fragments": [
                {
                    **cast(
                        dict, JoinSchema(exclude=["is_in_fragmentarium"]).dump(join)
                    ),
                    "group": 0,
                }
            ]
        }
    )

    assert text_repository.query_manuscripts_with_joins_by_chapter(CHAPTER.id_) == [
        attr.evolve(CHAPTER.manuscripts[0], joins=Joins(((join,),)))
    ]


def test_query_corpus_by_manuscripts(database, text_repository) -> None:
    when_text_in_collection(database, text=attr.evolve(TEXT, references=()))
    when_chapter_in_collection(database)

    expected_manuscript_attestation = ManuscriptAttestationFactory.build(
        text=attr.evolve(TEXT, references=()),
        chapter_id=CHAPTER.id_,
        manuscript=CHAPTER.manuscripts[0],
    )

    assert text_repository.query_corpus_by_manuscripts(
        [CHAPTER.manuscripts[0].museum_number]
    ) == [expected_manuscript_attestation]


def test_query_corpus_by_uncertain_fragments(
    database, text_repository, fragment_repository
) -> None:
    text_with_uncertain_fragment = attr.evolve(
        TEXT,
        chapters=(
            attr.evolve(
                TEXT.chapters[0],
                uncertain_fragments=(UncertainFragment(UNCERTAIN_FRAGMENT),),
            ),
        ),
        references=(),
    )
    chapter_with_uncertain_fragment = attr.evolve(
        CHAPTER, uncertain_fragments=(UNCERTAIN_FRAGMENT,)
    )
    when_text_in_collection(database, text_with_uncertain_fragment)
    when_chapter_in_collection(database, chapter_with_uncertain_fragment)
    cleaned_text = attr.evolve(
        text_with_uncertain_fragment,
        chapters=(
            attr.evolve(
                text_with_uncertain_fragment.chapters[0],
                uncertain_fragments=(),
            ),
        ),
    )
    expected_uncertain_fragment_attestation = UncertainFragmentAttestationFactory.build(
        text=cleaned_text,
        chapter_id=chapter_with_uncertain_fragment.id_,
    )
    result = text_repository.query_corpus_by_uncertain_fragments(
        [chapter_with_uncertain_fragment.uncertain_fragments[0]]
    )
    assert result == [expected_uncertain_fragment_attestation]


def test_get_sign_data(database, text_repository):
    when_chapter_in_collection(database)
    assert text_repository.get_sign_data(CHAPTER.id_) == CHAPTER_SIGN_SCHEMA.dump(
        CHAPTER
    )


def test_get_all_sign_data(text_repository):
    signs = [
        ["", None],
        ["KU", "TA"],
        ["MI", "NA"],
    ]

    def sort_by_signs(chapters):
        return sorted(chapters, key=lambda chapter: chapter["signs"])

    chapters = [attr.evolve(CHAPTER, signs=signs_) for signs_ in signs]

    for chapter in chapters:
        text_repository.create_chapter(chapter)

    assert sort_by_signs(text_repository.get_all_sign_data()) == sort_by_signs(
        CHAPTER_SIGN_SCHEMA.dump(
            [chapter for chapter in chapters if any(chapter.signs)], many=True
        )
    )
