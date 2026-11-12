import attr
import pytest

from ebl.errors import NotFoundError
from ebl.sumerian_dictionary.domain.sumerian_word import AkkadianEquivalent, Sources
from ebl.sumerian_dictionary.domain.sumerian_word_links import (
    CrossReference,
    WordLink,
)
from ebl.sumerian_dictionary.domain.sumerian_word_summary import Statistics
from ebl.sumerian_dictionary.infrastructure.mongo_sumerian_word_repository import (
    INDEXED_FIELDS,
    MongoSumerianWordRepository,
)
from ebl.tests.factories.sumerian_dictionary import (
    AttingerSourceFactory,
    Epsd2SourceFactory,
    SumerianWordFactory,
    build_complete_word,
)
from ebl.tests.sumerian_dictionary.conftest import InsertWords

UNMANAGED_DOCUMENT = {"_id": "legacy", "citationForm": "lugal"}


def _target(id_: str, citation_form: str, homonym: str, guide_word: str):
    return SumerianWordFactory.build(
        id=id_, citation_form=citation_form, homonym=homonym, guide_word=guide_word
    )


def test_find_resolves_every_link(
    sumerian_word_repository: MongoSumerianWordRepository, insert_words: InsertWords
) -> None:
    word = build_complete_word()
    insert_words(
        word,
        _target("o0000001", "lu₂", "I", "man"),
        _target("o0000002", "lugal-ĝu₁₀", "", "my king"),
        _target("o0000003", "Lugal-banda", "", "Lugalbanda"),
        _target("o0000004", "nin", "I", "lady"),
        _target("o0000005", "Nin-lil₂", "", "Ninlil"),
    )

    expected = attr.evolve(
        word,
        head=WordLink("o0000001", "lu₂", "I", "man"),
        compounds=(WordLink("o0000002", "lugal-ĝu₁₀", "", "my king"),),
        name_compounds=(WordLink("o0000003", "Lugal-banda", "", "Lugalbanda"),),
        cross_references=(
            attr.evolve(
                word.cross_references[0],
                targets=(WordLink("o0000004", "nin", "I", "lady"),),
                name_targets=(WordLink("o0000005", "Nin-lil₂", "", "Ninlil"),),
            ),
        ),
    )

    assert sumerian_word_repository.find(word.id) == expected


def test_find_keeps_links_whose_target_is_missing(
    sumerian_word_repository: MongoSumerianWordRepository, insert_words: InsertWords
) -> None:
    word = SumerianWordFactory.build(
        head=WordLink("gone", "ignored"),
        compounds=(WordLink("gone-too", "lugal-x", "II", "stale"),),
        cross_references=(
            CrossReference("see", "x", "unresolved", (WordLink("gone", "x"),), ()),
        ),
    )
    insert_words(word)

    found = sumerian_word_repository.find(word.id)

    assert found.head == WordLink("gone", "")
    assert found.compounds == (WordLink("gone-too", "lugal-x", "II", "stale"),)
    assert found.cross_references[0].targets == (WordLink("gone", "x"),)


def test_find_word_without_links(
    sumerian_word_repository: MongoSumerianWordRepository, insert_words: InsertWords
) -> None:
    word = SumerianWordFactory.build()
    insert_words(word)

    assert sumerian_word_repository.find(word.id) == word


def test_find_missing_word(
    sumerian_word_repository: MongoSumerianWordRepository,
) -> None:
    with pytest.raises(NotFoundError, match="Sumerian word 'sux-000001' not found."):
        sumerian_word_repository.find("sux-000001")


def test_find_unmanaged_document(
    sumerian_word_repository: MongoSumerianWordRepository,
) -> None:
    sumerian_word_repository._collection.insert_one(UNMANAGED_DOCUMENT)

    with pytest.raises(NotFoundError, match="Sumerian word 'legacy' not found."):
        sumerian_word_repository.find("legacy")


def test_create_indexes(sumerian_word_repository: MongoSumerianWordRepository) -> None:
    sumerian_word_repository.create_indexes()

    indexed = {
        key
        for index in sumerian_word_repository._collection.index_information().values()
        for key, _ in index["key"]
    }
    assert indexed == {"_id", *INDEXED_FIELDS}


def test_list_ids_skips_unmanaged_documents(
    sumerian_word_repository: MongoSumerianWordRepository, insert_words: InsertWords
) -> None:
    insert_words(SumerianWordFactory.build(id="o2"), SumerianWordFactory.build(id="o1"))
    sumerian_word_repository._collection.insert_one(UNMANAGED_DOCUMENT)

    assert sorted(sumerian_word_repository.list_ids()) == ["o1", "o2"]


def test_statistics(
    sumerian_word_repository: MongoSumerianWordRepository, insert_words: InsertWords
) -> None:
    attinger = Sources(attinger=AttingerSourceFactory.build())
    aligned = Sources(AttingerSourceFactory.build(), Epsd2SourceFactory.build())
    epsd2 = Sources(epsd2=Epsd2SourceFactory.build())
    insert_words(
        SumerianWordFactory.build(sources=attinger),
        SumerianWordFactory.build(sources=aligned, pos="DN"),
        SumerianWordFactory.build(sources=epsd2, pos="PN"),
        SumerianWordFactory.build(
            sources=epsd2,
            akkadian_equivalents=(AkkadianEquivalent("šarru I", "borger"),),
        ),
    )
    sumerian_word_repository._collection.insert_one(UNMANAGED_DOCUMENT)

    assert sumerian_word_repository.statistics() == Statistics(4, 2, 1, 2, 2, 1)


def test_statistics_of_an_empty_collection(
    sumerian_word_repository: MongoSumerianWordRepository,
) -> None:
    assert sumerian_word_repository.statistics() == Statistics(0, 0, 0, 0, 0, 0)
