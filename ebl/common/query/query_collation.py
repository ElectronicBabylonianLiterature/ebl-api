import re
import attr
from enum import Enum
from typing import Dict, Iterable, Literal, Sequence
from urllib.parse import parse_qsl

DataType = Literal["dictionary", "afo-register", "colophons"]


class Fields(Enum):
    DICTIONARY = {
        "COLLATED_FIELDS": ["word", "meaning", "root"],
        "WILDCARD_FIELDS": ["word", "root"],
        "MARKDOWN_FIELDS": [],
    }
    AFO_REGISTER = {
        "COLLATED_FIELDS": ["text"],
        "WILDCARD_FIELDS": [],
        "MARKDOWN_FIELDS": ["text"],
    }
    COLOPHONS = {
        "COLLATED_FIELDS": ["names"],
        "WILDCARD_FIELDS": [],
        "MARKDOWN_FIELDS": [],
    }

    @staticmethod
    def findByDataType(data_type: DataType) -> Dict[str, Sequence[str]]:
        if data_type == "dictionary":
            return Fields.DICTIONARY.value
        elif data_type == "afo-register":
            return Fields.AFO_REGISTER.value
        elif data_type == "colophons":
            return Fields.COLOPHONS.value
        else:
            raise ValueError("Invalid data type")

    @staticmethod
    def use_collations(data_type: DataType, field_name: str) -> bool:
        return field_name in Fields.findByDataType(data_type)["COLLATED_FIELDS"]

    @staticmethod
    def use_wildcards(data_type: DataType, field_name: str) -> bool:
        return field_name in Fields.findByDataType(data_type)["WILDCARD_FIELDS"]

    @staticmethod
    def use_markdown_escape(data_type: DataType, field_name: str) -> bool:
        return field_name in Fields.findByDataType(data_type)["MARKDOWN_FIELDS"]


WILDCARD_AND_COLLATION_MATCHERS: Dict[str, Dict[str, str]] = {
    "any sign": {"wildcard": r"\?", "regex": r"[^\s]"},
    "any sign+": {"wildcard": r"\*", "regex": r"[^\s]*"},
    "collation S": {"wildcard": r"[s|š|ṣ|ś|σ]", "regex": r"[s|š|ṣ|ś|σ]"},
    "collation SS": {"wildcard": r"[ss|ß]", "regex": r"[ss|ß]"},
    "collation T": {"wildcard": r"[t|ṭ|τ]", "regex": r"[t|ṭ|τ]"},
    "collation D": {"wildcard": r"[d|ᵈ]", "regex": r"[d|ᵈ]"},
    "collation H": {"wildcard": r"[h|ḫ|ḥ|ʕ|ʾ|ʿ]", "regex": r"[h|ḫ|ḥ|ʕ|ʾ|ʿ]"},
    "collation C": {"wildcard": r"[c|č|ç|ć]", "regex": r"[c|č|ç|ć]"},
    "collation G": {"wildcard": r"[g|ĝ|ğ]", "regex": r"[g|ĝ|ğ]"},
    "collation K": {"wildcard": r"[k|κ]", "regex": r"[k|κ]"},
    "collation L": {"wildcard": r"[l|ł]", "regex": r"[l|ł]"},
    "collation N": {"wildcard": r"[n|ń|ň|ν]", "regex": r"[n|ń|ň|ν]"},
    "collation R": {"wildcard": r"[r|ř|ρ]", "regex": r"[r|ř|ρ]"},
    "collation Y": {"wildcard": r"[y|ý|ÿ]", "regex": r"[y|ý|ÿ]"},
    "collation X": {"wildcard": r"[x|ₓ]", "regex": r"[x|ₓ]"},
    "collation A": {"wildcard": r"[a|ā|â|á|à|ä|α]", "regex": r"[a|ā|â|á|à|ä|α]"},
    "collation E": {"wildcard": r"[e|ē|ê|é|è]", "regex": r"[e|ē|ê|é|è]"},
    "collation I": {"wildcard": r"[i|ī|î|í|ì|ï|ı|ι]", "regex": r"[i|ī|î|í|ì|ï|ı|ι]"},
    "collation U": {"wildcard": r"[u|ū|û|ú|ù|ü|ů]", "regex": r"[u|ū|û|ú|ù|ü|ů]"},
    "collation O": {
        "wildcard": r"[o|ò|ó|ô|ö|ø|ō|ő|ο]",
        "regex": r"[o|ò|ó|ô|ö|ø|ō|ő|ο]",
    },
    "collation 0": {"wildcard": r"[0|₀|⁰|ø]", "regex": r"[0|₀|⁰|ø]"},
    "collation 1": {"wildcard": r"[1|₁|¹]", "regex": r"[1|₁|¹]"},
    "collation 2": {"wildcard": r"[2|₂|²]", "regex": r"[2|₂|²]"},
    "collation 3": {"wildcard": r"[3|₃|³]", "regex": r"[3|₃|³]"},
    "collation 4": {"wildcard": r"[4|₄|⁴]", "regex": r"[4|₄|⁴]"},
    "collation 5": {"wildcard": r"[5|₅|⁵]", "regex": r"[5|₅|⁵]"},
    "collation 6": {"wildcard": r"[6|₆|⁶]", "regex": r"[6|₆|⁶]"},
    "collation 7": {"wildcard": r"[7|₇|⁷]", "regex": r"[7|₇|⁷]"},
    "collation 8": {"wildcard": r"[8|₈|⁸]", "regex": r"[8|₈|⁸]"},
    "collation 9": {"wildcard": r"[9|₉|⁹]", "regex": r"[9|₉|⁹]"},
    "collation +": {"wildcard": r"[+|₊]", "regex": r"[+|₊]"},
}

