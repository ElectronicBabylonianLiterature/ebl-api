import attr
import pytest
from ebl.errors import NotFoundError
from ebl.text.lemmatization import Lemmatization
from ebl.text.token import Token, Word
from ebl.text.line import TextLine, ControlLine, EmptyLine
from ebl.text.text import Text
from ebl.fragment.transliteration_query import TransliterationQuery
from ebl.fragment.transliteration import Transliteration


COLLECTION = 'fragments'


def test_create(database, fragment_repository, fragment):
    fragment_number = fragment_repository.create(fragment)

    assert database[COLLECTION].find_one({
        '_id': fragment_number
    }) == fragment.to_dict()


def test_find(database, fragment_repository, fragment):
    database[COLLECTION].insert_one(fragment.to_dict())

    assert fragment_repository.find(fragment.number) == fragment


def test_find_random(fragment_repository,
                     fragment,
                     transliterated_fragment):
    for a_fragment in fragment, transliterated_fragment:
        fragment_repository.create(a_fragment)

    assert fragment_repository.find_random() ==\
        [transliterated_fragment]


def test_find_interesting(fragment_repository,
                          fragment,
                          transliterated_fragment,
                          interesting_fragment):
    for a_fragment in fragment, transliterated_fragment, interesting_fragment:
        fragment_repository.create(a_fragment)

    assert fragment_repository.find_interesting() ==\
        [interesting_fragment]


def test_fragment_not_found(fragment_repository):
    with pytest.raises(NotFoundError):
        fragment_repository.find('unknown id')


def test_update_transliteration_with_record(fragment_repository,
                                            fragment,
                                            user):
    fragment_number = fragment_repository.create(fragment)
    updated_fragment = fragment.update_transliteration(
        Transliteration('$ (the transliteration)', 'notes'),
        user
    )

    fragment_repository.update_transliteration(
        updated_fragment
    )
    result = fragment_repository.find(fragment_number)

    assert result == updated_fragment


def test_update_update_transliteration_not_found(fragment_repository,
                                                 transliterated_fragment):
    with pytest.raises(NotFoundError):
        fragment_repository.update_transliteration(
            transliterated_fragment
        )


def test_update_lemmatization(fragment_repository,
                              transliterated_fragment):
    fragment_number = fragment_repository.create(transliterated_fragment)
    tokens = transliterated_fragment.text.lemmatization.to_list()
    tokens[1][1]['uniqueLemma'] = ['aklu I']
    updated_fragment = transliterated_fragment.update_lemmatization(
        Lemmatization.from_list(tokens)
    )

    fragment_repository.update_lemmatization(
        updated_fragment
    )
    result = fragment_repository.find(fragment_number)

    assert result == updated_fragment


def test_update_update_lemmatization_not_found(fragment_repository,
                                               transliterated_fragment):
    with pytest.raises(NotFoundError):
        fragment_repository.update_lemmatization(
            transliterated_fragment
        )


def test_statistics(database, fragment_repository, fragment):
    database[COLLECTION].insert_many([
        {**fragment.to_dict(), '_id': '1', 'text': Text((
            TextLine('1.', (Word('first'), Word('line'))),
            ControlLine('$', (Token('ignore'), )),
            EmptyLine()
        )).to_dict()},
        {**fragment.to_dict(), '_id': '2', 'text': Text((
            ControlLine('$', (Token('ignore'), )),
            TextLine('1.', (Word('second'), )),
            TextLine('1.', (Word('third'), )),
            ControlLine('$', (Token('ignore'), )),
            TextLine('1.', (Word('fourth'), )),
        )).to_dict()},
        {**fragment.to_dict(), '_id': '3', 'text': Text().to_dict()}
    ])

    assert fragment_repository.count_transliterated_fragments() == 2
    assert fragment_repository.count_lines() == 4


