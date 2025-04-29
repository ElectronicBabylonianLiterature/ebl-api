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
from ebl.atf_importer.application.logger import Logger, LoggerUtil
from ebl.errors import DataError


class DatabaseImporter:
    def __init__(self, database, logger: Logger, username: str):
        self.database = database
        self.logger = logger
        self.user = AtfImporterUser(username)
        context = create_context()
        self.transliteration_factory: TransliterationUpdateFactory = (
            context.get_transliteration_update_factory()
        )
        self.updater: FragmentUpdater = context.get_fragment_updater()
        self.museum_number_getter = MuseumNumberGetter(database, logger)

    def import_into_database(self, ebl_lines: Dict[str, List], filename: str):
        museum_number: Optional[str] = self.museum_number_getter.get_museum_number(
            ebl_lines, filename
        )
        if not museum_number:
            self.logger.error(
                f"{filename} could not be imported: Museum number not found",
                "not_imported_files",
            )
            self.logger.info(
                LoggerUtil.print_frame(f'Conversion of "{filename}.atf" failed')
            )
            return
        self.logger.info(f"Museum number found: {museum_number}")
        if self._check_fragment_exists(museum_number):
            # ToDo: Ask user if to rewrite fragment
            pass
        else:
            self._import(ebl_lines, museum_number, filename)

    def _import(self, ebl_lines: Dict[str, List], museum_number: str, filename: str):
        try:
            self._insert_transliterations(
                ebl_lines["transliteration"],
                museum_number,
            )
            self._insert_lemmatization(ebl_lines["lemmatization"], museum_number)
            self.logger.success(
                f"{filename} successfully imported as {museum_number}", "imported_files"
            )
        except Exception as e:
            # ToDo: Clean up
            print(f"Error importing {filename}.atf: {str(e)}", "not_imported_files")
            input("import error")
            self.logger.error(
                f"Error importing {filename}.atf: {str(e)}", "not_imported_files"
            )

    def _check_fragment_exists(self, museum_number: str) -> bool:
        exists = list(
            self.database.get_collection("fragments").find(
                {"museumNumber": museum_number}, {"text.lines.0"}
            )
        )
        return bool(exists)

    def _insert_transliterations(
        self,
        text: Text,
        museum_number: str,
    ) -> None:
        # ToDo: Continue from here.
        # This has to be rewritten to accept the parsed and serialized (!) data.
        # converted_transliteration = "\n".join(text)
        print(text)
        input()
        transliteration = self.transliteration_factory.create_from_text(
            text  # converted_transliteration <-- Error here!
            # Text is in fact not deserialized lark output
        )
        self.updater.update_edition(
            parse_museum_number(museum_number),
            self.user,
            transliteration=transliteration,
        )

    def _insert_lemmatization(
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
        self.logger.error(f"Could not find a valid museum number in '{filename}'")
        return self._input_museum_number()

    def _get_valid_museum_number_or_none(
        self, museum_number_string: str
    ) -> Optional[str]:
        try:
            parse_museum_number(museum_number_string)
            self.logger.info(f"Museum number '{museum_number_string}' is valid")
            return museum_number_string
        except DataError:
            return

    def _get_museum_number_by_data(
        self, cdli_number: Optional[str], traditional_reference: Optional[str]
    ) -> Optional[str]:
        if cdli_number:
            museum_number = self._find_museum_number_by_cdli(cdli_number)
            if museum_number:
                return museum_number
        if traditional_reference:
            museum_number = self._find_museum_number_by_traditional_reference(
                traditional_reference
            )
            if museum_number:
                return museum_number
        self._log_no_museum_number_found(cdli_number)
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

    def _log_no_museum_number_found(self, cdli_number: Optional[str]) -> None:
        self.logger.warning(
            f"No museum number to CDLI number '{cdli_number}' found."
            " Trying to parse from the original file..."
        )
