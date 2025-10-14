import os
import re
import attr
from typing import List, TypedDict, Optional


@attr.s(frozen=True, auto_attribs=True)
class FormEntry:
    transliteration: str
    transcription: str


@attr.s(frozen=True, auto_attribs=True)
class SenseEntry:
    guideword: str
    pos: str


@attr.s(frozen=True, auto_attribs=True)
class LexicalEntry:
    lemma: str
    guideword: str
    pos: str
    forms: List[FormEntry]
    senses: List[SenseEntry]


class GlossaryQuery(TypedDict, total=False):
    lemma: Optional[str]
    guideword: Optional[str]
    pos: Optional[str]
    transliteration: Optional[str]
    transcription: Optional[str]


@attr.s(frozen=True, auto_attribs=True)
class Glossary:
    entries: List[LexicalEntry]

    def find(self, query: GlossaryQuery) -> List[LexicalEntry]:
        return [entry for entry in self.entries if self._entry_matches(entry, query)]

    def _entry_matches(self, entry: LexicalEntry, query: GlossaryQuery) -> bool:
        return all(
            [
                self._match_lemma(entry, query),
                self._match_guideword(entry, query),
                self._match_pos(entry, query),
            ]
        )

    def _match_lemma(self, entry: LexicalEntry, query: GlossaryQuery) -> bool:
        return "lemma" in query and (
            query["lemma"] == entry.lemma
            or any(query["lemma"] == form.transcription for form in entry.forms)
        )

    def _match_guideword(self, entry: LexicalEntry, query: GlossaryQuery) -> bool:
        if "guideword" not in query:
            return True
        guideword = re.sub(r"[()]", "", query["guideword"])
        return guideword == entry.guideword or any(
            sense.guideword == guideword for sense in entry.senses
        )

    def _match_pos(self, entry: LexicalEntry, query: GlossaryQuery) -> bool:
        if "pos" not in query:
            return True
        return query["pos"] == entry.pos or any(
            sense.pos == query["pos"] for sense in entry.senses
        )


class GlossaryParser:
    def __init__(self):
        self.entries = []
        self.text = ""

    @property
    def glossary(self) -> Glossary:
        return Glossary(entries=self.entries)

    def load_glossaries(
        self,
        directory_path: str,
    ) -> Glossary:
        for filename in os.listdir(directory_path):
            if filename.endswith(".glo"):
                file_path = os.path.join(directory_path, filename)
                with open(file_path, "r", encoding="utf8") as file:
                    self.parse(file.read())
        return self.glossary

    def parse(self, text: str) -> None:
        blocks = self._extract_entry_blocks(text)
        for block in blocks:
            entry = self._parse_entry_block(block)
            if entry:
                self.entries.append(entry)

    def _extract_entry_blocks(self, text: str) -> List:
        return re.findall(r"@entry\s.*?@end entry", text, flags=re.DOTALL)

    def _parse_entry_block(self, block):
        header = self._parse_entry_header(block)
        if not header:
            return None
        forms = self._parse_forms(block)
        senses = self._parse_senses(block)
        return LexicalEntry(
            lemma=header["lemma"],
            guideword=header["guideword"],
            pos=header["pos"],
            forms=forms,
            senses=senses,
        )

    def _parse_entry_header(self, block):
        match = re.search(r"@entry\s+(\S+)\s+\[([^\]]+)\]\s+(\w+)", block)
        if match:
            return {
                "lemma": match.group(1),
                "guideword": match.group(2),
                "pos": match.group(3),
            }
        return None

    def _parse_forms(self, block):
        forms = []
        for match in re.finditer(r"@form\s+(.+?)\s+\$(\S+)", block):
            form = FormEntry(
                transliteration=match.group(1).strip(),
                transcription=match.group(2).strip(),
            )
            forms.append(form)
        return forms

    def _parse_senses(self, block):
        senses = []
        for match in re.finditer(r"@sense\s+(\w+)\s+(.+)", block):
            sense = SenseEntry(
                pos=match.group(1).strip(), guideword=match.group(2).strip()
            )
            senses.append(sense)
        return senses
