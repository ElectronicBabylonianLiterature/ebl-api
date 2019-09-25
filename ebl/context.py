import attr
from falcon_auth.backends import AuthBackend

from ebl.bibliography.infrastructure.bibliography import MongoBibliography
from ebl.changelog import Changelog
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.dictionary.infrastructure.dictionary import MongoDictionary
from ebl.files.infrastructure.file_repository import GridFsFiles
from ebl.fragmentarium.application.fragment_repository import \
    FragmentRepository
from ebl.signs.application.sign_repository import SignRepository


@attr.s(auto_attribs=True, frozen=True)
class Context:
    auth_backend: AuthBackend
    dictionary: MongoDictionary
    sign_repository: SignRepository
    files: GridFsFiles
    fragment_repository: FragmentRepository
    changelog: Changelog
    bibliography: MongoBibliography
    text_repository: MongoTextRepository
