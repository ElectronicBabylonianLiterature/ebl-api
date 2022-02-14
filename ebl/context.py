import attr
from falcon_auth.backends import AuthBackend
from falcon_caching import Cache

from ebl.bibliography.application.bibliography import Bibliography
from ebl.bibliography.application.bibliography_repository import BibliographyRepository
from ebl.changelog import Changelog
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.dictionary.application.word_repository import WordRepository
from ebl.ebl_ai_client import EblAiClient
from ebl.files.application.file_repository import FileRepository
from ebl.fragmentarium.application.annotations_repository import AnnotationsRepository
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.application.fragment_updater import FragmentUpdater
from ebl.fragmentarium.application.transliteration_update_factory import (
    TransliterationUpdateFactory,
)
from ebl.lemmatization.application.suggestion_finder import LemmaRepository
from ebl.transliteration.application.sign_repository import SignRepository
from ebl.transliteration.application.transliteration_query_factory import (
    TransliterationQueryFactory,
)


@attr.s(auto_attribs=True, frozen=True)
class Context:
    ebl_ai_client: EblAiClient
    auth_backend: AuthBackend
    word_repository: WordRepository
    sign_repository: SignRepository
    public_file_repository: FileRepository
    photo_repository: FileRepository
    folio_repository: FileRepository
    fragment_repository: FragmentRepository
    changelog: Changelog
    bibliography_repository: BibliographyRepository
    text_repository: MongoTextRepository
    annotations_repository: AnnotationsRepository
    lemma_repository: LemmaRepository
    cache: Cache

    def get_bibliography(self):
        return Bibliography(self.bibliography_repository, self.changelog)

    def get_fragment_updater(self):
        return FragmentUpdater(
            self.fragment_repository,
            self.changelog,
            self.get_bibliography(),
            self.photo_repository,
        )

    def get_transliteration_update_factory(self):
        return TransliterationUpdateFactory(self.sign_repository)

    def get_transliteration_query_factory(self):
        return TransliterationQueryFactory(self.sign_repository)
