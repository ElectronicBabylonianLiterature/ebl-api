import json
from typing import Any, Dict, List, Sequence, Tuple, cast

from falcon import testing

from ebl.corpus.domain.chapter import Chapter
from ebl.dictionary.domain.word import WordId
from ebl.fragmentarium.domain.fragment import Fragment
from ebl.lemmatization.domain.lemmatization import Lemma
from ebl.tests.factories.corpus import (
    ChapterFactory,
    LineFactory,
    LineVariantFactory,
    ManuscriptLineFactory,
)
from ebl.tests.factories.fragment import FragmentFactory
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.normalized_akkadian import AkkadianWord
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import LanguageShift, Token, ValueToken
from ebl.transliteration.domain.word_tokens import Word

__all__ = ("WORD_IDS",)

Query = Tuple[str, bool]
BATCH_URL = "/lemmas/batch"
NO_LEMMA: Lemma = ()


def create_lemma(*ids: str) -> Lemma:
    return tuple(WordId(id_) for id_ in ids)


def create_word(reading: str, lemma: Lemma) -> Word:
    return Word.of([Reading.of_name(reading)], unique_lemma=lemma)


def create_normalized_word(value: str, lemma: Lemma) -> AkkadianWord:
    return AkkadianWord.of((ValueToken.of(value),), unique_lemma=lemma)


ANA_I = create_lemma("ana I")
ANA_II = create_lemma("ana II")
ANA_III = create_lemma("ana III")
ANA_IV = create_lemma("ana IV")
KU = create_lemma("kû I", "kû II")
TA = create_lemma("ta I")
BUARU = create_lemma("buāru I")
TIED_LEMMAS: Sequence[Lemma] = (
    create_lemma("ši III"),
    create_lemma("ši I", "ši IV"),
    create_lemma("ši II"),
    create_lemma("ši I"),
)
FRAGMENT_TOKENS: Sequence[Sequence[Token]] = (
    (
        create_word("ana", ANA_II),
        create_word("ana", ANA_II),
        create_word("ana", ANA_I),
        create_word("ku", KU),
        create_word("mu", NO_LEMMA),
        create_normalized_word("ana", ANA_III),
    ),
    tuple(create_word("ši", lemma) for lemma in TIED_LEMMAS),
)
RECONSTRUCTION: Sequence[Token] = (
    LanguageShift.normalized_akkadian(),
    create_normalized_word("ana", ANA_IV),
    create_normalized_word("ana", ANA_IV),
    create_normalized_word("buāru", BUARU),
)
MANUSCRIPT_TOKENS: Sequence[Token] = (
    create_word("ana", ANA_I),
    create_word("ana", ANA_I),
    create_word("ana", ANA_I),
    create_word("ta", TA),
)
QUERIES: Sequence[Query] = (
    ("ana", False),
    ("ana", True),
    ("ku", False),
    ("ta", False),
    ("mu", False),
    ("absent", False),
    ("absent", True),
    ("ana", False),
    ("ši", False),
    ("buāru", True),
    ("buāru", False),
    ("ta", True),
)
EXPECTED_LEMMAS: Sequence[Sequence[Lemma]] = (
    (ANA_I, ANA_II),
    (ANA_IV, ANA_III),
    (KU,),
    (TA,),
    (),
    (),
    (),
    (ANA_I, ANA_II),
    (
        create_lemma("ši I"),
        create_lemma("ši I", "ši IV"),
        create_lemma("ši II"),
        create_lemma("ši III"),
    ),
    (BUARU,),
    (),
    (),
)
WORD_IDS: Sequence[str] = tuple(
    dict.fromkeys(
        unique_lemma
        for lemmas in EXPECTED_LEMMAS
        for lemma in lemmas
        for unique_lemma in lemma
    )
)


def create_fragments() -> Sequence[Fragment]:
    return [
        FragmentFactory.build(
            text=Text.of_iterable([TextLine.of_iterable(LineNumber(1), tokens)]),
            signs="",
        )
        for tokens in FRAGMENT_TOKENS
    ]


def create_chapter() -> Chapter:
    return ChapterFactory.build(
        lines=(
            LineFactory.build(
                variants=(
                    LineVariantFactory.build(
                        reconstruction=RECONSTRUCTION,
                        manuscripts=(
                            ManuscriptLineFactory.build(
                                manuscript_id=1,
                                line=TextLine.of_iterable(
                                    LineNumber(1), MANUSCRIPT_TOKENS
                                ),
                            ),
                        ),
                    ),
                )
            ),
        )
    )


def create_body(queries: Sequence[Query]) -> Dict[str, Any]:
    return {
        "words": [
            {"word": word, "isNormalized": is_normalized}
            for word, is_normalized in queries
        ]
    }


def post_batch(client: testing.TestClient, body: object) -> testing.Result:
    result = client.simulate_post(BATCH_URL, body=json.dumps(body))
    assert isinstance(result, testing.Result)
    return result


def get_lemmas(client: testing.TestClient, query: Query) -> testing.Result:
    word, is_normalized = query
    result = client.simulate_get(
        "/lemmas", params={"word": word, "isNormalized": is_normalized}
    )
    assert isinstance(result, testing.Result)
    return result


def find_lemma_ids(lemmas: Sequence[Sequence[Dict[str, Any]]]) -> List[Lemma]:
    return [create_lemma(*(word["_id"] for word in lemma)) for lemma in lemmas]


def read_entries(result: testing.Result) -> List[Dict[str, Any]]:
    return cast(List[Dict[str, Any]], result.json)


def read_lemmas(result: testing.Result) -> List[List[Dict[str, Any]]]:
    return cast(List[List[Dict[str, Any]]], result.json)


def find_entry_lemma_ids(result: testing.Result) -> List[List[Lemma]]:
    return [find_lemma_ids(entry["lemmas"]) for entry in read_entries(result)]
