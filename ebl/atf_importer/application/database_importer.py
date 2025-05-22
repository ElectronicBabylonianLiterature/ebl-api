from typing import Dict, List, Tuple, Optional, Sequence
from ebl.app import create_context
from ebl.fragmentarium.application.fragment_updater import FragmentUpdater
from ebl.fragmentarium.application.transliteration_update_factory import (
    TransliterationUpdateFactory,
)
from ebl.fragmentarium.web.dtos import parse_museum_number
from ebl.lemmatization.domain.lemmatization import Lemmatization, LemmatizationToken
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.atf_parsers.lark_parser import parse_atf_lark
from ebl.users.domain.user import AtfImporterUser
from ebl.atf_importer.application.logger import Logger
from ebl.errors import DataError
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.errors import NotFoundError


class DatabaseImporter:
    def __init__(
        self,
        database,
        fragment_repository: FragmentRepository,
        logger: Logger,
        username: str,
    ):
        self.database = database
        self.logger = logger
        self.user = AtfImporterUser(username)
        context = create_context()
        self.fragment_repository = fragment_repository
        self.transliteration_factory: TransliterationUpdateFactory = (
            context.get_transliteration_update_factory()
        )
        self.updater: FragmentUpdater = context.get_fragment_updater()
        self.museum_number_getter = MuseumNumberGetter(database, logger)
        self.lemmatization_getter = LemmatizationGetter(self.updater, self.user)

    def import_into_database(
        self, ebl_lines: Dict[str, List], text: Text, filename: str
    ):
        museum_number: Optional[str] = self.museum_number_getter.get_museum_number(
            ebl_lines, filename
        )
        if not museum_number:
            self.logger.error(
                f"{filename}.atf could not be imported: Museum number not found",
                "not_imported_files",
            )
            return
        return self.check_and_import(ebl_lines, text, museum_number, filename)

    def check_and_import(
        self, ebl_lines: Dict[str, List], text: Text, museum_number: str, filename: str
    ) -> None:
        self.logger.info(f"Museum number found: {museum_number}")
        fragment_exists, edition_exists = self._check_fragment_and_edition_exist(
            museum_number
        )
        if fragment_exists is False:
            self.logger.error(
                f"{filename}.atf could not be imported: Museum number not in the database.\n"
                f"Please create a fragment with museum number {museum_number} and try again",
                "not_imported_files",
            )
            return
        if edition_exists:
            if self._edition_overwrite_consent(museum_number) is False:
                self.logger.info(
                    f"{filename}.atf could not be imported: Edition found, importing cancelled by user",
                    "not_imported_files",
                )
                return
            self.logger.info(f"Overwriting edition for {museum_number}")
        self._import(ebl_lines, text, museum_number, filename)

    def _edition_overwrite_consent(self, museum_number: str) -> bool:
        answers_dict = {"Y": True, "N": False}
        answer = input(
            f"Fragment {museum_number} already has an edition. Should it be overwritten?\n "
            "Answer with 'Y'(es) / 'N'(o), then press Enter.\n"
        )
        if answer in answers_dict.keys():
            return answers_dict[answer]
        else:
            print(f"'{answer}' is an invalid answer. Please choose 'Y' or 'N'")
            return self._overwrite_edition(museum_number)

    def _import(
        self, ebl_lines: Dict[str, List], text: Text, museum_number: str, filename: str
    ):
        # try:
        self._insert_transliterations(
            text,
            museum_number,
        )
        # ToDo: IMPORTANT! Fix lemmatization!
        # self.lemmatization_getter.insert_lemmatization(ebl_lines["lemmatization"], museum_number)
        self.logger.info(
            f"{filename}.atf successfully imported as {museum_number}", "imported_files"
        )
        # except Exception as e:
        #    self.logger.error(
        #        f"Error importing {filename}.atf: {str(e)}", "not_imported_files"
        #    )

    def _check_fragment_and_edition_exist(
        self, museum_number: str
    ) -> tuple[bool, bool]:
        try:
            result = self.fragment_repository.query_by_museum_number(
                MuseumNumber.of(museum_number)
            )
            # result = self.database.get_collection("fragments").find_one(
            #    {"museumNumber": museum_number}
            # )
            # , {"_id": 0, "text.lines.0": 1}
        except NotFoundError:
            return False, False
        has_edition = bool(
            result.text.lines
        )
        return True, has_edition

    def _insert_transliterations(
        self,
        text: Text,
        museum_number: str,
    ) -> None:
        transliteration = self.transliteration_factory.create_from_text(text)
        self.updater.update_edition(
            parse_museum_number(museum_number),
            self.user,
            transliteration=transliteration,
        )


