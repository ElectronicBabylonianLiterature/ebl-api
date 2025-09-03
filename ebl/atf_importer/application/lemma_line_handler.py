from typing import List, Dict, Any
from ebl.atf_importer.application.atf_importer_config import AtfImporterConfigData
from ebl.atf_importer.application.lemmatization import (
    LemmaLookup,
    OraccLemmatizationToken,
)
from ebl.atf_importer.application.logger import Logger
from collections import defaultdict
from ebl.transliteration.domain.text import TextLine
from ebl.transliteration.domain.word_tokens import Word
from ebl.transliteration.domain.tokens import Token
from ebl.transliteration.domain.enclosure_tokens import Removal
from ebl.transliteration.domain.sign_tokens import Reading, Logogram


class LemmaLineHandler:
    def __init__(
        self, database, config: AtfImporterConfigData, logger: Logger, glossary
    ):
        self.lemmatization = LemmaLookup(database, config, logger, glossary)
        self.logger = logger

    def apply_lemmatization(
        self,
        lemmatization_line: Dict[str, Any],
        result: defaultdict,
        filename: str,
        transliteration_line: TextLine,
    ) -> TextLine:
        oracc_lemmatization = self.parse_lemmatization_line(
            lemmatization_line, transliteration_line
        )
        ebl_lemmatization = tuple(
            token.lemmatization_token for token in oracc_lemmatization
        )
        return transliteration_line.update_lemmatization(ebl_lemmatization)

    def parse_lemmatization_line(
        self, lemmatization_line, transliteration_line: TextLine
    ) -> List[OraccLemmatizationToken]:
        oracc_lemmatization = []
        transliteration_tokens = self.get_transliteration_tokens(transliteration_line)
        # ToDo: Add length check here.
        # If length doesn't match, consider manual lemmatization? (new card)
        index_correction = 0
        for index, transliteration_token in enumerate(transliteration_tokens):
            token, index_correction = self.get_oracc_lemmatization_token(
                transliteration_token, lemmatization_line, index, index_correction
            )
            oracc_lemmatization.append(token)
        return oracc_lemmatization

    def get_oracc_lemmatization_token(
        self,
        transliteration_token,
        lemmatization_line,
        index,
        index_correction,
    ):
        transliteration = transliteration_token["value"]
        if transliteration_token["skip"]:
            index_correction += 1
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
                }
            )
        return transliteration_tokens

    def is_token_lemmatizable(
        self, token: Token, index: int, removals_map: dict[int, bool]
    ) -> bool:
        if not isinstance(token, Word) or not token.lemmatizable or removals_map[index]:
            return False
        return True

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
            for part_index, part in enumerate(parts):
                remove_token = removal_status
                change_within_token = False
                if isinstance(part, Removal):
                    removal_status = True if str(part.side) == "Side.LEFT" else False
                    if part_index > 0 and part_index + 1 < len(token.parts):
                        change_within_token = True
                    remove_token = False if change_within_token else True
            removals_map[token_index] = remove_token
        return removals_map

    def _log_transliteration_error(self, transliteration_line: str) -> None:
        # ToDo: Implement
        self.logger.error(
            "Transliteration and Lemmatization don't have equal length:"
            f"\n{str(transliteration_line)}",
            "error_lines",
        )
