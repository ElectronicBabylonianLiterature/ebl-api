"""Parsing of the free-text bibliography search query.

Extracted from `Bibliography` so the service stays within the file-size limit
and so the patterns can be tested without a repository.
"""

import re


def parse_author_year_and_title(query: str) -> dict:
    parsed_query = dict.fromkeys(["author", "year", "title"])
    if match := re.match(r"^([^\d]+)(?: (\d{1,4})(?: (.*))?)?$", query):
        parsed_query["author"] = match[1]
        parsed_query["year"] = int(match[2]) if match[2] else None
        parsed_query["title"] = match[3]
    return parsed_query


def parse_container_title_short_and_collection_number(query: str) -> dict:
    parsed_query = dict.fromkeys(["container_title_short", "collection_number"])
    if match := re.match(r"^([^\s]+)(?: (\d*))?$", query):
        parsed_query["container_title_short"] = match[1]
        parsed_query["collection_number"] = match[2]
    return parsed_query


def parse_title_short_and_volume(query: str) -> dict:
    parsed_query = dict.fromkeys(["title_short", "volume"])
    if match := re.match(r"^([^\s]+)(?: (\d*))?$", query):
        parsed_query["title_short"] = match[1]
        parsed_query["volume"] = match[2]
    return parsed_query