markdown_escape = r"(\*|\^)*"


@attr.s(auto_attribs=True)
class CollatedFieldQuery:
    string: str
    field: str
    data_type: DataType = attr.ib(default="dictionary")
    use_wildcards: bool = attr.ib(default=False)
    use_collations: bool = attr.ib(default=False)
    use_markdown_escape: bool = attr.ib(default=False)
    regexp: str = attr.ib(default="")

    def __attrs_post_init__(self) -> None:
        self.string = self.string.strip(" ")
        self.use_collations = Fields.use_collations(
            self.data_type, self.field
        ) and not re.match(r'^".+"$', self.string)
        self.use_wildcards = Fields.use_wildcards(self.data_type, self.field)
        self.use_markdown_escape = Fields.use_markdown_escape(
            self.data_type, self.field
        )
        self.string = self.string.strip('"')
        self.regexp = self._make_regexp()

    @property
    def value(self) -> str:
        return self.regexp or re.escape(self.string)

    @property
    def all_wildcards(self) -> str:
        return r"|".join(
            expression["wildcard"]
            for expression in WILDCARD_AND_COLLATION_MATCHERS.values()
        )

    def _make_regexp(self) -> str:
        regexp = r"".join(
            self._wildcards_to_regexp(segment) for segment in self._segmentize()
        ).replace(markdown_escape + markdown_escape, markdown_escape)
        return regexp if regexp != re.escape(self.string) else ""

    def _segmentize(self) -> Iterable[str]:
        return (
            segment
            for segment in re.split(rf"({self.all_wildcards})", self.string)
            if segment
        )

    def _is_regex(self, segment: str, type: str, expression: Dict) -> bool:
        return (
            bool(
                ("collation" in type and self.use_collations)
                or ("collation" not in type and self.use_wildcards)
            )
            if re.match(expression["wildcard"], segment)
            else False
        )

    def _wildcards_to_regexp(self, segment: str) -> str:
        for type, expression in WILDCARD_AND_COLLATION_MATCHERS.items():
            if not self._is_regex(segment, type, expression):
                continue
            return self._process_expression(segment, expression)

        return self._escape_segment(segment)

    def _process_expression(self, segment: str, expression: Dict) -> str:
        regex = expression["regex"]
        return (
            self._markdown_aware_regex(regex, False)
            if self.use_markdown_escape
            else regex
        )

    def _escape_segment(self, segment: str) -> str:
        if self.use_markdown_escape:
            return r"".join([self._markdown_aware_regex(char) for char in segment])
        else:
            return re.escape(segment)

    def _markdown_aware_regex(self, segment: str, escape=True) -> str:
        return r"".join(
            [
                markdown_escape
                + (re.escape(segment) if escape else segment)
                + markdown_escape
            ]
        )


def make_query_params_from_string(
    query_string: str, data_type: DataType = "dictionary"
) -> Iterable[CollatedFieldQuery]:
    parsed_query = parse_qsl(query_string)
    query_dict = dict(parsed_query) if parsed_query else {}
    return make_query_params(query_dict, data_type)


def make_query_params(
    query_dict: dict, data_type: DataType = "dictionary"
) -> Iterable[CollatedFieldQuery]:
    if "vowelClass" in query_dict:
        query_dict["vowel_class"] = query_dict.pop("vowelClass")
    return (
        CollatedFieldQuery(string, field, data_type)
        for field, string in query_dict.items()
    )
