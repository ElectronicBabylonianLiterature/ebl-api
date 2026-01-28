from urllib.parse import urlencode

from ebl.dictionary.application.dictionary_service import (
    _parse_vowel_class_value,
    _parse_origin_value,
    _collect_parsed_params,
    _build_search_result,
    get_search_params,
)


class TestParseVowelClassValue:
    def test_parse_simple_vowel_class(self):
        result = _parse_vowel_class_value("a/i")
        assert result == ("a", "i")

    def test_parse_vowel_class_with_comma_separator(self):
        result = _parse_vowel_class_value("a,i")
        assert result == ("a", "i")

    def test_parse_vowel_class_with_mixed_separators(self):
        result = _parse_vowel_class_value("a,i/u")
        assert result == ("a", "i", "u")

    def test_parse_vowel_class_strips_whitespace(self):
        result = _parse_vowel_class_value("a / i / u")
        assert result == ("a", "i", "u")

    def test_parse_empty_vowel_class_returns_empty_tuple(self):
        result = _parse_vowel_class_value("")
        assert result == ()

    def test_parse_vowel_class_only_separators_returns_empty(self):
        result = _parse_vowel_class_value("/ / /")
        assert result == ()

    def test_parse_vowel_class_with_trailing_separator(self):
        result = _parse_vowel_class_value("a/i/")
        assert result == ("a", "i")


class TestParseOriginValue:
    def test_parse_single_origin(self):
        result = _parse_origin_value("CDA")
        assert result == ["CDA"]

    def test_parse_comma_separated_origins(self):
        result = _parse_origin_value("CDA,EBL,CDA_ADDENDA")
        assert result == ["CDA", "EBL", "CDA_ADDENDA"]

    def test_parse_origin_with_spaces_not_split(self):
        result = _parse_origin_value("CDA ADDENDA")
        assert result == ["CDA ADDENDA"]


class TestCollectParsedParams:
    def test_collect_query_parameter(self):
        parsed = [("query", "test")]
        vowel_classes, origins, other = _collect_parsed_params(parsed)
        assert other["word"] == "test"
        assert vowel_classes == []
        assert origins == []

    def test_collect_origin_parameter(self):
        parsed = [("origin", "CDA")]
        vowel_classes, origins, other = _collect_parsed_params(parsed)
        assert origins == ["CDA"]
        assert vowel_classes == []
        assert other == {}

    def test_collect_vowel_class_parameter(self):
        parsed = [("vowelClass", "a/i")]
        vowel_classes, origins, other = _collect_parsed_params(parsed)
        assert vowel_classes == [("a", "i")]
        assert origins == []
        assert other == {}

    def test_collect_multiple_vowel_classes(self):
        parsed = [("vowelClass", "a/i"), ("vowelClass", "u/u")]
        vowel_classes, origins, other = _collect_parsed_params(parsed)
        assert len(vowel_classes) == 2
        assert ("a", "i") in vowel_classes
        assert ("u", "u") in vowel_classes

    def test_collect_multiple_origins(self):
        parsed = [("origin", "CDA"), ("origin", "EBL")]
        vowel_classes, origins, other = _collect_parsed_params(parsed)
        assert origins == ["CDA", "EBL"]

    def test_collect_other_parameters(self):
        parsed = [("meaning", "to eat"), ("root", "k-l")]
        vowel_classes, origins, other = _collect_parsed_params(parsed)
        assert other["meaning"] == "to eat"
        assert other["root"] == "k-l"

    def test_collect_mixed_parameters(self):
        parsed = [
            ("query", "test"),
            ("origin", "CDA"),
            ("vowelClass", "a/i"),
            ("meaning", "test meaning"),
        ]
        vowel_classes, origins, other = _collect_parsed_params(parsed)
        assert other["word"] == "test"
        assert other["meaning"] == "test meaning"
        assert origins == ["CDA"]
        assert vowel_classes == [("a", "i")]

    def test_collect_empty_list(self):
        vowel_classes, origins, other = _collect_parsed_params([])
        assert vowel_classes == []
        assert origins == []
        assert other == {}


class TestBuildSearchResult:
    def test_build_result_with_word_only(self):
        other = {"word": "test"}
        result = _build_search_result([], [], other)
        assert "word" in result
        assert result["origin"] == []

    def test_build_result_with_origins(self):
        other = {"word": "test"}
        result = _build_search_result([], ["CDA", "EBL"], other)
        assert result["origin"] == ["CDA", "EBL"]

    def test_build_result_with_vowel_classes(self):
        other = {"word": "test"}
        vowel_classes = [("a", "i"), ("u", "u")]
        result = _build_search_result(vowel_classes, [], other)
        assert result["vowel_class"] == vowel_classes

    def test_build_result_with_all_params(self):
        other = {"word": "test", "meaning": "to eat", "root": "k-l"}
        vowel_classes = [("a", "i")]
        origins = ["CDA"]
        result = _build_search_result(vowel_classes, origins, other)
        assert "word" in result
        assert "meaning" in result
        assert "root" in result
        assert result["vowel_class"] == vowel_classes
        assert result["origin"] == origins

    def test_build_result_empty_other_params_no_origin_added(self):
        result = _build_search_result([], [], {})
        assert "origin" not in result

    def test_build_result_defaults_to_empty_origin_list(self):
        other = {"word": "test"}
        result = _build_search_result([], [], other)
        assert result["origin"] == []


class TestGetSearchParams:
    def test_get_search_params_with_word(self):
        query = urlencode({"word": "test"})
        result = get_search_params(query)
        assert "word" in result

    def test_get_search_params_with_origin(self):
        query = urlencode({"word": "test", "origin": "CDA"})
        result = get_search_params(query)
        assert result["origin"] == ["CDA"]

    def test_get_search_params_with_multiple_origins(self):
        query = "word=test&origin=CDA&origin=EBL"
        result = get_search_params(query)
        assert result["origin"] == ["CDA", "EBL"]

    def test_get_search_params_with_vowel_class(self):
        query = "word=test&vowelClass=a%2Fi&vowelClass=a%2Fu"
        result = get_search_params(query)
        assert "vowel_class" in result
        assert len(result["vowel_class"]) == 2

    def test_get_search_params_with_meaning(self):
        query = urlencode({"word": "test", "meaning": "to eat"})
        result = get_search_params(query)
        assert "meaning" in result

    def test_get_search_params_with_root(self):
        query = urlencode({"word": "test", "root": "k-l"})
        result = get_search_params(query)
        assert "root" in result

    def test_get_search_params_empty_query(self):
        result = get_search_params("")
        assert result == {}

    def test_get_search_params_complex_query(self):
        query = "word=test&meaning=definition&root=abc&vowelClass=a%2Fi&origin=CDA&origin=EBL"
        result = get_search_params(query)
        assert "word" in result
        assert "meaning" in result
        assert "root" in result
        assert "vowel_class" in result
        assert result["origin"] == ["CDA", "EBL"]
