from ebl.fragmentarium.application.named_entity_schema import NamedEntitySchema
import pytest

import ebl.transliteration.domain.atf as atf
from ebl.tests.asserts import assert_token_serialization
from ebl.transliteration.application.token_schemas import OneOfTokenSchema
from ebl.transliteration.domain.greek_tokens import GreekLetter, GreekWord
from ebl.transliteration.domain.language import Language


def test_greek_letter() -> None:
    alphabet = "α"
    flag = atf.Flag.UNCERTAIN
    greek_letter = GreekLetter.of(alphabet, [flag])

    assert greek_letter.value == f"{alphabet}{flag.value}"
    assert greek_letter.clean_value == alphabet
    assert greek_letter.get_key() == f"GreekLetter⁝{greek_letter.value}"
    assert greek_letter.lemmatizable is False

    serialized = {"type": "GreekLetter", "letter": alphabet, "flags": [flag.value]}
    assert_token_serialization(greek_letter, serialized)


@pytest.mark.parametrize(
    "word,expected,language,lemmatizable,alignable",
    [
        (
            GreekWord.of((GreekLetter.of("α"), GreekLetter.of("β"))),
            "αβ",
            Language.GREEK,
            False,
            False,
        ),
        (
            GreekWord.of(
                (GreekLetter.of("α"), GreekLetter.of("β")), language=Language.AKKADIAN
            ),
            "αβ",
            Language.AKKADIAN,
            True,
            True,
        ),
        (
            GreekWord.of(
                (GreekLetter.of("α"), GreekLetter.of("β")), language=Language.SUMERIAN
            ),
            "αβ",
            Language.SUMERIAN,
            False,
            True,
        ),
    ],
)
def test_greek_word(
    word: GreekWord,
    expected: str,
    language: Language,
    lemmatizable: bool,
    alignable: bool,
) -> None:
    assert word.value == expected
    assert word.clean_value == expected.translate(str.maketrans("", "", "[]()<>#?!"))
    assert word.language == language
    assert word.normalized is False
    assert word.lemmatizable is lemmatizable
    assert word.alignable is alignable

    serialized = {
        "type": "GreekWord",
        "parts": OneOfTokenSchema().dump(word.parts, many=True),
        "uniqueLemma": [],
        "alignment": None,
        "variant": None,
        "lemmatizable": lemmatizable,
        "alignable": alignable,
        "normalized": word.normalized,
        "language": language.name,
        "hasVariantAlignment": word.has_variant_alignment,
        "hasOmittedAlignment": word.has_omitted_alignment,
        "id": word.id_,
        "namedEntities": NamedEntitySchema().dump(word.named_entities, many=True)
    }
    assert_token_serialization(word, serialized)
