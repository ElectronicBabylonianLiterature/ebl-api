import attr
import pytest

from ebl.atf.atf import Atf
from ebl.dictionary.domain.word import WordId
from ebl.errors import NotFoundError
from ebl.fragmentarium.application.transliteration_update import \
    TransliterationUpdate
from ebl.fragmentarium.domain.fragment import UncuratedReference
from ebl.tests.factories.bibliography import ReferenceFactory
from ebl.tests.factories.fragment import (FragmentFactory,
                                          InterestingFragmentFactory,
                                          LemmatizedFragmentFactory,
                                          TransliteratedFragmentFactory)
from ebl.transliteration.labels import LineNumberLabel
from ebl.transliteration.lemmatization import Lemmatization
from ebl.transliteration.line import ControlLine, EmptyLine, TextLine
from ebl.transliteration.text import Text
from ebl.transliteration.token import Token, Word
from ebl.transliteration_search.transliteration_query import \
    TransliterationQuery

COLLECTION = 'fragments'


ANOTHER_LEMMATIZED_FRAGMENT = attr.evolve(
    TransliteratedFragmentFactory.build(),
    text=Text((
        TextLine("1'.", (
            Word('GI₆', unique_lemma=(WordId('ginâ I'),)),
            Word('ana', unique_lemma=(WordId('ana II'),)),
            Word('ana', unique_lemma=(WordId('ana II'),)),
            Word('u₄-šu', unique_lemma=(WordId('ūsu I'),))
        )),
    )),
    signs='MI DIŠ DIŠ UD ŠU'
)


def test_create(database, fragment_repository):
    fragment = FragmentFactory.build()
    fragment_number = fragment_repository.create(fragment)

    assert database[COLLECTION].find_one({
        '_id': fragment_number
    }) == fragment.to_dict()


def test_find(database, fragment_repository):
    fragment = FragmentFactory.build()
    database[COLLECTION].insert_one(fragment.to_dict())

    assert fragment_repository.find(fragment.number) == fragment


def test_find_random(fragment_repository,):
    fragment = FragmentFactory.build()
    transliterated_fragment = TransliteratedFragmentFactory.build()
    for a_fragment in fragment, transliterated_fragment:
        fragment_repository.create(a_fragment)

    assert fragment_repository.find_random() ==\
        [transliterated_fragment]


def test_find_interesting(fragment_repository):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    interesting_fragment = InterestingFragmentFactory.build()
    too_many_references = InterestingFragmentFactory.build(
        uncurated_references=(
            UncuratedReference('7(0)'),
            UncuratedReference('CAD 51', (34, 56)),
            UncuratedReference('7(1)'),
            UncuratedReference('CAD 53', (1,)),
        )
    )
    not_kuyunjik = InterestingFragmentFactory.build(
        collection='Not Kuyunjik'
    )

    for fragment in [
            transliterated_fragment,
            interesting_fragment,
            too_many_references,
            not_kuyunjik
    ]:
        fragment_repository.create(fragment)

    assert fragment_repository.find_interesting() ==\
        [interesting_fragment]


def test_fragment_not_found(fragment_repository):
    with pytest.raises(NotFoundError):
        fragment_repository.find('unknown id')


def test_update_transliteration_with_record(fragment_repository,
                                            user):
    fragment = FragmentFactory.build()
    fragment_number = fragment_repository.create(fragment)
    updated_fragment = fragment.update_transliteration(
        TransliterationUpdate(Atf('$ (the transliteration)'), 'notes'),
        user
    )

    fragment_repository.update_transliteration(
        updated_fragment
    )
    result = fragment_repository.find(fragment_number)

    assert result == updated_fragment


def test_update_update_transliteration_not_found(fragment_repository):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    with pytest.raises(NotFoundError):
        fragment_repository.update_transliteration(
            transliterated_fragment
        )


def test_update_lemmatization(fragment_repository):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    fragment_number = fragment_repository.create(transliterated_fragment)
    tokens = transliterated_fragment.text.lemmatization.to_list()
    tokens[1][3]['uniqueLemma'] = ['aklu I']
    updated_fragment = transliterated_fragment.update_lemmatization(
        Lemmatization.from_list(tokens)
    )

    fragment_repository.update_lemmatization(
        updated_fragment
    )
    result = fragment_repository.find(fragment_number)

    assert result == updated_fragment


def test_update_update_lemmatization_not_found(fragment_repository):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    with pytest.raises(NotFoundError):
        fragment_repository.update_lemmatization(
            transliterated_fragment
        )


def test_statistics(database, fragment_repository):
    database[COLLECTION].insert_many([
        FragmentFactory.build(text=Text((
            TextLine('1.', (Word('first'), Word('line'))),
            ControlLine('$', (Token('ignore'), )),
            EmptyLine()
        ))).to_dict(),
        FragmentFactory.build(text=Text((
            ControlLine('$', (Token('ignore'), )),
            TextLine('1.', (Word('second'), )),
            TextLine('1.', (Word('third'), )),
            ControlLine('$', (Token('ignore'), )),
            TextLine('1.', (Word('fourth'), )),
        ))).to_dict(),
        FragmentFactory.build(text=Text()).to_dict()
    ])

    assert fragment_repository.count_transliterated_fragments() == 2
    assert fragment_repository.count_lines() == 4


