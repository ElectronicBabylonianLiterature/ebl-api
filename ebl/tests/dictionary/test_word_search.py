from ebl.dictionary.web.word_search import WordSearch


class TestParseNestedQueryString:
    def test_no_query_key_returns_params_unchanged(self):
        params = {"lemma": "test"}
        result = WordSearch._parse_nested_query_string(params)
        assert result == params

    def test_query_not_string_returns_params_unchanged(self):
        params = {"query": 123}
        result = WordSearch._parse_nested_query_string(params)
        assert result == params

    def test_query_without_equals_returns_params_unchanged(self):
        params = {"query": "simple query"}
        result = WordSearch._parse_nested_query_string(params)
        assert result == params

    def test_query_with_embedded_query_string_parses_correctly(self):
        params = {"query": "word=test&origin=CDA"}
        result = WordSearch._parse_nested_query_string(params)
        assert result == {"word": "test", "origin": "CDA"}

    def test_query_with_repeated_keys_creates_list(self):
        params = {"query": "vowelClass=a%2Fi&vowelClass=a%2Fu&word=test"}
        result = WordSearch._parse_nested_query_string(params)
        assert result["word"] == "test"
        assert result["vowelClass"] == ["a/i", "a/u"]

    def test_query_with_existing_params_merges_correctly(self):
        params = {"query": "word=nested", "lemma": "direct"}
        result = WordSearch._parse_nested_query_string(params)
        assert result == {"word": "nested", "lemma": "direct"}

    def test_query_with_duplicate_key_existing_as_string_creates_list(self):
        params = {"query": "origin=CDA", "origin": "EBL"}
        result = WordSearch._parse_nested_query_string(params)
        assert result["origin"] == ["EBL", "CDA"]

    def test_query_with_duplicate_key_existing_as_list_appends(self):
        params = {"query": "origin=SAD", "origin": ["CDA", "EBL"]}
        result = WordSearch._parse_nested_query_string(params)
        assert result["origin"] == ["CDA", "EBL", "SAD"]


class TestNormalizeOriginValues:
    def test_normalize_string_origin_returns_unchanged(self):
        result = WordSearch._normalize_origin_values("CDA")
        assert result == "CDA"

    def test_normalize_single_item_list_returns_string(self):
        result = WordSearch._normalize_origin_values(["CDA"])
        assert result == "CDA"

    def test_normalize_multiple_origins_joins_with_comma(self):
        result = WordSearch._normalize_origin_values(["CDA", "EBL", "CDA_ADDENDA"])
        assert result == "CDA,EBL,CDA_ADDENDA"


class TestExtractSearchParams:
    def test_no_query_or_word_returns_empty_dict(self):
        result = WordSearch._extract_search_params({})
        assert result == {}

    def test_query_value_used_when_both_query_and_word_present(self):
        result = WordSearch._extract_search_params(
            {"query": "from_query", "word": "from_word"}
        )
        assert "word=from_query" in result["query"]

    def test_word_key_used_when_only_word_present(self):
        result = WordSearch._extract_search_params({"word": "test"})
        assert "word=test" in result["query"]

    def test_origin_added_to_sanitized_when_present(self):
        result = WordSearch._extract_search_params({"word": "test", "origin": "CDA"})
        assert result["origin"] == "CDA"

    def test_origin_not_added_when_not_present(self):
        result = WordSearch._extract_search_params({"word": "test"})
        assert "origin" not in result

    def test_meaning_included_in_query_string(self):
        result = WordSearch._extract_search_params(
            {"word": "test", "meaning": "to eat"}
        )
        assert "meaning=to+eat" in result["query"]

    def test_root_included_in_query_string(self):
        result = WordSearch._extract_search_params({"word": "test", "root": "k-l"})
        assert "root=k-l" in result["query"]

    def test_vowel_class_included_in_query_string(self):
        result = WordSearch._extract_search_params(
            {"word": "test", "vowelClass": ["a/i", "u/u"]}
        )
        assert "vowelClass=a%2Fi" in result["query"]
        assert "vowelClass=u%2Fu" in result["query"]

    def test_vowel_class_without_query_returns_query_with_vowel_class(self):
        result = WordSearch._extract_search_params({"vowelClass": ["a/i", "u/u"]})
        assert "vowelClass=a%2Fi" in result["query"]
        assert "vowelClass=u%2Fu" in result["query"]
        assert "word=" not in result["query"]

    def test_origin_and_vowel_class_without_query(self):
        result = WordSearch._extract_search_params(
            {"vowelClass": "a/i", "origin": "CDA"}
        )
        assert "vowelClass=a%2Fi" in result["query"]
        assert result["origin"] == "CDA"

    def test_origin_only_without_query_returns_empty(self):
        result = WordSearch._extract_search_params({"origin": "CDA"})
        assert result == {}

    def test_multiple_search_params_all_included(self):
        result = WordSearch._extract_search_params(
            {"word": "test", "meaning": "definition", "root": "prs", "origin": "CDA"}
        )
        assert "word=test" in result["query"]
        assert "meaning=definition" in result["query"]
        assert "root=prs" in result["query"]
        assert result["origin"] == "CDA"


