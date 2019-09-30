import attr
from falcon_auth.backends import AuthBackend

from ebl.bibliography.application.bibliography_repository import \
    BibliographyRepository
from ebl.changelog import Changelog
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.dictionary.application.word_repository import WordRepository
from ebl.files.application.file_repository import FileRepository
from ebl.fragmentarium.application.fragment_repository import \
    FragmentRepository
from ebl.signs.application.sign_repository import SignRepository


@attr.s(auto_attribs=True, frozen=True)
class Context:
    auth_backend: AuthBackend
    word_repository: WordRepository
    sign_repository: SignRepository
    file_repository: FileRepository
    photo_repository: FileRepository
    fragment_repository: FragmentRepository
    changelog: Changelog
    bibliography_repository: BibliographyRepository
    text_repository: MongoTextRepository
