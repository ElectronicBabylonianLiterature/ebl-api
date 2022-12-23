import re
import attr
from typing import Dict, Iterable
from urllib.parse import parse_qsl

WILDCARD_FIELDS = ["word", "root"]
COLLATED_FIELDS = ["word", "meaning", "root"]

WILDCARD_MATCHERS: Dict[str, Dict[str, str]] = {
    "any sign": {"wildcard": r"\?", "regex": r"([^\s])"},
    "any sign+": {"wildcard": r"\*", "regex": r"([^\s])*"},
    "collation S": {"wildcard": r"[s|š|ṣ]", "regex": r"[s|š|ṣ]"},
    "collation T": {"wildcard": r"[t|ṭ]", "regex": r"[t|ṭ]"},
    "collation A": {"wildcard": r"[a|ā|â]", "regex": r"[a|ā|â]"},
    "collation E": {"wildcard": r"[e|ē|ê]", "regex": r"[e|ē|ê]"},
    "collation I": {"wildcard": r"[i|ī|î]", "regex": r"[i|ī|î]"},
    "collation U": {"wildcard": r"[u|ū|û]", "regex": r"[u|ū|û]"},
}


@attr.s(auto_attribs=True)
class DictionaryFieldQuery:
    string: str
    field: str
    use_wildcards: bool
    use_collations: bool = attr.ib(init=False)
    regexp: str = attr.ib(init=False)

    def __attrs_post_init__(self) -> None:
        self.string = self.string.strip(" ")
        self.use_collations = (
            not re.match(r'^".+"$', self.string) and self.field in COLLATED_FIELDS
        )
        self.string = self.string.strip('"')
        self.regexp = self._make_regexp()

    @property
    def value(self) -> str:
        return self.regexp or re.escape(self.string)

    @property
    def all_wildcards(self) -> str:
        return r"|".join(
            expression["wildcard"] for expression in WILDCARD_MATCHERS.values()
        )

    def _make_regexp(self) -> str:
        regexp = "".join(
            self._wildcards_to_regexp(segment) for segment in self._segmentize()
        )
        return regexp if regexp != re.escape(self.string) else ""

    def _segmentize(self) -> Iterable[str]:
        return (
            segment
            for segment in re.split(rf"({self.all_wildcards})", self.string)
            if segment
        )

    def _is_regex(self, segment, type) -> bool:
        if not re.match(expression["wildcard"], segment):
            return False
        return True if (
            "collation" in type
            and self.use_collations
        ) or (
            "collation" not in type
            and self.use_wildcards
        ) else False

    def _wildcards_to_regexp(self, segment: str) -> str:
        for type, expression in WILDCARD_MATCHERS.items():
            if self._is_regex(segment, type, expression):
                return expression["regex"]
        return re.escape(segment)


def make_query_params_from_string(query_string: str) -> Iterable[DictionaryFieldQuery]:
    parsed_query = parse_qsl(query_string)
    query_dict = dict(parsed_query) if parsed_query else {}
    return (
        DictionaryFieldQuery(string, field, field in WILDCARD_FIELDS)
        for field, string in query_dict.items()
    )