class TestSanitize:
    def test_sanitize_with_query_and_lemma_returns_both(self):
        result = WordSearch._sanitize({"query": "test", "lemma": "lem"})
        assert result == {"query": "test", "lemma": "lem"}

    def test_sanitize_with_only_lemma_returns_lemma(self):
        result = WordSearch._sanitize({"lemma": "test"})
        assert result == {"lemma": "test"}

    def test_sanitize_with_only_lemmas_returns_lemmas(self):
        result = WordSearch._sanitize({"lemmas": "lem1,lem2"})
        assert result == {"lemmas": "lem1,lem2"}

    def test_sanitize_with_query_extracts_search_params(self):
        result = WordSearch._sanitize({"query": "test"})
        assert "query" in result
        assert "word=test" in result["query"]

    def test_sanitize_with_embedded_query_string(self):
        result = WordSearch._sanitize({"query": "word=nested&origin=CDA"})
        assert result["origin"] == "CDA"
        assert "word=nested" in result["query"]

    def test_sanitize_preserves_vowelClass_from_nested_query(self):
        result = WordSearch._sanitize(
            {"query": "word=test&vowelClass=a%2Fi&vowelClass=a%2Fu"}
        )
        assert "vowelClass=a%2Fi" in result["query"]
        assert "vowelClass=a%2Fu" in result["query"]


class TestMergeQueryAndOrigin:
    def test_merge_when_origin_already_in_query_returns_unchanged(self):
        query = "word=test&origin=CDA"
        result = WordSearch._merge_query_and_origin(query, "EBL")
        assert result == query

    def test_merge_appends_origin_to_nonempty_query(self):
        result = WordSearch._merge_query_and_origin("word=test", "CDA")
        assert result == "word=test&origin=CDA"

    def test_merge_with_empty_query_returns_origin_only(self):
        result = WordSearch._merge_query_and_origin("", "CDA")
        assert result == "origin=CDA"

    def test_merge_with_query_containing_multiple_params(self):
        query = "word=test&meaning=eat"
        result = WordSearch._merge_query_and_origin(query, "CDA")
        assert result == "word=test&meaning=eat&origin=CDA"


class TestNormalizeQuery:
    def test_normalize_query_with_equals_returns_unchanged(self):
        query = "word=test&origin=CDA"
        result = WordSearch._normalize_query(query)
        assert result == query

    def test_normalize_simple_query_encodes_as_query_param(self):
        result = WordSearch._normalize_query("test")
        assert result == "query=test"

    def test_normalize_query_with_special_chars_encodes_properly(self):
        result = WordSearch._normalize_query("test*")
        assert "query=" in result
        assert "*" in result or "%2A" in result


class TestBuildQueryString:
    def test_build_query_string_from_dict(self):
        result = WordSearch._build_query_string({"word": "test", "origin": "CDA"})
        assert "word=test" in result
        assert "origin=CDA" in result

    def test_build_query_string_with_list_values_repeated(self):
        result = WordSearch._build_query_string({"vowelClass": ["a/i", "u/u"]})
        assert "vowelClass=a%2Fi" in result
        assert "vowelClass=u%2Fu" in result

    def test_build_query_string_with_special_characters(self):
        result = WordSearch._build_query_string({"word": "te*st"})
        assert "word=te%2Ast" in result or "word=te*st" in result

    def test_build_query_string_empty_dict(self):
        result = WordSearch._build_query_string({})
        assert result == ""


class TestOnGet:
    def test_on_get_with_query_param_calls_dispatch(self, dictionary, when):
        word_search = WordSearch(dictionary)
        when(dictionary).search(...).thenReturn([])
        mock_req = type("Request", (), {"params": {"query": "test"}})()
        mock_resp = type("Response", (), {"media": None})()

        word_search.on_get(mock_req, mock_resp)

        assert mock_resp.media is not None

    def test_on_get_with_lemma_calls_search_lemma(self, dictionary, when):
        word_search = WordSearch(dictionary)
        when(dictionary).search_lemma(...).thenReturn([])
        mock_req = type("Request", (), {"params": {"lemma": "pa"}})()
        mock_resp = type("Response", (), {"media": None})()

        word_search.on_get(mock_req, mock_resp)

        assert mock_resp.media is not None

    def test_on_get_with_lemmas_calls_find_many(self, dictionary, when):
        word_search = WordSearch(dictionary)
        when(dictionary).find_many(...).thenReturn([])
        mock_req = type("Request", (), {"params": {"lemmas": "lem1,lem2"}})()
        mock_resp = type("Response", (), {"media": None})()

        word_search.on_get(mock_req, mock_resp)

        assert mock_resp.media is not None