class MuseumNumberGetter:
    def __init__(self, database, logger: Logger):
        self.logger = logger
        self.database = database

    def get_museum_number(
        self, ebl_lines: Dict[str, List], filename: str
    ) -> Optional[str]:
        cdli_number, reference = self._get_cdli_number_and_reference(
            ebl_lines["control_lines"]
        )
        if reference is not None:
            if museum_number := self._get_valid_museum_number_or_none(reference):
                return museum_number
            if museum_number := self._get_museum_number_by_data(cdli_number, reference):
                return museum_number
        self.logger.error(f"Could not find a valid museum number for '{filename}'")
        return self._input_museum_number()

    def _get_valid_museum_number_or_none(
        self, museum_number_string: str
    ) -> Optional[str]:
        try:
            parse_museum_number(museum_number_string)
            self.logger.info(f"Museum number '{museum_number_string}' is valid")
            return museum_number_string
        except DataError:
            return None

    def _get_museum_number_by_data(
        self, cdli_number: Optional[str], traditional_reference: Optional[str]
    ) -> Optional[str]:
        if cdli_number:
            if museum_number := self._find_museum_number_by_cdli(cdli_number):
                return museum_number
        if traditional_reference:
            if museum_number := self._find_museum_number_by_traditional_reference(
                traditional_reference
            ):
                return museum_number
        return None

    def _find_museum_number_by_cdli(self, cdli_number: str) -> Optional[str]:
        for entry in self.database.get_collection("fragments").find(
            {"externalNumbers.cdliNumber": cdli_number}, {"museumNumber"}
        ):
            if "_id" in entry:
                return entry["_id"]
        return None

    def _find_museum_number_by_traditional_reference(
        self, reference: str
    ) -> Optional[str]:
        for entry in self.database.get_collection("fragments").find(
            {"traditionalReferences": {"$in": [reference]}},
            {"museumNumber"},
        ):
            if "_id" in entry:
                return entry["_id"]
        return None

    @staticmethod
    def _get_cdli_number_and_reference(control_lines) -> Sequence[Optional[str]]:
        for line in control_lines:
            if "=" in str(line["serialized"].content):
                cdli_number, reference = (
                    element.strip()
                    for element in str(line["serialized"].content).split("=")
                )
                return cdli_number, reference
        return None, None

    def _input_museum_number(self) -> Optional[str]:
        museum_number = None
        while museum_number is None:
            museum_number_input = input(
                "Please enter a valid museum number (enter 'skip' to skip this file): "
            )
            if museum_number_input.lower() == "skip":
                return None
            museum_number = self._get_valid_museum_number_or_none(museum_number_input)
        return museum_number


class LemmatizationGetter:
    # ToDo: Move to legacy lemmatization, if possible
    def __init__(self, updater: FragmentUpdater, user: AtfImporterUser) -> None:
        self.updater: updater
        self.user = user

    def insert_lemmatization(
        self,
        lemmatizations: List[Tuple[str, List[Dict]]],
        museum_number: str,
    ):
        lemmatization_tokens = self._get_lemmatization_tokens(lemmatizations)
        lemmatization = Lemmatization([lemmatization_tokens])
        self.updater.update_lemmatization(
            parse_museum_number(museum_number), lemmatization, self.user
        )

    def _get_lemmatization_tokens(
        self, lemmatizations: List[Tuple[str, List[Dict]]]
    ) -> Sequence[LemmatizationToken]:
        lemmatization_tokens: List[LemmatizationToken] = []
        for text_line, lemmas in lemmatizations:
            ebl_lines = parse_atf_lark(text_line).lines[0].content
            lemmatization_tokens = self._get_lemmatization_tokens_in_lines(
                ebl_lines, lemmas, lemmatization_tokens
            )
        return lemmatization_tokens

    def _get_lemmatization_tokens_in_lines(
        self,
        ebl_lines,
        lemmas,
        lemmatization_tokens: List[LemmatizationToken],
    ) -> List[LemmatizationToken]:
        for token in ebl_lines:
            lemma_ids = [
                lemma["_id"] for lemma in lemmas if lemma["lemma"] == token.value
            ]
            lemmatization_tokens.append(
                LemmatizationToken(token.value, tuple(lemma_ids) if lemma_ids else None)
            )
        return lemmatization_tokens
