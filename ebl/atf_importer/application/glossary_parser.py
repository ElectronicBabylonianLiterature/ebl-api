import re
from typing import Dict, List, Tuple, Optional, Iterator


class GlossaryParser:
    @staticmethod
    def parse(
        file: Iterator[str],
    ) -> Tuple[Dict[str, str], Dict[str, List[str]], Dict[str, Tuple[str, str]]]:
        lemgwpos_cf: Dict[str, str] = {}
        forms_senses: Dict[str, List[str]] = {}
        lemposgw_cfgw: Dict[str, Tuple[str, str]] = {}

        current_entry: Dict[str, str] = {}
        lemmas: List[str] = []

        for line in file:
            line = line.strip()
            if line.startswith("@entry"):
                current_entry = GlossaryParser.parse_entry(line)
                lemmas.clear()
            elif line.startswith("@form"):
                lemma = GlossaryParser.parse_form(line, current_entry, lemgwpos_cf)
                if lemma:
                    lemmas.append(lemma)
            elif line.startswith("@sense"):
                GlossaryParser.parse_sense(
                    line, lemmas, current_entry, forms_senses, lemposgw_cfgw
                )

        return lemgwpos_cf, forms_senses, lemposgw_cfgw

    @staticmethod
    def parse_entry(line: str) -> Dict[str, str]:
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

    @staticmethod
    def parse_form(
        line: str, current_entry: Dict[str, str], lemgwpos_cf: Dict[str, str]
    ) -> Optional[str]:
        parts = line.split(" ")
        if len(parts) > 2:
            lemma = parts[2].lstrip("$").rstrip("\n")
            if (
                "cf" in current_entry
                and "gw" in current_entry
                and "pos" in current_entry
            ):
                key = f"{lemma}{current_entry['pos']}{current_entry['gw']}"
                lemgwpos_cf[key] = current_entry["cf"]
            return lemma
        return None

    @staticmethod
    def parse_sense(
        line: str,
        lemmas: List[str],
        current_entry: Dict[str, str],
        forms_senses: Dict[str, List[str]],
        lemposgw_cfgw: Dict[str, Tuple[str, str]],
    ):
        parts = line.split(" ", 2)
        pos_tag = parts[1] if len(parts) > 1 else None
        sense = parts[2].strip() if len(parts) > 2 else None

        for lemma in lemmas:
            sense_key = f"{lemma}{pos_tag}{sense}"
            if lemma not in forms_senses and sense:
                forms_senses[lemma] = [sense]
            elif sense:
                forms_senses[lemma].append(sense)
            if sense and "gw" in current_entry:
                lemposgw_cfgw[sense_key] = (current_entry["cf"], current_entry["gw"])
        # ToDo:
        # Check if that's ok that this function does not return anything
