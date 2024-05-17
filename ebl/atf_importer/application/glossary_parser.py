import re
from typing import Dict, List, Tuple, Optional, Iterator, TypedDict


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

    def parse(
        self,
        file: Iterator[str],
    ) -> GlossaryParserData:
        current_entry: Dict[str, str] = {}
        lemmas: List[str] = []

        for line in file:
            line = line.strip()
            if line.startswith("@entry"):
                current_entry = self._parse_entry(line)
                lemmas.clear()
            elif line.startswith("@form"):
                lemma = self._parse_form(line, current_entry)
                if lemma:
                    lemmas.append(lemma)
            elif line.startswith("@sense"):
                self._parse_sense(line, lemmas, current_entry)
        return self.data

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
        self,
        line: str,
        lemmas: List[str],
        current_entry: Dict[str, str],
    ):
        parts = line.split(" ", 2)
        pos_tag = parts[1] if len(parts) > 1 else None
        sense = parts[2].strip() if len(parts) > 2 else None

        for lemma in lemmas:
            sense_key = f"{lemma}{pos_tag}{sense}"
            if lemma not in self.forms_senses and sense:
                self.forms_senses[lemma] = [sense]
            elif sense:
                self.forms_senses[lemma].append(sense)
            if sense and "gw" in current_entry:
                self.lemposgw_cfgw[sense_key] = (
                    current_entry["cf"],
                    current_entry["gw"],
                )
