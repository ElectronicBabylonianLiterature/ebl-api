import attr
from ebl.corpus.domain.manuscript_attestation import ManuscriptAttestation
from ebl.tests.factories.corpus import (
    TextFactory,
    ChapterFactory,
    ManuscriptAttestationFactory,
)


def test_manuscript_attestation() -> None:
    TEXT = TextFactory.build()
    CHAPTER = ChapterFactory.build(text_id=TEXT.id)
    MANUSCRIPT_ATTESTATION = ManuscriptAttestationFactory.build(
        text=attr.evolve(TEXT, references=()),
        chapter_id=CHAPTER.id_,
        manuscript=CHAPTER.manuscripts[0],
    )
    assert (
        ManuscriptAttestation(
            attr.evolve(TEXT, references=()), CHAPTER.id_, CHAPTER.manuscripts[0]
        )
        == MANUSCRIPT_ATTESTATION
    )
