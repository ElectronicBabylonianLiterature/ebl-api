from typing import Union
from urllib.parse import urlencode, parse_qsl

from ebl.dispatcher import create_dispatcher
from ebl.dictionary.application.dictionary_service import Dictionary


class WordSearch:
    def __init__(self, dictionary: Dictionary):
        self._dispatch = create_dispatcher(
            {
                frozenset(["query"]): lambda value: dictionary.search(
                    self._normalize_query(value["query"])
                ),
                frozenset(["query", "origin"]): lambda value: dictionary.search(
                    self._merge_query_and_origin(
                        self._normalize_query(value["query"]), value["origin"]
                    )
                ),
                frozenset(["lemma"]): lambda value: dictionary.search_lemma(
                    value["lemma"]
                ),
                frozenset(["lemmas"]): lambda value: dictionary.find_many(
                    value["lemmas"].split(",")
                ),
            }
        )

    @staticmethod
    def _build_query_string(params: dict) -> str:
        return urlencode(params, doseq=True)

    @staticmethod
    def _parse_nested_query_string(params: dict) -> dict:
        parsed_params = params.copy()
        if "query" not in parsed_params:
            return parsed_params

        query_value = parsed_params["query"]
        if not isinstance(query_value, str) or "=" not in query_value:
            return parsed_params

        query_string = parsed_params.pop("query")
        for key, value in parse_qsl(query_string, keep_blank_values=True):
            if key in parsed_params:
                existing = parsed_params[key]
                if isinstance(existing, list):
                    existing.append(value)
                else:
                    parsed_params[key] = [existing, value]
            else:
                parsed_params[key] = value

        return parsed_params

    @staticmethod
    def _normalize_origin_values(origin_value: Union[str, list[str]]) -> str:
        if isinstance(origin_value, list):
            return ",".join(origin_value)
        return origin_value

    @staticmethod
    def _extract_search_params(parsed_params: dict) -> dict:
        query_value = parsed_params.get("query") or parsed_params.get("word")
        if not query_value:
            return {}

        search_query: dict = {"word": query_value}
        for key in ["meaning", "root", "vowelClass"]:
            if key in parsed_params:
                search_query[key] = parsed_params[key]

        sanitized = {"query": WordSearch._build_query_string(search_query)}
        if "origin" in parsed_params:
            sanitized["origin"] = WordSearch._normalize_origin_values(
                parsed_params["origin"]
            )
        return sanitized

    @staticmethod
    def _sanitize(params: dict) -> dict:
        parsed_params = WordSearch._parse_nested_query_string(params)

        if "query" in parsed_params and "lemma" in parsed_params:
            return parsed_params

        search_params = WordSearch._extract_search_params(parsed_params)
        if search_params:
            return search_params

        if "lemma" in parsed_params:
            return {"lemma": parsed_params["lemma"]}
        if "lemmas" in parsed_params:
            return {"lemmas": parsed_params["lemmas"]}
        return parsed_params

    @staticmethod
    def _merge_query_and_origin(query_str: str, origin: str) -> str:
        if "origin=" in query_str:
            return query_str
        if query_str:
            return f"{query_str}&origin={origin}"
        return f"origin={origin}"

    @staticmethod
    def _normalize_query(query_value: str) -> str:
        if "=" in query_value:
            return query_value
        return urlencode({"query": query_value})

    def on_get(self, req, resp):
        resp.media = self._dispatch(self._sanitize(req.params))
