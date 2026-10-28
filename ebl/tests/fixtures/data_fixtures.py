import datetime
import json
from typing import List, Optional

import pytest
from dictdiffer import diff


from ebl.fragmentarium.domain.named_entity import EntityAnnotationSpan, NamedEntityType
from ebl.tests.factories.bibliography import BibliographyEntryFactory
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.at_line import ColumnAtLine, SurfaceAtLine, ObjectAtLine
from ebl.transliteration.domain.labels import ColumnLabel, SurfaceLabel, ObjectLabel
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.sign import (
    Sign,
    SignListRecord,
    SortKeys,
    Value,
    Logogram,
)
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.word_tokens import Word


@pytest.fixture
def text_with_labels():
    return Text.of_iterable(
        [
            TextLine.of_iterable(LineNumber(1), [Word.of([Reading.of_name("bu")])]),
            ColumnAtLine(ColumnLabel.from_int(1)),
            SurfaceAtLine(SurfaceLabel([], atf.Surface.SURFACE, "Stone wig")),
            ObjectAtLine(ObjectLabel([], atf.Object.OBJECT, "Stone wig")),
            TextLine.of_iterable(LineNumber(2), [Word.of([Reading.of_name("bu")])]),
        ]
    )


@pytest.fixture
def word():
    return {
        "lemma": ["part1", "Parṭ2"],
        "attested": True,
        "legacyLemma": "part1 part2",
        "homonym": "I",
        "_id": "part1 part2 I",
        "forms": [
            {"lemma": ["form1"], "notes": [], "attested": True},
            {"lemma": ["form2", "part2"], "notes": ["a note"], "attested": False},
        ],
        "meaning": "some semantics",
        "amplifiedMeanings": [
            {
                "meaning": "(*i/i*) meaning",
                "vowels": [{"value": ["i", "i"], "notes": []}],
                "key": "G",
                "entries": [],
            }
        ],
        "logograms": [],
        "derived": [[{"lemma": ["derived"], "homonym": "I", "notes": []}]],
        "derivedFrom": None,
        "source": "**part1 part2** source",
        "roots": ["wb'", "'b'", "plš"],
        "pos": ["V"],
        "namedEntityTags": [],
        "guideWord": "meaning",
        "arabicGuideWord": "meaning",
        "oraccWords": [{"lemma": "oracc lemma", "guideWord": "oracc meaning"}],
        "origin": ["CDA"],
        "akkadischeGlossareUndIndices": [
            {
                "mainWord": "word",
                "note": "a note",
                "reference": "reference",
                "AfO": "AfO",
                "agiID": "agiID",
            }
        ],
        "cdaAddenda": "additions",
        "supplementsAkkadianDictionaries": "new stuff",
    }


@pytest.fixture
def make_changelog_entry(user):
    def _make_changelog_entry(resource_type, resource_id, old, new):
        return {
            "user_profile": {
                key.replace(".", "_"): value for key, value in user.profile.items()
            },
            "resource_type": resource_type,
            "resource_id": resource_id,
            "date": datetime.datetime.utcnow().isoformat(),
            "diff": json.loads(json.dumps(list(diff(old, new)))),
        }

    return _make_changelog_entry


@pytest.fixture
def signs():
    return [
        Sign(
            name=name,
            lists=tuple(
                SignListRecord(list_name, number) for list_name, number in lists
            ),
            values=tuple(
                Value(value_name, sub_index) for value_name, sub_index in values
            ),
            logograms=tuple(
                Logogram(name, name, tuple(word_ids), name) for word_ids in logograms
            ),
            unicode=tuple(unicode),
            sort_keys=SortKeys(*sort_keys) if sort_keys else None,
        )
        for name, values, lists, logograms, unicode, sort_keys in [
            (
                "P₂",
                [(":", 1)],
                [("ABZ", "377n1")],
                [["lemmatu I"]],
                [74865],
                ([1, 2], [1, 2], [1, 2], [1, 2]),
            ),
            ("KU", [("ku", 1)], [("KWU", "869")], [], [74154], None),
            ("NU", [("nu", 1)], [("ABZ", "075")], [], [74337], None),
            (
                "IGI",
                [("ši", 1), ("igi", 1)],
                [("HZL", "288"), ("ABZ", "207a/207b X")],
                [],
                [74054],
                None,
            ),
            ("DIŠ", [("ana", 1), ("1", 1), ("diš", 1)], [], [], [73849], None),
            ("UD", [("ud", 1), ("u", 4), ("tu", 2)], [], [], [74515], None),
            ("MI", [("mi", 1), ("gi", 6)], [], [], [74282], None),
            ("KI", [("ki", 1)], [], [], [74144], None),
            ("DU", [("du", 1)], [], [], [73850], None),
            ("U", [("u", 1), ("10", 1)], [("ABZ", "411")], [], [74507], None),
            ("|U.U|", [("20", 1)], [("ABZ", "471")], [], [74649], None),
            ("BA", [("ba", 1), ("ku", 1)], [], [], [73792], None),
            ("MA", [("ma", 1)], [], [], [74272], None),
            ("TI", [("ti", 1)], [], [], [74494], None),
            ("MU", [("mu", 1)], [], [], [74284], None),
            ("TA", [("ta", 1)], [], [], [74475], None),
            ("ŠU", [("šu", 1)], [], [], [74455], None),
            ("BU", [("bu", 1), ("gid", 2)], [], [], [73805], None),
            ("|(4×ZA)×KUR|", [("geštae", 1)], [("ABZ", "531+588")], [], [74591], None),
            ("|(AŠ&AŠ@180)×U|", [], [], [], [74499], None),
            ("|A.EDIN.LAL|", [("ummu", 3)], [], [], [73728, 73876, 74226], None),
            ("|HU.HI|", [("mat", 3)], [("ABZ", "081")], [], [74039, 74029], None),
            ("AŠ", [("ana", 3)], [("ABZ", "001")], [], [73784], None),
            ("EDIN", [("bil", None), ("bir", 4)], [("ABZ", "168")], [], [73876], None),
            ("|ŠU₂.3×AN|", [("kunga", 1)], [], [], [74457], None),
            ("BUR₂", [("bul", 1)], [("ABZ", "11")], [], [74215], None),
            ("HU", [("u", 18)], [("ABZ", "78")], [], [74039], None),
            ("|URU×URUDA|", [("bansur", 1)], [("ABZ", "41")], [], [74574], None),
        ]
    ]


@pytest.fixture
def create_mongo_bibliography_entry():
    def _from_bibliography_entry(bibliography_entry: Optional[dict] = None) -> dict:
        entry: dict = bibliography_entry or BibliographyEntryFactory.build()
        return {"_id" if key == "id" else key: value for key, value in entry.items()}

    return _from_bibliography_entry


@pytest.fixture
def named_entity_spans() -> List[EntityAnnotationSpan]:
    return [
        EntityAnnotationSpan("Entity-1", NamedEntityType.PERSONAL_NAME, ["Word-2"]),
        EntityAnnotationSpan(
            "Entity-2", NamedEntityType.BUILDING_NAME, ["Word-2", "Word-3"]
        ),
        EntityAnnotationSpan(
            "Entity-3", NamedEntityType.YEAR_NAME, ["Word-7", "Word-14"]
        ),
    ]
