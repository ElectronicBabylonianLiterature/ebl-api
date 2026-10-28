from typing import Dict, Mapping, cast

import attr
import pytest
from marshmallow import Schema, ValidationError

from ebl.sumerian_dictionary.domain.sumerian_word import (
    Attestation,
    Match,
    Sources,
    SumerianWord,
)
from ebl.sumerian_dictionary.domain.sumerian_word_links import WordLink
from ebl.sumerian_dictionary.infrastructure.sumerian_schema_base import AttrsSchema
from ebl.sumerian_dictionary.infrastructure.sumerian_word_schemas import (
    SumerianWordDocumentSchema,
    SumerianWordSchema,
)
from ebl.tests.factories.sumerian_dictionary import (
    Epsd2SourceFactory,
    SumerianWordFactory,
    build_complete_word,
)

LIST_FIELDS = (
    "lemma",
    "stems",
    "determinatives",
    "caseFrame",
    "emesal",
    "attingerSenses",
    "epsd2Senses",
    "attingerForms",
    "epsd2Forms",
    "signs",
    "renderings",
    "compounds",
    "nameCompounds",
    "crossReferences",
    "aliases",
    "akkadianEquivalents",
    "citations",
)

MINIMAL_MATCH = {
    "tier": "epsd2-only",
    "method": "none",
    "spelling": "a",
    "candidateCount": 0,
    "curated": False,
}

MINIMAL_DOCUMENT = {
    "_id": "o0000099",
    "citationForm": "a",
    "homonym": "",
    "guideWord": "water",
    "pos": "N",
    "attingerPos": "",
    "language": "SUMERIAN",
    "uncertain": False,
    "head": None,
    "attestation": {},
    "sources": {"epsd2": {"oid": "o0000099", "headword": "a[water]N"}},
    "match": MINIMAL_MATCH,
    **{field: [] for field in LIST_FIELDS},
}


def _dump(schema: Schema, word: SumerianWord) -> Dict[str, object]:
    return cast(Dict[str, object], schema.dump(word))


def _load(schema: Schema, document: Mapping[str, object]) -> SumerianWord:
    return cast(SumerianWord, schema.load(document))


def test_complete_word_round_trips_on_the_wire() -> None:
    word = build_complete_word()
    schema = SumerianWordSchema()

    assert _load(schema, _dump(schema, word)) == word


def test_complete_word_round_trips_through_mongo_with_head_as_id() -> None:
    word = build_complete_word()
    schema = SumerianWordDocumentSchema()
    document = _dump(schema, word)

    assert document["head"] == "o0000001"
    assert _load(schema, document) == attr.evolve(word, head=WordLink("o0000001", ""))


def test_wire_head_is_a_link() -> None:
    dumped = _dump(SumerianWordSchema(), build_complete_word())

    assert dumped["head"] == {
        "id": "o0000001",
        "citationForm": "lu₂",
        "homonym": "I",
        "guideWord": "man",
    }


def test_document_without_optional_fields_loads_defaults() -> None:
    word = _load(SumerianWordDocumentSchema(), MINIMAL_DOCUMENT)

    assert word == SumerianWordFactory.build(
        id="o0000099",
        citation_form="a",
        lemma=(),
        homonym="",
        guide_word="water",
        attinger_pos="",
        sources=Sources(
            epsd2=Epsd2SourceFactory.build(
                oid="o0000099", headword="a[water]N", builds=()
            )
        ),
        match=Match("epsd2-only", "none", "a", 0, False),
        attestation=Attestation(),
    )


def test_minimal_word_dumps_empty_optionals() -> None:
    word = _load(SumerianWordDocumentSchema(), MINIMAL_DOCUMENT)
    dumped = _dump(SumerianWordSchema(), word)

    assert dumped["atf"] == ""
    assert dumped["truncated"] is False
    assert dumped["head"] is None
    assert dumped["sources"] == {
        "attinger": None,
        "epsd2": {"oid": "o0000099", "headword": "a[water]N", "builds": []},
    }


def test_unknown_fields_are_excluded_at_every_level() -> None:
    document = {
        **MINIMAL_DOCUMENT,
        "searchKeys": ["a"],
        "attestation": {"count": 2, "periods": [], "added": True},
        "match": {**MINIMAL_MATCH, "score": 1},
    }

    word = _load(SumerianWordDocumentSchema(), document)

    assert word.attestation == Attestation(2, ())
    assert word.match == Match("epsd2-only", "none", "a", 0, False)


@pytest.mark.parametrize(
    "field,value",
    [
        ("language", "AKKADIAN"),
        (
            "renderings",
            [
                {
                    "spelling": "a",
                    "source": "x",
                    "kind": "key",
                    "cuneiform": [],
                    "complete": True,
                }
            ],
        ),
        (
            "renderings",
            [
                {
                    "spelling": "a",
                    "source": "epsd2",
                    "kind": "x",
                    "cuneiform": [],
                    "complete": True,
                }
            ],
        ),
        ("crossReferences", [{"relation": "equals", "target": "a", "method": "m"}]),
        (
            "aliases",
            [
                {
                    "form": "a",
                    "relation": "compare",
                    "entryId": "e",
                    "method": "m",
                    "source": "attinger",
                }
            ],
        ),
        ("akkadianEquivalents", [{"wordId": "a I", "source": "attinger"}]),
        ("emesal", [{"form": "a", "source": "epsd2"}]),
        (
            "signs",
            [
                {
                    "reading": "a",
                    "name": "A",
                    "utf8": "",
                    "ambiguous": False,
                    "sources": [],
                    "signList": "x",
                }
            ],
        ),
        ("head", 7),
    ],
)
def test_values_outside_the_vocabulary_are_rejected(field: str, value: object) -> None:
    with pytest.raises(ValidationError):
        SumerianWordDocumentSchema().load({**MINIMAL_DOCUMENT, field: value})


@pytest.mark.parametrize("field", ["citationForm", "sources", "match", "renderings"])
def test_required_fields_are_enforced(field: str) -> None:
    document = {key: value for key, value in MINIMAL_DOCUMENT.items() if key != field}

    with pytest.raises(ValidationError):
        SumerianWordDocumentSchema().load(document)


def test_schema_without_a_model_refuses_to_load() -> None:
    class ModelLessSchema(AttrsSchema):
        pass

    with pytest.raises(NotImplementedError, match="The schema declares no model."):
        ModelLessSchema().load({})
