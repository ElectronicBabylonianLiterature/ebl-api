import attr
from typing import List, Dict, TypedDict, Union, Any, Optional, Callable
from ebl.atf_importer.application.atf_importer_config import AtfImporterConfigData
from ebl.atf_importer.application.logger import Logger
from collections import defaultdict
from ebl.transliteration.domain.text import TextLine
from ebl.transliteration.domain.word_tokens import Word
from ebl.transliteration.domain.tokens import Token
from ebl.transliteration.domain.enclosure_tokens import Removal
from ebl.lemmatization.domain.lemmatization import LemmatizationToken
from ebl.dictionary.domain.word import WordId
from ebl.atf_importer.application.glossary import Glossary


class QueryArgs(TypedDict, total=False):
    lemma_field: str
    lemma_value: Union[str, List[str]]
    guideword_field: str = ""
    guideword_value: str = ""


@attr.s(frozen=True, auto_attribs=True)
class OraccLemmatizationToken:
    transliteration: str
    get_word_id: Optional[Callable[["OraccLemmatizationToken"], Optional[str]]]
    lemma: str = ""
    guideword: str = ""
    pos: str = ""

    @property
    def lemmatizable(self) -> bool:
        if self.lemma in ["X", "u", "n", ""]:
            return False
        return True

    @property
    def lemmatization_token(self) -> LemmatizationToken:
        if self.lemmatizable and hasattr(self, "get_word_id"):
            word_id = self.get_word_id(self)
            if word_id is not None:
                return LemmatizationToken(self.transliteration, (WordId(word_id),))
        return LemmatizationToken(self.transliteration)


class LemmaLookup:
    def __init__(
        self,
        database,
        config: AtfImporterConfigData,
        logger: Logger,
        glossary: Glossary,
    ):
        self.database = database
        self.config = config
        self.logger = logger
        self.glossary = glossary

    def lookup_lemma(
        self, lemmatization_token: OraccLemmatizationToken
    ) -> Optional[str]:
        unique_lemmas = self._get_unique_lemmas(lemmatization_token)
        self._log_warning_if_no_lemmas(unique_lemmas, lemmatization_token)
        # ToDo: Possibly implement selection of options if more then 1, if found
        return unique_lemmas[0] if len(unique_lemmas) > 0 else None  # <- HERE

    def _get_unique_lemmas(
        self, lemmatization_token: OraccLemmatizationToken
    ) -> List[str]:
        unique_lemmas = self._lookup_standard_lemma(lemmatization_token)
        if (
            not unique_lemmas
            and lemmatization_token.pos in self.config["NOUN_POS_TAGS"]
        ):
            return self._query_database(
                {
                    "lemma_field": "oraccWords.lemma",
                    "lemma_value": lemmatization_token.lemma,
                }
            )
        return unique_lemmas

    def _lookup_standard_lemma(
        self, lemmatization_token: OraccLemmatizationToken
    ) -> List[str]:
        unique_lemmas = []
        glossary_lexemes = self.glossary.find({"lemma": lemmatization_token.lemma})
        if glossary_lexemes == []:
            self.logger.warning(
                "Incompatible lemmatization: No citation form"
                f" or guideword (by sense) found in the glossary for '{lemmatization_token.lemma}'",
                "not_lemmatized_tokens",
            )
            return []
        for lexeme in glossary_lexemes:
            unique_lemmas += self._query_sources(
                lemmatization_token.lemma, lexeme.guideword, lexeme.lemma
            )
        return unique_lemmas

    def _query_sources(
        self, lemma: str, guideword: str, citation_form: str
    ) -> List[str]:
        lemma_guideword_pairs = [
            ("forms.lemma", "guideWord", lemma),
            ("lemma", "guideWord", lemma),
            ("oraccWords.lemma", "oraccWords.guideWord", citation_form),
        ]
        unique_lemmas = []
        for lemma_field, guideword_field, lemma_value in lemma_guideword_pairs:
            unique_lemmas += self._query_database(
                {
                    "lemma_field": lemma_field,
                    "lemma_value": lemma_value,
                    "guideword_field": guideword_field,
                    "guideword_value": guideword,
                }
            )
        if unique_lemmas == []:
            for lemma_field, guideword_field, lemma_value in lemma_guideword_pairs:  # noqa: B007
                unique_lemmas += self._query_database(
                    {
                        "lemma_field": lemma_field,
                        "lemma_value": lemma_value,
                    }
                )
        return list(set(unique_lemmas))

    def _query_database(self, args: Dict[str, Any]) -> List[str]:
        query = {args["lemma_field"]: args["lemma_value"]}
        if self._has_guideword(args):
            query[args["guideword_field"]] = args["guideword_value"]
        return [
            entry["_id"]
            for entry in self.database.get_collection("words").aggregate(
                [{"$match": query}, {"$project": {"_id": 1}}]
            )
        ]

    def _has_guideword(self, args: Dict[str, Any]) -> bool:
        return (
            "guideword_field" in args
            and "guideword_value" in args
            and args["guideword_field"]
            and args["guideword_value"]
        )

    def _log_warning_if_no_lemmas(
        self, unique_lemmas: List[str], lemmatization_token: OraccLemmatizationToken
    ) -> None:
        # ToDo: Implement manual select of lemma by user
        if not unique_lemmas:
            self.logger.warning(
                "Incompatible lemmatization: No eBL word found for lemma"
                f" '{lemmatization_token.lemma}' and guideword '{lemmatization_token.guideword}'",
                "not_lemmatized_tokens",
            )


class LemmaLineHandler:
    def __init__(
        self, database, config: AtfImporterConfigData, logger: Logger, glossary
    ):
        self.lemma_lookup = LemmaLookup(database, config, logger, glossary)
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
    ) -> Dict[str, str]:
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
        skip = True if transliteration_token["skip"] else False
        if skip:
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
                get_word_id=self.lemma_lookup.lookup_lemma,
            ), index_correction

    def get_transliteration_tokens(self, transliteration_line: TextLine) -> List[Dict]:
        transliteration_tokens = []
        for token in transliteration_line._content:
            if self.is_token_lemmatizable(token):
                transliteration_tokens.append({"value": token.value, "skip": False})
            else:
                transliteration_tokens.append({"value": token.value, "skip": True})
        return transliteration_tokens

    def is_token_lemmatizable(self, token: Token) -> bool:
        if not isinstance(token, Word) or not token.lemmatizable:
            return False
        parts = token._parts
        if len(parts) >= 2 and (
            isinstance(parts[0], Removal) or isinstance(parts[-1], Removal)
        ):
            return False
        return True

        # ToDo: Adjust for cases when removal consists of more than 2 words.
        # <<a-a ba-ba>>

    def _log_transliteration_error(self, transliteration_line: str) -> None:
        # ToDo: Implement
        self.logger.error(
            "Transliteration and Lemmatization don't have equal length:"
            f"\n{str(transliteration_line)}",
            "error_lines",
        )
