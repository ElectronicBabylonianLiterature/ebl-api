from typing import Dict, List, Tuple, Optional, Sequence
from ebl.app import create_context
from ebl.fragmentarium.application.fragment_updater import FragmentUpdater
from ebl.fragmentarium.application.transliteration_update_factory import (
    TransliterationUpdateFactory,
)
from ebl.fragmentarium.web.dtos import parse_museum_number
from ebl.lemmatization.domain.lemmatization import Lemmatization, LemmatizationToken
from ebl.transliteration.domain.atf import Atf
from ebl.transliteration.domain.lark_parser import parse_atf_lark
from ebl.users.domain.user import AtfImporterUser
from ebl.atf_importer.domain.atf_preprocessor_util import Util


class DatabaseImporter:
    def __init__(self, database, logger, username: str):
        self.database = database
        self.logger = logger
        self.user = AtfImporterUser(username)
        context = create_context()
        self.transliteration_factory: TransliterationUpdateFactory = (
            context.get_transliteration_update_factory()
        )
        self.updater: FragmentUpdater = context.get_fragment_updater()

    def import_into_database(self, ebl_lines: Dict[str, List], filename: str):
        museum_number: Optional[str] = self._retrieve_museum_number(ebl_lines, filename)
        if not museum_number:
            self.logger.error(
                f"{filename} could not be imported: Museum number not found",
                "not_imported_files",
            )
            self.logger.info(Util.print_frame(f'Conversion of "{filename}.atf" failed'))
            return
        if self._check_fragment_exists(museum_number):
            self._import(ebl_lines, museum_number, filename)

    def _import(self, ebl_lines: Dict[str, List], museum_number: str, filename: str):
        try:
            self._insert_transliterations(
                ebl_lines["transliteration"],
                museum_number,
            )
            self._insert_lemmatization(ebl_lines["lemmatization"], museum_number)
            self.logger(f"{filename} successfully imported", "imported_files")
        except Exception as e:
            self.logger.error(
                f"Error importing {filename}: {str(e)}", "not_imported_files"
            )

    def _get_valid_museum_number_or_none(
        self, museum_number_string: str
    ) -> Optional[str]:
        try:
            parse_museum_number(museum_number_string)
            self.logger.info(f"Museum number '{museum_number_string}' is valid")
            return museum_number_string
        except ValueError:
            return

    def _retrieve_museum_number(
        self, ebl_lines: Dict[str, List], filename: str
    ) -> Optional[str]:
        if museum_number := self._get_museum_number_by_cdli_number(
            ebl_lines["control_lines"]
        ):
            return museum_number
        for line in ebl_lines["control_lines"]:
            linesplit = line["c_line"].split("=")
            if len(linesplit) > 1 and (
                museum_number := self._get_valid_museum_number_or_none(
                    linesplit[-1].strip()
                )
            ):
                return museum_number
        self.logger.error(f"Could not find a valid museum number in '{filename}'")
        return self._input_museum_number(filename)

    def _input_museum_number(
        self, filename: str, museum_number: Optional[str] = None
    ) -> Optional[str]:
        while museum_number is None:
            museum_number_input = input(
                "Please enter a valid museum number (enter 'skip' to skip this file): "
            )
            if museum_number_input.lower() == "skip":
                return None
            museum_number = self._get_valid_museum_number_or_none(museum_number_input)
        return museum_number

    def _get_museum_number_by_cdli_number(self, control_lines) -> Optional[str]:
        cdli_number = self._get_cdli_number(control_lines)
        if cdli_number:
            museum_number = self._find_museum_number_by_cdli(cdli_number)
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

    def _log_no_museum_number_found(self, cdli_number: Optional[str]) -> None:
        self.logger.warning(
            f"No museum number to CDLI number '{cdli_number}' found."
            " Trying to parse from the original file..."
        )

    @staticmethod
    def _get_cdli_number(control_lines) -> Optional[str]:
        for line in control_lines:
            cdli_number = line["c_line"].split("=")[0].strip().replace("&", "")
            return cdli_number
        return None

    def _check_fragment_exists(self, museum_number: str) -> bool:
        exists = list(
            self.database.get_collection("fragments").find(
                {"museumNumber": museum_number}, {"text.lines.0"}
            )
        )
        return bool(exists)

    def _insert_transliterations(
        self,
        transliterations: List[str],
        museum_number: str,
    ) -> None:
        converted_transliteration = "\n".join(transliterations)
        transliteration = self.transliteration_factory.create(
            Atf(converted_transliteration)
        )
        self.updater.update_transliteration(
            parse_museum_number(museum_number), transliteration, self.user
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
