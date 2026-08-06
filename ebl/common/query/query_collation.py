import re
import attr
from enum import Enum
from typing import Dict, Iterable, Literal, Mapping, Sequence
from urllib.parse import parse_qsl

DataType = Literal["dictionary", "afo-register", "colophons", "realia"]

REALIA_STRIP_CHARS = str.maketrans("", "", "“”„ʾ‘’'")


def strip_realia_query_chars(query: str) -> str:
    return query.translate(REALIA_STRIP_CHARS)


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
    REALIA = {
        "COLLATED_FIELDS": ["_id", "relatedTerms"],
        "WILDCARD_FIELDS": [],
        "MARKDOWN_FIELDS": [],
    }

    @staticmethod
    def findByDataType(data_type: DataType) -> Mapping[str, Sequence[str]]:
        if data_type == "dictionary":
            return Fields.DICTIONARY.value
        elif data_type == "afo-register":
            return Fields.AFO_REGISTER.value
        elif data_type == "colophons":
            return Fields.COLOPHONS.value
        elif data_type == "realia":
            return Fields.REALIA.value
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
    "collation S": {"wildcard": r"[sšṣśσSŠṢŚΣ]", "regex": r"[sšṣśσSŠṢŚΣ]"},
    "collation SS": {"wildcard": r"[sßS]", "regex": r"[sßS]"},
    "collation T": {"wildcard": r"[tṭτTṬΤ]", "regex": r"[tṭτTṬΤ]"},
    "collation D": {"wildcard": r"[dᵈD]", "regex": r"[dᵈD]"},
    "collation H": {"wildcard": r"[hḫḥHḪḤʕʾʿ]", "regex": r"[hḫḥHḪḤʕʾʿ]"},
    "collation C": {"wildcard": r"[cčçćCČÇĆ]", "regex": r"[cčçćCČÇĆ]"},
    "collation G": {"wildcard": r"[gĝğGĜĞ]", "regex": r"[gĝğGĜĞ]"},
    "collation K": {"wildcard": r"[kκKΚ]", "regex": r"[kκKΚ]"},
    "collation L": {"wildcard": r"[lłLŁ]", "regex": r"[lłLŁ]"},
    "collation N": {"wildcard": r"[nńňνNŃŇΝ]", "regex": r"[nńňνNŃŇΝ]"},
    "collation R": {"wildcard": r"[rřρRŘΡ]", "regex": r"[rřρRŘΡ]"},
    "collation Y": {"wildcard": r"[yýÿYÝŸ]", "regex": r"[yýÿYÝŸ]"},
    "collation X": {"wildcard": r"[xₓX]", "regex": r"[xₓX]"},
    "collation A": {"wildcard": r"[aāâáàäαAĀÂÁÀÄΑ]", "regex": r"[aāâáàäαAĀÂÁÀÄΑ]"},
    "collation E": {"wildcard": r"[eēêéèEĒÊÉÈ]", "regex": r"[eēêéèEĒÊÉÈ]"},
    "collation I": {"wildcard": r"[iīîíìïıιIĪÎÍÌÏΙ]", "regex": r"[iīîíìïıιIĪÎÍÌÏΙ]"},
    "collation U": {"wildcard": r"[uūûúùüůUŪÛÚÙÜŮ]", "regex": r"[uūûúùüůUŪÛÚÙÜŮ]"},
    "collation O": {
        "wildcard": r"[oòóôöøōőοOÒÓÔÖØŌŐΟ]",
        "regex": r"[oòóôöøōőοOÒÓÔÖØŌŐΟ]",
    },
    "collation 0": {"wildcard": r"[0₀⁰øØ]", "regex": r"[0₀⁰øØ]"},
    "collation 1": {"wildcard": r"[1₁¹]", "regex": r"[1₁¹]"},
    "collation 2": {"wildcard": r"[2₂²]", "regex": r"[2₂²]"},
    "collation 3": {"wildcard": r"[3₃³]", "regex": r"[3₃³]"},
    "collation 4": {"wildcard": r"[4₄⁴]", "regex": r"[4₄⁴]"},
    "collation 5": {"wildcard": r"[5₅⁵]", "regex": r"[5₅⁵]"},
    "collation 6": {"wildcard": r"[6₆⁶]", "regex": r"[6₆⁶]"},
    "collation 7": {"wildcard": r"[7₇⁷]", "regex": r"[7₇⁷]"},
    "collation 8": {"wildcard": r"[8₈⁸]", "regex": r"[8₈⁸]"},
    "collation 9": {"wildcard": r"[9₉⁹]", "regex": r"[9₉⁹]"},
    "collation +": {"wildcard": r"[+₊]", "regex": r"[+₊]"},
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
    return (
        CollatedFieldQuery(string, field, data_type)
        for field, string in query_dict.items()
    )
