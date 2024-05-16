import json
import logging
from collections import defaultdict
from typing import Any, Dict, List, Tuple, Optional


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
from ebl.atf_importer.application.lemma_lookup import LemmaLookup


class LemmatizationError(Exception):
    pass


class AtfImporterConfig:
    def __init__(self, config_path: str):
        with open(config_path, "r") as file:
            self.config_data = json.load(file)

    def __getitem__(self, item: str) -> Any:
        return self.config_data.get(item)


class AtfImporterBase:
    def __init__(self, database):
        self.database = database
        self.username: str = ""
        self.logger = self.setup_logger()
        self.config = AtfImporterConfig("ebl/atf_importer/domain/atf_data.json")
        self._ebl_lines_getter = EblLinesGetter(self.database, self.config, self.logger)
        self._database_importer = DatabaseImporter(database, self.logger, self.username)

    def convert_to_ebl_lines(
        self, converted_lines: List[Dict[str, Any]], filename: str
    ) -> Dict[str, List]:
        return self._ebl_lines_getter.convert_to_ebl_lines(converted_lines, filename)

    def setup_logger(self) -> logging.Logger:
        logging.basicConfig(level=logging.DEBUG)
        return logging.getLogger("Atf-Importer")

    def import_into_database(self, ebl_lines: Dict[str, List], filename: str):
        self._database_importer.import_into_database(ebl_lines, filename)


class EblLinesGetter:
    def __init__(self, database, config, logger):
        self.logger = logger
        self._lemmalookup = LemmaLookup(database, config, logger)

    def convert_to_ebl_lines(
        self, converted_lines: List[Dict[str, Any]], filename: str
    ) -> Dict[str, List]:
        result = defaultdict(list)
        last_transliteration: Optional[str] = None

        for line in converted_lines:
            self._handle_line_type(line, result, filename, last_transliteration)

        return dict(result)

    def _handle_line_type(
        self,
        line: Dict[str, Any],
        result: defaultdict,
        filename: str,
        last_transliteration: Optional[str],
    ):
        c_type = line["c_type"]
        if c_type == "control_line":
            self._handle_control_line(line, result)
        elif c_type == "text_line":
            last_transliteration = self._handle_text_line(line, result)
        elif c_type == "lem_line":
            self._handle_lem_line(line, result, filename, last_transliteration)

    def _handle_control_line(self, line: Dict[str, Any], result: defaultdict):
        result["control_lines"].append(line)

    def _handle_text_line(self, line: Dict[str, Any], result: defaultdict) -> str:
        transliteration = line["c_line"]
        result["transliteration"].append(transliteration)
        return transliteration

    def _handle_lem_line(
        self,
        line: Dict[str, Any],
        result: defaultdict,
        filename: str,
        last_transliteration: Optional[str],
    ):
        if last_transliteration:
            lemmas = self._process_lemmatization(line["c_array"], filename)
            result["lemmatization"].append((last_transliteration, lemmas))
        else:
            self.logger.warning(
                f"Lemmatization line without preceding text line in {filename}"
            )

    def _process_lemmatization(
        self, lemma_tuples: List[Tuple[str, str, str]], filename: str
    ) -> List[Dict]:
        unique_lemmas = []
        for lemma, guideword, pos_tag in lemma_tuples:
            if db_entries := self._lookup_lemma(lemma, guideword, pos_tag):
                unique_lemmas.extend(db_entries)
            else:
                self.logger.warning(f"Lemma not found: {lemma} in {filename}")
        return unique_lemmas

    def _lookup_lemma(self, lemma: str, guideword: str, pos_tag: str):
        return self._lemmalookup.lookup_lemma(lemma, guideword, pos_tag)


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
            self.logger.info(f"{filename} successfully imported")
        except Exception as e:
            self.logger.error(f"Error importing {filename}: {str(e)}")

    def _retrieve_museum_number(
        self, ebl_lines: Dict[str, List], filename: str
    ) -> Optional[str]:
        for line in ebl_lines["control_lines"]:
            linesplit = line["c_line"].split("=")
            if len(linesplit) > 1:
                return linesplit[-1].strip()
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
        lemmatization_tokens = []
        for text_line, lemmas in lemmatizations:
            ebl_lines = parse_atf_lark(text_line).lines[0].content
            for token in ebl_lines:
                lemma_ids = [
                    lemma["_id"] for lemma in lemmas if lemma["lemma"] == token.value
                ]
                lemmatization_tokens.append(
                    LemmatizationToken(
                        token.value, tuple(lemma_ids) if lemma_ids else None
                    )
                )

        lemmatization = Lemmatization(tuple(lemmatization_tokens))
        self.updater.update_lemmatization(
            parse_museum_number(museum_number), lemmatization, self.user
        )
