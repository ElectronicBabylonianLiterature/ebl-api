import attr
from ebl.corpus.domain.uncertain_fragment_attestation import (
    UncertainFragmentAttestation,
)
from ebl.corpus.application.schemas import (
    UncertainFragmentAttestationSchema,
)
from ebl.tests.factories.corpus import (
    TextFactory,
    ChapterFactory,
    UncertainFragmentAttestationFactory,
)
from ebl.transliteration.domain.museum_number import MuseumNumber


def test_manuscript_attestation() -> None:
    TEXT = TextFactory.build()
    CHAPTER = ChapterFactory.build(
        text_id=TEXT.id, uncertain_fragments=(MuseumNumber.of("X.500"))
    )
    UNCERTAIN_FRAGMENT_ATTESTATION = UncertainFragmentAttestationFactory.build(
        text=attr.evolve(TEXT, references=()),
        chapter_id=CHAPTER.id_,
        museum_number=MuseumNumber.of("X.500"),
    )
    assert (
        UncertainFragmentAttestation(
            text=attr.evolve(TEXT, references=()),
            chapter_id=CHAPTER.id_,
            museum_number=MuseumNumber.of("X.500"),
        )
        == UNCERTAIN_FRAGMENT_ATTESTATION
    )
    assert (
        UncertainFragmentAttestationSchema().load(
            (UncertainFragmentAttestationSchema().dump(UNCERTAIN_FRAGMENT_ATTESTATION))
        )
        == UNCERTAIN_FRAGMENT_ATTESTATION
    )
