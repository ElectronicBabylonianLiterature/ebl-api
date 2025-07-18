import os
import re
from typing import Dict, List, Tuple, Optional, Iterator, TypedDict
from ebl.atf_importer.application.atf_importer_config import AtfImporterConfigData


class GlossaryParserData(TypedDict):
    lemma_guideword_pos__citationform: Dict[str, str]
    forms_senses: Dict[str, List[str]]
    lemma_pos_guideword__citationform_guideword: Dict[str, Tuple[str, str]]


class GlossaryParser:
    def __init__(self, config: AtfImporterConfigData):
        self.config = config
        self.lemma_guideword_pos__citationform: Dict[str, str] = {}
        self.forms_senses: Dict[str, List[str]] = {}
        self.lemma_pos_guideword__citationform_guideword: Dict[
            str, Tuple[str, str]
        ] = {}

    @property
    def data(self) -> GlossaryParserData:
        print(
            {
                "lemma_guideword_pos__citationform": self.lemma_guideword_pos__citationform,
                "forms_senses": self.forms_senses,
                "lemma_pos_guideword__citationform_guideword": self.lemma_pos_guideword__citationform_guideword,
            }
        )
        # ToDo: Clean up
        # print('glossary')
        # input()
        return {
            "lemma_guideword_pos__citationform": self.lemma_guideword_pos__citationform,
            "forms_senses": self.forms_senses,
            "lemma_pos_guideword__citationform_guideword": self.lemma_pos_guideword__citationform_guideword,
        }

    def parse_glossaries(
        self,
        directory_path: str,
    ) -> GlossaryParserData:
        for filename in os.listdir(directory_path):
            if filename.endswith(".glo"):
                file_path = os.path.join(directory_path, filename)
                with open(file_path, "r", encoding="utf8") as file:
                    self.parse(file)
        return self.data

    def parse(self, file: Iterator[str]) -> None:
        current_entry: Dict[str, str] = {}
        lemmas: List[str] = []
        for line in file:
            line = line.strip()
            if line.startswith("@entry"):
                lemmas, current_entry = self._handle_entry(line, lemmas)
            elif line.startswith("@form"):
                lemmas = self._handle_form(line, current_entry, lemmas)
            elif line.startswith("@sense"):
                self._handle_sense(line, lemmas, current_entry)

    def _handle_entry(
        self, line: str, lemmas: List[str]
    ) -> Tuple[List[str], Dict[str, str]]:
        lemmas.clear()
        return lemmas, self._parse_entry(line)

    def _handle_form(
        self, line: str, current_entry: Dict[str, str], lemmas: List[str]
    ) -> List[str]:
        lemma = self._parse_form(line, current_entry)
        if lemma:
            lemmas.append(lemma)
        return lemmas

    def _handle_sense(
        self, line: str, lemmas: List[str], current_entry: Dict[str, str]
    ) -> None:
        self._parse_sense(line, lemmas, current_entry)

    def _parse_entry(self, line: str) -> Dict[str, str]:
        entry = {}
        parts = line.split(" ", 2)
        if len(parts) > 1:
            entry["citationform"] = parts[1].replace("ʾ", "'").strip()
            description = parts[2] if len(parts) > 2 else ""
            if match := re.search(r"\[(.*?)\] (.*)", description):
                entry["guideword"], entry["pos"] = match.groups()
                entry["guideword"] = entry["guideword"].strip()
                entry["pos"] = entry["pos"].strip()
        return entry

    def _parse_form(self, line: str, current_entry: Dict[str, str]) -> Optional[str]:
        parts = line.split(" ")
        if len(parts) > 2:
            lemma = parts[2].lstrip("$").rstrip("\n")
            if (
                "citationform" in current_entry
                and "guideword" in current_entry
                and "pos" in current_entry
            ):
                key = f"{lemma}{current_entry['pos']}{current_entry['guideword']}"
                self.lemma_guideword_pos__citationform[key] = current_entry[
                    "citationform"
                ]
            return lemma
        return None

    def _parse_sense(
        self, line: str, lemmas: List[str], current_entry: Dict[str, str]
    ) -> None:
        pos_tag, sense = self._extract_pos_tag_and_sense(line)
        for lemma in lemmas:
            self._update_forms_senses(lemma, sense)
            self._update_lemma_pos_guideword__citationform_guideword(
                lemma, pos_tag, sense, current_entry
            )

    def _extract_pos_tag_and_sense(
        self, line: str
    ) -> Tuple[Optional[str], Optional[str]]:
        pos_tags = list(set(line.split(" ", 2)).intersection(self.config["POS_TAGS"]))
        pos_tag = pos_tags[0] if pos_tags[0] else ""
        sense = line.split(pos_tag)[1].strip(" \n")
        return pos_tag, sense

    def _update_forms_senses(self, lemma: str, sense: Optional[str]) -> None:
        if sense:
            if lemma not in self.forms_senses:
                self.forms_senses[lemma] = [sense]
            else:
                self.forms_senses[lemma].append(sense)

    def _update_lemma_pos_guideword__citationform_guideword(
        self,
        lemma: str,
        pos_tag: Optional[str],
        sense: Optional[str],
        current_entry: Dict[str, str],
    ) -> None:
        if sense and "guideword" in current_entry:
            sense_key = f"{lemma}{pos_tag}{sense}"
            self.lemma_pos_guideword__citationform_guideword[sense_key] = (
                current_entry["citationform"],
                current_entry["guideword"],
            )
