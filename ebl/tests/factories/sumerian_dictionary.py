from factory.declarations import LazyAttribute, Sequence
from factory.helpers import make_factory

from ebl.sumerian_dictionary.domain.sumerian_word import (
    AkkadianEquivalent,
    Attestation,
    AttingerForm,
    AttingerHeadword,
    AttingerSense,
    AttingerSource,
    Citation,
    EmesalForm,
    Epsd2Form,
    Epsd2Sense,
    Epsd2Source,
    Match,
    Rendering,
    SignEntry,
    SignSpelling,
    Sources,
    SumerianWord,
    UnrenderedToken,
)
from ebl.sumerian_dictionary.domain.sumerian_word_links import (
    Alias,
    CrossReference,
    WordLink,
)


AttingerSourceFactory = make_factory(
    AttingerSource,
    entry_id=Sequence(lambda n: f"att-{n:05d}"),
    node=Sequence(lambda n: f"node-{n}"),
    letter="L",
    depth=1,
    part_of_speech="N",
    headword=LazyAttribute(
        lambda _: AttingerHeadword("lugal", "lugal, ES u₃-mu-un", ((0, 5, "italic"),))
    ),
)

Epsd2SourceFactory = make_factory(
    Epsd2Source,
    oid=Sequence(lambda n: f"o{n:07d}"),
    headword="lugal[king]N",
    builds=("package",),
)

SumerianWordFactory = make_factory(
    SumerianWord,
    id=Sequence(lambda n: f"o{n:07d}"),
    citation_form=Sequence(lambda n: f"word{n}"),
    lemma=LazyAttribute(lambda word: tuple(word.citation_form.split(" "))),
    homonym="I",
    guide_word="word",
    pos="N",
    attinger_pos="N",
    language="SUMERIAN",
    uncertain=False,
    stems=(),
    determinatives=(),
    case_frame=(),
    emesal=(),
    attinger_senses=(),
    epsd2_senses=(),
    attinger_forms=(),
    epsd2_forms=(),
    signs=(),
    renderings=(),
    head=None,
    compounds=(),
    name_compounds=(),
    cross_references=(),
    aliases=(),
    akkadian_equivalents=(),
    citations=(),
    attestation=LazyAttribute(lambda _: Attestation()),
    sources=LazyAttribute(lambda _: Sources(attinger=AttingerSourceFactory.build())),
    match=LazyAttribute(
        lambda word: Match("attinger-only", "none", word.citation_form, 0, False)
    ),
)


def _complete_sign() -> SignEntry:
    return SignEntry(
        reading="lugal",
        name="LUGAL",
        utf8="𒈗",
        ambiguous=True,
        sources=(SignSpelling("attinger", "lugal"), SignSpelling("epsd2", "lugal")),
        sign_list="ogsl",
        character_list="ogsl",
        known_wrong_character=True,
        determinative=True,
        unresolved=True,
        form_of=("GAL",),
    )


def _partial_rendering() -> Rendering:
    return Rendering(
        spelling="lu₂-ga-al",
        source="attinger",
        kind="variant",
        cuneiform=("𒇽?",),
        complete=False,
        sign_lists=("ebl", "ogsl"),
        unrendered=(UnrenderedToken("ga", "noCharacter"),),
        printed="˹lu˺-ga-al",
        known_wrong_characters=("𒇽",),
    )


def build_complete_word() -> SumerianWord:
    return SumerianWordFactory.build(
        atf="lugal",
        truncated=True,
        uncertain=True,
        language="EMESAL",
        stems=("lugal",),
        determinatives=("lu₂",),
        case_frame=("-e",),
        emesal=(EmesalForm("u₃-mu-un", "attinger"),),
        attinger_senses=(AttingerSense("roi", "fr", "att-04420"),),
        epsd2_senses=(Epsd2Sense("1.", "king", "en"),),
        attinger_forms=(AttingerForm("lu-gal", True, "ELA 12"),),
        epsd2_forms=(Epsd2Form("lugal", 1200, 98.5),),
        signs=(_complete_sign(),),
        renderings=(_partial_rendering(),),
        head=WordLink("o0000001", "lu₂", "I", "man"),
        compounds=(WordLink("o0000002", "lugal-ĝu₁₀", "", ""),),
        name_compounds=(WordLink("o0000003", "Lugal-banda", "", ""),),
        cross_references=(
            CrossReference(
                "compare",
                "nin",
                "homonym",
                (WordLink("o0000004", "nin"),),
                (WordLink("o0000005", "Nin-lil₂"),),
                True,
            ),
        ),
        aliases=(
            Alias("{ĝeš}lugal", "equals", "att-1", "exact", "attinger", ("x",), True),
        ),
        akkadian_equivalents=(AkkadianEquivalent("šarru I", "borger", "L118"),),
        citations=(Citation("ELA", "12", "1.8.2.3", "c1823"),),
        attestation=Attestation(1200, ("Ur III", "Old Babylonian")),
        sources=Sources(AttingerSourceFactory.build(), Epsd2SourceFactory.build()),
        match=Match(
            "exact", "spelling", "lugal", 1, True, "o0032435", "ok", "held", ("x",)
        ),
    )
