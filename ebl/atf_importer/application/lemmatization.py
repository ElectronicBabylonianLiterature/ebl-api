import attr
from typing import List, Dict, TypedDict, Union, Any, Optional, Callable
from ebl.atf_importer.application.atf_importer_config import AtfImporterConfigData
from ebl.atf_importer.application.logger import Logger
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
            oracc_lemmatization_token = self
            word_id = (
                self.get_word_id(oracc_lemmatization_token)
                if self.get_word_id
                else None
            )
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
        if not unique_lemmas:
            return self._enter_lemma_id_or_skip(lemmatization_token)
        return unique_lemmas[0] if len(unique_lemmas) > 0 else None

    def _enter_lemma_id_or_skip(
        self, lemmatization_token: OraccLemmatizationToken
    ) -> Optional[str]:
        print(
            "Annotate the following token:\n"
            f"Transliteration: '{lemmatization_token.transliteration}' lemma: '{lemmatization_token.lemma}'; "
            f"guide word: '{lemmatization_token.guideword}'; POS: '{lemmatization_token.pos}'\n"
            "Manually enter the eBL lemma id (e.g. 'bītu I') and press enter. To skip lemmatization, leave the field blank."
        )
        lemma_id = input().strip(" ")
        if not lemma_id:
            return None
        cursor = self.database.get_collection("words").aggregate(
            [{"$match": {"_id": lemma_id}}, {"$project": {"_id": 1}}]
        )
        if len(list(cursor)) > 0:
            self._log_lemma_entered_by_user(lemma_id)
            return lemma_id
        else:
            print(
                f"Lemma id '{lemma_id}' is not found in the eBL database. Please try again."
            )
            return self._enter_lemma_id_or_skip(lemmatization_token)

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
        glossary_lexemes = self.glossary.find(
            {
                "lemma": lemmatization_token.lemma,
                "guideword": lemmatization_token.guideword,
            }
        )
        if glossary_lexemes == []:
            self.logger.warning(
                "Incompatible lemmatization: No citation form"
                f" and guideword (by sense) found in the glossary for '{lemmatization_token.lemma}'",
                "lemmatization_log",
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
            args = {
                "lemma_field": lemma_field,
                "lemma_value": lemma_value,
                "guideword_field": guideword_field,
                "guideword_value": guideword,
            }
            unique_lemmas += self._query_database(args)
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
        cursor = self.database.get_collection("words").aggregate(
            [{"$match": query}, {"$project": {"_id": 1}}]
        )
        return [entry["_id"] for entry in cursor]

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
        if not unique_lemmas:
            self.logger.warning(
                "Incompatible lemmatization: No eBL word found for lemma"
                f" '{lemmatization_token.lemma}' and guideword '{lemmatization_token.guideword}'",
                "lemmatization_log",
            )

    def _log_lemma_entered_by_user(self, lemma_id: str) -> None:
        self.logger.info(
            f"Manual lemmatization: eBL lemma '{lemma_id}' entered by user",
            "lemmatization_log",
        )
