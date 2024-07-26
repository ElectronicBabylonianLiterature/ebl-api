import falcon

from ebl.corpus.application.schemas import ManuscriptAttestationSchema
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.tests.factories.fragment import FragmentFactory
from ebl.tests.factories.corpus import (
    TextFactory,
    ChapterFactory,
    ManuscriptFactory,
    ManuscriptAttestationFactory,
)

MUSEUM_NUMBER = MuseumNumber("X", "1")
FRAGMENT = FragmentFactory.build(number=MUSEUM_NUMBER)
TEXT = TextFactory.build()
CHAPTER = ChapterFactory.build(
    text_id=TEXT.id,
    stage=TEXT.chapters[0].stage,
    name=TEXT.chapters[0].name,
    manuscripts=(
        ManuscriptFactory.build(
            id=1,
            museum_number=MUSEUM_NUMBER,
            accession="",
            references=(),
        ),
    ),
)

MANUSCRIPT_ATTESTATION = ManuscriptAttestationFactory.build(
    text=TEXT,
    chapter_id=CHAPTER.id_,
    manuscript=CHAPTER.manuscripts[0],
)


def test_search_fragment_attestations_in_corpus(client, fragmentarium, text_repository):
    fragmentarium.create(FRAGMENT)
    text_repository.create(TEXT)
    text_repository.create_chapter(CHAPTER)
    result = client.simulate_get("/fragments/X.1/corpus")
    assert result.status == falcon.HTTP_OK
    assert result.headers["Content-Type"] == "application/json"
    assert result.json == [ManuscriptAttestationSchema().dump(MANUSCRIPT_ATTESTATION)]