def test_statistics_no_fragments(fragment_repository):
    assert fragment_repository.count_transliterated_fragments() == 0
    assert fragment_repository.count_lines() == 0


def test_search_finds_by_id(database,
                            fragment_repository,
                            fragment,
                            another_fragment):
    database[COLLECTION].insert_many([
        fragment.to_dict(),
        another_fragment.to_dict()
    ])

    assert fragment_repository.search(fragment.number) == [fragment]


def test_search_finds_by_accession(database,
                                   fragment_repository,
                                   fragment,
                                   another_fragment):
    database[COLLECTION].insert_many([
        fragment.to_dict(),
        another_fragment.to_dict()
    ])

    assert fragment_repository.search(
        fragment.accession
    ) == [fragment]


def test_search_finds_by_cdli(database,
                              fragment_repository,
                              fragment,
                              another_fragment):
    database[COLLECTION].insert_many([
        fragment.to_dict(),
        another_fragment.to_dict()
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
        ['U', 'BA', 'MA']
    ], True),
    ([['IGI', 'UD']], False),
]


@pytest.mark.parametrize("signs,is_match", SEARCH_SIGNS_DATA)
def test_search_signs(signs,
                      is_match,
                      fragment_repository,
                      transliterated_fragment,
                      another_fragment):
    fragment_repository.create(transliterated_fragment)
    fragment_repository.create(another_fragment)

    result = fragment_repository.search_signs(TransliterationQuery(signs))
    expected = [transliterated_fragment] if is_match else []
    assert result == expected


def test_find_transliterated(database,
                             fragment_repository,
                             transliterated_fragment,
                             another_fragment):
    database[COLLECTION].insert_many([
        transliterated_fragment.to_dict(),
        another_fragment.to_dict()
    ])

    assert fragment_repository.find_transliterated() ==\
        [transliterated_fragment]


def test_find_lemmas(fragment_repository,
                     lemmatized_fragment,
                     another_lemmatized_fragment):
    fragment_repository.create(lemmatized_fragment)
    fragment_repository.create(another_lemmatized_fragment)

    assert fragment_repository.find_lemmas('GI₆') == [['ginâ I']]


def test_find_lemmas_multiple(fragment_repository,
                              lemmatized_fragment,
                              another_lemmatized_fragment):
    fragment_repository.create(lemmatized_fragment)
    fragment_repository.create(another_lemmatized_fragment)

    assert fragment_repository.find_lemmas('ana') ==\
        [['ana II'], ['ana I']]


def test_find_lemmas_ignores_in_value(fragment_repository,
                                      transliterated_fragment):
    fragment = attr.evolve(
        transliterated_fragment,
        number='5',
        text=Text.of_iterable([
            TextLine.of_iterable("1'.", [
                Word('[(a[(n)]a#*?!)]', unique_lemma=("ana I", ))
            ])
        ]),
        signs='DIŠ'
    )
    fragment_repository.create(fragment)

    assert fragment_repository.find_lemmas('ana') ==\
        [['ana I']]


def test_find_lemmas_ignores_in_query(fragment_repository,
                                      lemmatized_fragment):
    fragment_repository.create(lemmatized_fragment)

    assert fragment_repository.find_lemmas('[(a)]n[(a*#!?)]') ==\
        [['ana I']]


def test_find_lemmas_not_found(fragment_repository, lemmatized_fragment):
    fragment_repository.create(lemmatized_fragment)
    assert fragment_repository.find_lemmas('aklu') == []


def test_update_references(fragment_repository, fragment, reference):
    fragment_number = fragment_repository.create(fragment)
    references = (reference,)
    updated_fragment = fragment.set_references(references)

    fragment_repository.update_references(updated_fragment)
    result = fragment_repository.find(fragment_number)

    assert result == updated_fragment


def test_update_update_references(fragment_repository,
                                  transliterated_fragment):
    with pytest.raises(NotFoundError):
        fragment_repository.update_references(
            transliterated_fragment
        )
