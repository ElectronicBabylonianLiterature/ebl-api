import re
from typing import Dict, List, Sequence, Tuple, Optional, Iterator, TypedDict


class GlossaryParserData(TypedDict):
    lemgwpos_cf: Dict[str, str]
    forms_senses: Dict[str, List[str]]
    lemposgw_cfgw: Dict[str, Tuple[str, str]]


class GlossaryParser:
    def __init__(self):
        self.lemgwpos_cf: Dict[str, str] = {}
        self.forms_senses: Dict[str, List[str]] = {}
        self.lemposgw_cfgw: Dict[str, Tuple[str, str]] = {}

    @property
    def data(self) -> GlossaryParserData:
        return {
            "lemgwpos_cf": self.lemgwpos_cf,
            "forms_senses": self.forms_senses,
            "lemposgw_cfgw": self.lemposgw_cfgw,
        }

    def parse(self, file: Iterator[str]) -> GlossaryParserData:
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
        return self.data

    def _handle_entry(
        self, line: str, lemmas: List[str]
    ) -> List[List[str], Dict[str, str]]:
        lemmas.clear()
        return lemmas, self._parse_entry(line)

    def _handle_form(
        self, line: str, current_entry: Dict[str, str], lemmas: List[str]
    ) -> Sequence[str]:
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
            entry["cf"] = parts[1].replace("ʾ", "'").strip()
            description = parts[2] if len(parts) > 2 else ""
            match = re.search(r"\[(.*?)\] (.*)", description)
            if match:
                entry["gw"], entry["pos"] = match.groups()
                entry["gw"] = entry["gw"].strip()
                entry["pos"] = entry["pos"].strip()
        return entry

    def _parse_form(self, line: str, current_entry: Dict[str, str]) -> Optional[str]:
        parts = line.split(" ")
        if len(parts) > 2:
            lemma = parts[2].lstrip("$").rstrip("\n")
            if (
                "cf" in current_entry
                and "gw" in current_entry
                and "pos" in current_entry
            ):
                key = f"{lemma}{current_entry['pos']}{current_entry['gw']}"
                self.lemgwpos_cf[key] = current_entry["cf"]
            return lemma
        return None

    def _parse_sense(
        self, line: str, lemmas: List[str], current_entry: Dict[str, str]
    ) -> None:
        pos_tag, sense = self._extract_pos_tag_and_sense(line)
        for lemma in lemmas:
            self._update_forms_senses(lemma, sense)
            self._update_lemposgw_cfgw(lemma, pos_tag, sense, current_entry)

    def _extract_pos_tag_and_sense(
        self, line: str
    ) -> Tuple[Optional[str], Optional[str]]:
        parts = line.split(" ", 2)
        pos_tag = parts[1] if len(parts) > 1 else None
        sense = parts[2].strip() if len(parts) > 2 else None
        return pos_tag, sense

    def _update_forms_senses(self, lemma: str, sense: Optional[str]) -> None:
        if sense:
            if lemma not in self.forms_senses:
                self.forms_senses[lemma] = [sense]
            else:
                self.forms_senses[lemma].append(sense)

    def _update_lemposgw_cfgw(
        self,
        lemma: str,
        pos_tag: Optional[str],
        sense: Optional[str],
        current_entry: Dict[str, str],
    ) -> None:
        if sense and "gw" in current_entry:
            sense_key = f"{lemma}{pos_tag}{sense}"
            self.lemposgw_cfgw[sense_key] = (current_entry["cf"], current_entry["gw"])
