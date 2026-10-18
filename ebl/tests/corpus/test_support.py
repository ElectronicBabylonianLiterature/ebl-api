from ebl.tests.corpus.support import allow_references, allow_signs
from ebl.tests.factories.corpus import ChapterFactory, ManuscriptFactory
from ebl.transliteration.domain.sign import Sign, SignName


def test_allow_references(bibliography) -> None:
    manuscript = ManuscriptFactory.build(with_old_sigla=True)
    chapter = ChapterFactory.build(manuscripts=(manuscript,), lines=())
    documents = [
        *(reference.document for reference in manuscript.references),
        *(old_siglum.reference.document for old_siglum in manuscript.old_sigla),
    ]

    allow_references(chapter, bibliography)

    assert documents
    assert [bibliography.find(document["id"]) for document in documents] == documents


def test_allow_signs(sign_repository) -> None:
    signs = [Sign(SignName("IGI")), Sign(SignName("KUR"))]

    allow_signs(signs, sign_repository)

    assert [sign_repository.find(sign.name) for sign in signs] == signs
