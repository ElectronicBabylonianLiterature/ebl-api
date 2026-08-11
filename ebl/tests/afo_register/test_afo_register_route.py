import falcon
import pytest
import json
import re
from mockito import when

from ebl.afo_register.domain.afo_register_record import AfoRegisterRecord
from ebl.tests.factories.afo_register import (
    AfoRegisterRecordFactory,
    AfoRegisterRecordSuggestionFactory,
)
from ebl.afo_register.application.afo_register_repository import (
    AfoRegisterRepository,
)
from ebl.afo_register.infrastructure.mongo_afo_register_repository import (
    MAX_CANDIDATES,
    TOO_MANY_CANDIDATES_MESSAGE,
    AfoRegisterRecordSchema,
    AfoRegisterRecordSuggestionSchema,
)
from ebl.afo_register.web.afo_register_records import (
    count_candidate_splits,
    validate_candidate_budget,
    validate_texts_and_numbers_query,
    MAX_TEXTS_AND_NUMBERS_QUERIES,
    MAX_QUERY_LENGTH,
    MAX_QUERY_TOKENS,
)
from ebl.errors import DataError


@pytest.fixture
def afo_register_record() -> AfoRegisterRecord:
    return AfoRegisterRecordFactory.build()


def test_search_afo_register_record_route(
    afo_register_record, afo_register_repository: AfoRegisterRepository, client
) -> None:
    params = {
        "afoNumber": afo_register_record.afo_number,
        "page": afo_register_record.page,
        "text": afo_register_record.text,
        "textNumber": afo_register_record.text_number,
        "linesDiscussed": afo_register_record.lines_discussed,
        "discussedBy": afo_register_record.discussed_by,
        "discussedByNotes": afo_register_record.discussed_by_notes,
    }
    afo_register_repository.create(afo_register_record)
    get_result = client.simulate_get("/afo-register", params=params)

    assert get_result.status == falcon.HTTP_OK
    assert get_result.json == [AfoRegisterRecordSchema().dump(afo_register_record)]


def test_search_by_texts_and_numbers_route(
    afo_register_repository: AfoRegisterRepository, client
) -> None:
    record1 = AfoRegisterRecordFactory.build(text="Text1", text_number="1")
    record2 = AfoRegisterRecordFactory.build(text="Text2", text_number="2")
    record3 = AfoRegisterRecordFactory.build(text="Text3", text_number="3")
    afo_register_repository.create(record1)
    afo_register_repository.create(record2)
    afo_register_repository.create(record3)
    get_result = client.simulate_post(
        "/afo-register/texts-numbers", body=json.dumps(["Text1 1", "Text3 3"])
    )
    expected_results = [
        AfoRegisterRecordSchema().dump(record) for record in [record1, record3]
    ]

    assert get_result.status == falcon.HTTP_OK
    assert get_result.json == expected_results


def test_search_by_texts_and_numbers_route_with_spaces(
    afo_register_repository: AfoRegisterRepository, client
) -> None:
    record = AfoRegisterRecordFactory.build(text="OrNS", text_number="59, 17")
    afo_register_repository.create(record)
    afo_register_repository.create(
        AfoRegisterRecordFactory.build(text="OrNS", text_number="59, 26ff.")
    )

    get_result = client.simulate_post(
        "/afo-register/texts-numbers", body=json.dumps(["OrNS 59, 17"])
    )

    assert get_result.status == falcon.HTTP_OK
    assert get_result.json == [AfoRegisterRecordSchema().dump(record)]


def test_validate_texts_and_numbers_query_passes_valid_body():
    assert validate_texts_and_numbers_query(["OrNS 59, 17"]) == ["OrNS 59, 17"]


def test_validate_texts_and_numbers_query_rejects_non_list():
    with pytest.raises(DataError):
        validate_texts_and_numbers_query({"not": "a list"})


def test_validate_texts_and_numbers_query_rejects_too_many_queries():
    with pytest.raises(DataError):
        validate_texts_and_numbers_query(["x"] * (MAX_TEXTS_AND_NUMBERS_QUERIES + 1))