def test_statistics_no_fragments(fragment_repository):
    assert fragment_repository.count_transliterated_fragments() == 0
    assert fragment_repository.count_lines() == 0


def test_search_finds_by_id(database, fragment_repository):
    fragment = FragmentFactory.build()
    database[COLLECTION].insert_many([
        fragment.to_dict(),
        FragmentFactory.build().to_dict()
    ])

    assert fragment_repository.search(fragment.number) == [fragment]


def test_search_finds_by_accession(database, fragment_repository):
    fragment = FragmentFactory.build()
    database[COLLECTION].insert_many([
        fragment.to_dict(),
        FragmentFactory.build().to_dict()
    ])

    assert fragment_repository.search(
        fragment.accession
    ) == [fragment]


def test_search_finds_by_cdli(database, fragment_repository):
    fragment = FragmentFactory.build()
    database[COLLECTION].insert_many([
        fragment.to_dict(),
        FragmentFactory.build().to_dict()
    ])

    assert fragment_repository.search(
        fragment.cdli_number
    ) == [fragment]


def test_search_not_found(fragment_repository):
    assert fragment_repository.search('K.1') == []


SEARCH_SIGNS_DATA = [
    ([['DIŠ', 'UD']], True),
    ([['KU']], True),
    ([['UD']], True),
    ([
        ['MI', 'DIŠ'],
        ['ABZ411', 'BA', 'MA']
    ], True),
    ([['IGI', 'UD']], False),
]


@pytest.mark.parametrize('signs,is_match', SEARCH_SIGNS_DATA)
def test_search_signs(signs,
                      is_match,
                      fragment_repository):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    fragment_repository.create(transliterated_fragment)
    fragment_repository.create(FragmentFactory.build())

    result = fragment_repository.search_signs(TransliterationQuery(signs))
    expected = [transliterated_fragment] if is_match else []
    assert result == expected


def test_find_transliterated(database,
                             fragment_repository):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    database[COLLECTION].insert_many([
        transliterated_fragment.to_dict(),
        FragmentFactory.build().to_dict()
    ])

    assert fragment_repository.find_transliterated() ==\
        [transliterated_fragment]


def test_find_lemmas(fragment_repository):
    lemmatized_fragment = LemmatizedFragmentFactory.build()
    fragment_repository.create(lemmatized_fragment)
    fragment_repository.create(ANOTHER_LEMMATIZED_FRAGMENT)

    assert fragment_repository.find_lemmas('GI₆') == [['ginâ I']]


def test_find_lemmas_multiple(fragment_repository):
    lemmatized_fragment = LemmatizedFragmentFactory.build()
    fragment_repository.create(lemmatized_fragment)
    fragment_repository.create(ANOTHER_LEMMATIZED_FRAGMENT)

    assert fragment_repository.find_lemmas('ana') ==\
        [['ana II'], ['ana I']]


@pytest.mark.parametrize('value', [
    '[(a[(n)]a#*?!)]',
    '°\\ana°'
])
def test_find_lemmas_ignores_in_value(value, fragment_repository):
    fragment = FragmentFactory.build(
        text=Text.of_iterable([
            TextLine.of_iterable(LineNumberLabel.from_atf("1'."), [
                Word(value,  unique_lemma=(WordId('ana I'),))
            ])
        ]),
        signs='DIŠ'
    )
    fragment_repository.create(fragment)

    assert fragment_repository.find_lemmas('ana') == [['ana I']]


@pytest.mark.parametrize('query,expected', [
    ('[(a)]n[(a*#!?)]', [['ana I']]),
    ('°ana\\me-e-li°', []),
    ('°me-e-li\\ana°', [['ana I']]),
    ('°\\ana°', [['ana I']])
])
def test_find_lemmas_ignores_in_query(query,
                                      expected,
                                      fragment_repository):
    lemmatized_fragment = LemmatizedFragmentFactory.build()
    fragment_repository.create(lemmatized_fragment)

    assert fragment_repository.find_lemmas(query) == expected


def test_find_lemmas_not_found(fragment_repository):
    lemmatized_fragment = LemmatizedFragmentFactory.build()
    fragment_repository.create(lemmatized_fragment)
    assert fragment_repository.find_lemmas('aklu') == []


def test_update_references(fragment_repository):
    reference = ReferenceFactory.build()
    fragment = FragmentFactory.build()
    fragment_number = fragment_repository.create(fragment)
    references = (reference,)
    updated_fragment = fragment.set_references(references)

    fragment_repository.update_references(updated_fragment)
    result = fragment_repository.find(fragment_number)

    assert result == updated_fragment


def test_update_update_references(fragment_repository):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    with pytest.raises(NotFoundError):
        fragment_repository.update_references(
            transliterated_fragment
        )
