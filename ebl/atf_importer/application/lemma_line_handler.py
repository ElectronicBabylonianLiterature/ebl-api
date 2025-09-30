from typing import List, Tuple, Sequence, Dict, Optional, Any
from ebl.atf_importer.application.atf_importer_config import AtfImporterConfigData
from ebl.atf_importer.application.lemmatization import (
    LemmaLookup,
    OraccLemmatizationToken,
)
from ebl.atf_importer.application.logger import Logger
from ebl.transliteration.domain.text import TextLine
from ebl.transliteration.domain.word_tokens import Word
from ebl.transliteration.domain.tokens import Token
from ebl.transliteration.domain.enclosure_tokens import Removal
from ebl.transliteration.domain.sign_tokens import Reading, Logogram
from ebl.atf_importer.domain.legacy_atf_converter import LegacyAtfConverter
from ebl.atf_importer.application.glossary import Glossary


class LemmaLineHandler:
    def __init__(
        self,
        database,
        config: AtfImporterConfigData,
        logger: Logger,
        glossary: Glossary,
        atf_converter: LegacyAtfConverter,
    ):
        self.lemmatization = LemmaLookup(database, config, logger, glossary)
        self.logger = logger
        self.atf_converter = atf_converter

    def apply_lemmatization(
        self,
        lemmatization_line: Dict[str, Any],
        transliteration_line: TextLine,
        filename: str,
    ) -> TextLine:
        oracc_lemmatization = self.parse_lemmatization_line(
            lemmatization_line, transliteration_line
        )
        if oracc_lemmatization is None:
            self._log_lemmatization_length_error(
                transliteration_line, lemmatization_line, filename
            )
            return self.input_lemmatization_line(
                lemmatization_line, transliteration_line, filename
            )
        ebl_lemmatization = tuple(
            [token.lemmatization_token for token in oracc_lemmatization]
        )
        return transliteration_line.update_lemmatization(ebl_lemmatization)

    def input_lemmatization_line(
        self,
        lemmatization_line: Dict[str, Any],
        transliteration_line: TextLine,
        filename: str,
    ) -> TextLine:
        lemmatization_input = input(
            "Please enter the valid lemmatization or leave blank to skip lemmatization, then press enter:\n"
        )
        if lemmatization_input == "":
            return transliteration_line
        new_lemmatization_line = self.atf_converter.convert_lines_from_string(
            lemmatization_input
        )[0][0]
        return self.apply_lemmatization(
            new_lemmatization_line, transliteration_line, filename
        )

    def parse_lemmatization_line(
        self, lemmatization_line: Dict[str, Any], transliteration_line: TextLine
    ) -> Optional[List[OraccLemmatizationToken]]:
        oracc_lemmatization = []
        transliteration_tokens = self.get_transliteration_tokens(transliteration_line)
        if not self._is_lemmatizaton_length_match(
            transliteration_tokens, lemmatization_line
        ):
            return None
        index_correction = 0
        for index, transliteration_token in enumerate(transliteration_tokens):
            token, index_correction = self.get_oracc_lemmatization_token(
                transliteration_token, lemmatization_line, index, index_correction
            )
            oracc_lemmatization.append(token)
        return oracc_lemmatization

    def get_oracc_lemmatization_token(
        self,
        transliteration_token: Dict,
        lemmatization_line: Dict[str, Any],
        index: int,
        index_correction: int,
    ):
        transliteration = transliteration_token["value"]
        if transliteration_token["skip"]:
            index_correction += 1 if transliteration_token["adjust_index"] else 0
            return OraccLemmatizationToken(
                transliteration=transliteration, get_word_id=None
            ), index_correction
        else:
            oracc_lemma_tuple = lemmatization_line["c_array"][index - index_correction][
                0
            ]
            guideword = oracc_lemma_tuple[1].strip().strip("[]")
            guideword = guideword.split("//")[0] if "//" in guideword else guideword
            return OraccLemmatizationToken(
                lemma=oracc_lemma_tuple[0].strip("+"),
                guideword=guideword,
                pos=oracc_lemma_tuple[2],
                transliteration=transliteration,
                get_word_id=self.lemmatization.lookup_lemma,
            ), index_correction

    def get_transliteration_tokens(self, transliteration_line: TextLine) -> List[Dict]:
        transliteration_tokens = []
        removals_map = self._map_removals(transliteration_line)
        for index, token in enumerate(transliteration_line._content):
            transliteration_tokens.append(
                {
                    "value": token.value,
                    "skip": not self.is_token_lemmatizable(token, index, removals_map),
                    "adjust_index": self.is_adjust_index(token, index, removals_map),
                }
            )
        return transliteration_tokens

    def is_token_lemmatizable(
        self, token: Token, index: int, removals_map: dict[int, bool]
    ) -> bool:
        if not isinstance(token, Word) or not token.lemmatizable or removals_map[index]:
            return False
        return True

    def is_adjust_index(
        self, token: Token, index: int, removals_map: dict[int, bool]
    ) -> bool:
        if removals_map[index]:
            return True
        return False

    def _map_removals(self, transliteration_line: TextLine) -> dict[int, bool]:
        removal_status = remove_token = False
        removals_map = {}
        for token_index, token in enumerate(transliteration_line.content):
            parts = [
                part
                for part in token.parts
                if isinstance(part, Removal)
                or isinstance(part, Reading)
                or isinstance(part, Logogram)
            ]
            remove_token, removal_status = self._is_remove_token(
                token, parts, remove_token, removal_status
            )
            removals_map[token_index] = remove_token
        return removals_map

    def _is_remove_token(
        self,
        token: Token,
        parts: Sequence[Token],
        remove_token: bool,
        removal_status: bool,
    ) -> Tuple[bool, bool]:
        for part_index, part in enumerate(parts):
            remove_token = removal_status
            change_within_token = False
            if isinstance(part, Removal):
                removal_status = True if str(part.side) == "Side.LEFT" else False
                if part_index > 0 and part_index + 1 < len(token.parts):
                    change_within_token = True
                remove_token = False if change_within_token else True
        return remove_token, removal_status

    def _is_lemmatizaton_length_match(
        self, transliteration_tokens: List[Dict], lemmatization_line: Dict
    ) -> bool:
        if len(
            [token for token in transliteration_tokens if not token["adjust_index"]]
        ) == len(lemmatization_line["c_array"]):
            return True
        return False

    def _log_lemmatization_length_error(
        self,
        transliteration_line: TextLine,
        lemmatization_line: Dict[str, Any],
        filename: str,
    ) -> None:
        error_message = (
            f"In `{filename}.atf`: The lemmatization of the following line:\n"
            f"{transliteration_line.atf}\n"
            "does not match its length. Lemmatization:\n"
            f"{lemmatization_line['c_line']}"
        )
        print(error_message)
        self.logger.warning(error_message, "lemmatization_log")