def test_validate_texts_and_numbers_query_rejects_non_string_element():
    with pytest.raises(DataError):
        validate_texts_and_numbers_query(["ok", 5])


def test_validate_texts_and_numbers_query_rejects_too_long_query():
    with pytest.raises(DataError):
        validate_texts_and_numbers_query(["x" * (MAX_QUERY_LENGTH + 1)])


def test_validate_texts_and_numbers_query_rejects_query_with_too_many_words():
    with pytest.raises(DataError):
        validate_texts_and_numbers_query([" ".join(["x"] * (MAX_QUERY_TOKENS + 1))])


def test_search_by_texts_and_numbers_route_rejects_oversized_body(client) -> None:
    get_result = client.simulate_post(
        "/afo-register/texts-numbers",
        body=json.dumps(["x"] * (MAX_TEXTS_AND_NUMBERS_QUERIES + 1)),
    )

    assert get_result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_search_by_texts_and_numbers_route_rejects_too_many_words(client) -> None:
    get_result = client.simulate_post(
        "/afo-register/texts-numbers",
        body=json.dumps([" ".join(["x"] * (MAX_QUERY_TOKENS + 1))]),
    )

    assert get_result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def build_maximal_queries(count: int) -> list:
    return [
        " ".join([f"text{index}"] + [f"token{position}" for position in range(23)])
        for index in range(count)
    ]


def test_count_candidate_splits_counts_split_points():
    assert count_candidate_splits(["A B C", "A", ""]) == 2


def test_validate_candidate_budget_accepts_the_largest_allowed_batch():
    queries = build_maximal_queries(MAX_CANDIDATES // 23)

    assert validate_candidate_budget(queries) == queries


def test_validate_candidate_budget_rejects_an_over_broad_batch():
    with pytest.raises(DataError, match=re.escape(TOO_MANY_CANDIDATES_MESSAGE)):
        validate_candidate_budget(build_maximal_queries(MAX_CANDIDATES // 23 + 1))


def test_search_by_texts_and_numbers_route_rejects_too_broad_query(client) -> None:
    get_result = client.simulate_post(
        "/afo-register/texts-numbers",
        body=json.dumps(build_maximal_queries(MAX_CANDIDATES // 23 + 1)),
    )

    assert get_result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert get_result.json["description"] == TOO_MANY_CANDIDATES_MESSAGE


def test_search_by_texts_and_numbers_route_accepts_the_largest_allowed_batch(
    client,
) -> None:
    get_result = client.simulate_post(
        "/afo-register/texts-numbers",
        body=json.dumps(build_maximal_queries(MAX_CANDIDATES // 23)),
    )

    assert get_result.status == falcon.HTTP_OK
    assert get_result.json == []


def test_search_afo_register_route_not_found_on_value_error(
    afo_register_repository: AfoRegisterRepository, client
) -> None:
    when(afo_register_repository).search({"text": "x"}).thenRaise(ValueError())

    get_result = client.simulate_get("/afo-register", params={"text": "x"})

    assert get_result.status == falcon.HTTP_NOT_FOUND


def test_search_by_texts_and_numbers_route_not_found_on_value_error(
    afo_register_repository: AfoRegisterRepository, client
) -> None:
    when(afo_register_repository).search_by_texts_and_numbers(["A B"]).thenRaise(
        ValueError()
    )

    get_result = client.simulate_post(
        "/afo-register/texts-numbers", body=json.dumps(["A B"])
    )

    assert get_result.status == falcon.HTTP_NOT_FOUND


def test_search_afo_register_suggestions_route(
    afo_register_record, afo_register_repository: AfoRegisterRepository, client
) -> None:
    afo_register_repository.create(afo_register_record)
    get_result = client.simulate_get(
        "/afo-register/suggestions",
        params={"text_query": afo_register_record.text[:-2]},
    )
    afo_register_record_suggestion = AfoRegisterRecordSuggestionFactory.build(
        text=afo_register_record.text, text_numbers=[afo_register_record.text_number]
    )

    assert get_result.status == falcon.HTTP_OK
    assert get_result.json == [
        AfoRegisterRecordSuggestionSchema().dump(afo_register_record_suggestion)
    ]
