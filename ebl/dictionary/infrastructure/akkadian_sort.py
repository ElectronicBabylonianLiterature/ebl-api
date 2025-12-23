import roman
from typing import Any, Dict, Tuple, List

AKKADIAN_BASE_ORDER = "'abdeghḫiklmnpqrsṣštṭuwyz"
AKKADIAN_SORT_DEFAULT = 10000
ROMAN_NUMERALS = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
ROMAN_PATTERN = r"^(M{0,3}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3}))$"


def _build_base_map() -> Dict[str, int]:
    base_map = {
        **{char.upper(): idx * 2 for idx, char in enumerate(AKKADIAN_BASE_ORDER)},
        **{char: idx * 2 + 1 for idx, char in enumerate(AKKADIAN_BASE_ORDER)},
    }
    for variants, base in [
        ("ĀÂ", "A"),
        ("āâ", "a"),
        ("ĒÊ", "E"),
        ("ēê", "e"),
        ("ĪÎ", "I"),
        ("īî", "i"),
        ("ŪÛ", "U"),
        ("ūû", "u"),
    ]:
        for variant in variants:
            base_map[variant] = base_map[base]
    base_map[" "] = -1
    return base_map


def _build_accent_map() -> Dict[str, int]:
    accent_map = {
        **dict.fromkeys(AKKADIAN_BASE_ORDER, 0),
        **{char.upper(): 0 for char in AKKADIAN_BASE_ORDER},
    }
    accent_map[" "] = 0
    for variants in ["āĀēĒīĪūŪ", "âÂêÊîÎûÛ"]:
        weight = 1 if "ā" in variants else 2
        for char in variants:
            accent_map[char] = weight
    return accent_map


AKKADIAN_BASE_MAP = _build_base_map()
AKKADIAN_ACCENT_MAP = _build_accent_map()


def _split_prefix_and_roman(text: str) -> Tuple[str, int]:
    parts = text.rsplit(" ", 1)
    if len(parts) != 2:
        return text, 0

    prefix, candidate = parts
    try:
        value = roman.fromRoman(candidate.upper())
        return prefix, value
    except roman.InvalidRomanNumeralError:
        return text, 0


def akkadian_sort_key(text: str) -> List[int]:
    prefix, roman_value = _split_prefix_and_roman(text)
    base = [AKKADIAN_BASE_MAP.get(char, AKKADIAN_SORT_DEFAULT) for char in prefix]
    accent = [AKKADIAN_ACCENT_MAP.get(char, 0) for char in prefix]
    return base + accent + [roman_value]


def _make_character_switch(
    weight_map: Dict[str, int], default_value: int
) -> Dict[str, Any]:
    return {
        "$switch": {
            "branches": [
                {"case": {"$eq": ["$$char", char]}, "then": value}
                for char, value in weight_map.items()
            ],
            "default": default_value,
        }
    }


def _map_weight_expr(
    source: Any, weight_map: Dict[str, int], default_value: int
) -> Dict[str, Any]:
    return {
        "$map": {
            "input": {"$range": [0, {"$strLenCP": source}]},
            "as": "idx",
            "in": {
                "$let": {
                    "vars": {"char": {"$substrCP": [source, "$$idx", 1]}},
                    "in": _make_character_switch(weight_map, default_value),
                }
            },
        }
    }


def _make_roman_numeral_switch() -> Dict[str, Any]:
    return {
        "$switch": {
            "branches": [
                {
                    "case": {"$eq": [{"$substrCP": ["$$roman_token", "$$i", 1]}, char]},
                    "then": value,
                }
                for char, value in ROMAN_NUMERALS.items()
            ],
            "default": 0,
        }
    }


def _map_roman_characters(roman_token: Any) -> Dict[str, Any]:
    return {
        "$map": {
            "input": {"$range": [0, {"$strLenCP": roman_token}]},
            "as": "i",
            "in": {
                "$let": {
                    "vars": {"roman_token": roman_token},
                    "in": _make_roman_numeral_switch(),
                }
            },
        }
    }


def _apply_roman_rules(values: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "$map": {
            "input": {"$range": [0, {"$size": values}]},
            "as": "i",
            "in": {
                "$let": {
                    "vars": {
                        "val": {"$arrayElemAt": [values, "$$i"]},
                        "next": {
                            "$cond": [
                                {"$lt": ["$$i", {"$add": [{"$size": values}, -1]}]},
                                {"$arrayElemAt": [values, {"$add": ["$$i", 1]}]},
                                0,
                            ]
                        },
                    },
                    "in": {
                        "$cond": [
                            {"$lt": ["$$val", "$$next"]},
                            {"$multiply": ["$$val", -1]},
                            "$$val",
                        ]
                    },
                }
            },
        }
    }


def _roman_value_expr(roman_token: Any) -> Dict[str, Any]:
    values = _map_roman_characters(roman_token)
    terms = _apply_roman_rules(values)
    return {
        "$reduce": {
            "input": terms,
            "initialValue": 0,
            "in": {"$add": ["$$value", "$$this"]},
        }
    }


def _is_roman_check(last_element: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "$regexMatch": {
            "input": {"$toUpper": last_element},
            "regex": ROMAN_PATTERN,
        }
    }


def _extract_prefix(parts: Dict[str, Any], is_roman: Dict[str, Any]) -> Dict[str, Any]:
    prefix_parts = {
        "$cond": [
            is_roman,
            {"$slice": [parts, 0, {"$add": [{"$size": parts}, -1]}]},
            parts,
        ]
    }
    return {
        "$reduce": {
            "input": prefix_parts,
            "initialValue": "",
            "in": {
                "$cond": [
                    {"$eq": ["$$value", ""]},
                    "$$this",
                    {"$concat": ["$$value", " ", "$$this"]},
                ]
            },
        }
    }


def _pad_and_concat_weights(
    base_array: Dict[str, Any],
    accent_array: Dict[str, Any],
    roman_value: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "$reduce": {
            "input": {"$concatArrays": [base_array, accent_array, [roman_value]]},
            "initialValue": "",
            "in": {
                "$concat": ["$$value", {"$substr": [{"$add": [1000, "$$this"]}, 0, 4]}]
            },
        }
    }


def create_mongo_sort_key(field: str = "$_id") -> Dict[str, Any]:
    parts = {"$split": [field, " "]}
    last = {"$arrayElemAt": [parts, -1]}
    is_roman = _is_roman_check(last)
    prefix = _extract_prefix(parts, is_roman)
    roman_value = {"$cond": [is_roman, _roman_value_expr({"$toUpper": last}), 0]}

    base_array = _map_weight_expr(prefix, AKKADIAN_BASE_MAP, AKKADIAN_SORT_DEFAULT)
    accent_array = _map_weight_expr(prefix, AKKADIAN_ACCENT_MAP, 0)

    return _pad_and_concat_weights(base_array, accent_array, roman_value)
