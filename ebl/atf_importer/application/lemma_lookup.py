from typing import List, Dict


class LemmaLookup:
    def __init__(self, database, config, logger):
        self.database = database
        self.config = config
        self.logger = logger

    def lookup_lemma(self, lemma: str, guideword: str, pos_tag: str) -> List[Dict]:
        if lemma in ["X", "u", "n"]:
            return []

        lemma = lemma.strip()
        guideword = self._clean_guideword(guideword)

        if lemma.startswith("+"):
            unique_lemmas = self._lookup_prefixed_lemma(lemma[1:], guideword)
        else:
            unique_lemmas = self._lookup_standard_lemma(lemma, guideword, pos_tag)

        if not unique_lemmas and pos_tag in self.config.get("noun_pos_tags", []):
            unique_lemmas = self._query_database("oraccWords.lemma", lemma)

        if not unique_lemmas:
            self.logger.warning(
                f"""Incompatible lemmatization: No eBL word found for lemma
                 '{lemma}' and guide word '{guideword}'"""
            )

        return [{"_id": lemma_id} for lemma_id in unique_lemmas]

    def _clean_guideword(self, guideword: str) -> str:
        guideword = guideword.strip().strip("[]")
        return guideword.split("//")[0] if "//" in guideword else guideword

    def _lookup_prefixed_lemma(self, lemma: str, guideword: str) -> List[str]:
        lemma = lemma.replace("ʾ", "'")
        unique_lemmas = self._query_database(
            "oraccWords.lemma", lemma, "oraccWords.guideWord", guideword
        )

        if not unique_lemmas:
            unique_lemmas = self._query_multiple_sources(lemma, guideword)

        return unique_lemmas

    def _lookup_standard_lemma(
        self, lemma: str, guideword: str, pos_tag: str
    ) -> List[str]:
        try:
            citation_form, guideword = self.config["lemposgw_cfgw"][
                lemma + pos_tag + guideword
            ]
            guideword = guideword.split("//")[0] if "//" in guideword else guideword

            unique_lemmas = self._query_database(
                "oraccWords.lemma", citation_form, "oraccWords.guideWord", guideword
            )

            if not unique_lemmas:
                unique_lemmas = self._query_multiple_sources(citation_form, guideword)

        except KeyError:
            self.logger.warning(
                f"""Incompatible lemmatization: No citation form
                 or guideword found in the glossary for '{lemma}'"""
            )
            return []

        return unique_lemmas

    def _query_multiple_sources(self, lemma: str, guideword: str) -> List[str]:
        sources = ["forms.lemma", "lemma"]
        unique_lemmas = []
        for source in sources:
            unique_lemmas += self._query_database(
                source, [lemma], "guideWord", guideword
            )
        return unique_lemmas

    def _query_database(
        self,
        lemma_field: str,
        lemma_value,
        guideword_field: str = "",
        guideword_value: str = "",
    ) -> List[str]:
        query = {lemma_field: lemma_value}
        if guideword_field != "" and guideword_value != "":
            query[guideword_field] = guideword_value

        return [
            entry["_id"]
            for entry in self.database.get_collection("words").find(query, {"_id"})
        ]
