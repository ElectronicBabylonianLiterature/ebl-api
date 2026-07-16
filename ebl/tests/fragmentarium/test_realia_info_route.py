import falcon

from ebl.fragmentarium.domain.named_entity import RealiaAnnotationSpan
from ebl.realia.infrastructure.realia_schemas import RealiaEntrySchema
from ebl.tests.factories.fragment import TransliteratedFragmentFactory
from ebl.tests.factories.realia import RealiaEntryFactory

APKALLU_ID = "realia_000846"
LAMASSU_ID = "realia_000847"
DANGLING_ID = "realia_999999"


def store_realia(realia_repository, realia_id, lemma, type_):
    entry = RealiaEntryFactory.build(
        id=lemma,
        realia_id=realia_id,
        type=type_,
        related_terms=(),
        references=(),
        reallexikon=(),
    )
    realia_repository._realia_collection.insert_one(RealiaEntrySchema().dump(entry))


def create_realia_fragment(fragmentarium, realia_spans):
    fragment = TransliteratedFragmentFactory.build().set_token_ids()
    fragment = fragment.set_named_entities([], realia_spans)
    fragmentarium.create(fragment)
    return fragment


def test_realia_info_per_distinct_id_from_single_batch(
    client, fragmentarium, realia_repository, monkeypatch
):
    store_realia(realia_repository, APKALLU_ID, "Apkallu", ["Divine names"])
    store_realia(realia_repository, LAMASSU_ID, "Lamassu", ["Object names"])
    fragment = create_realia_fragment(
        fragmentarium,
        [
            RealiaAnnotationSpan("Realia-1", APKALLU_ID, ["Word-2", "Word-3"]),
            RealiaAnnotationSpan("Realia-2", LAMASSU_ID, ["Word-7"]),
        ],
    )

    calls = []
    original = realia_repository.find_by_realia_ids

    def counting(realia_ids):
        calls.append(list(realia_ids))
        return original(realia_ids)

    monkeypatch.setattr(realia_repository, "find_by_realia_ids", counting)

    result = client.simulate_get(f"/fragments/{fragment.number}")

    assert result.status == falcon.HTTP_OK
    assert result.json["realiaInfo"] == [
        {"realiaId": APKALLU_ID, "lemma": "Apkallu", "type": ["Divine names"]},
        {"realiaId": LAMASSU_ID, "lemma": "Lamassu", "type": ["Object names"]},
    ]
    assert len(calls) == 1


def test_realia_info_dedupes_repeated_ids(client, fragmentarium, realia_repository):
    store_realia(realia_repository, APKALLU_ID, "Apkallu", ["Divine names"])
    fragment = create_realia_fragment(
        fragmentarium,
        [
            RealiaAnnotationSpan("Realia-1", APKALLU_ID, ["Word-2"]),
            RealiaAnnotationSpan("Realia-2", APKALLU_ID, ["Word-7"]),
        ],
    )

    result = client.simulate_get(f"/fragments/{fragment.number}")

    assert result.json["realiaInfo"] == [
        {"realiaId": APKALLU_ID, "lemma": "Apkallu", "type": ["Divine names"]}
    ]


def test_realia_info_omits_dangling_id(client, fragmentarium, realia_repository):
    store_realia(realia_repository, APKALLU_ID, "Apkallu", ["Divine names"])
    fragment = create_realia_fragment(
        fragmentarium,
        [
            RealiaAnnotationSpan("Realia-1", APKALLU_ID, ["Word-2"]),
            RealiaAnnotationSpan("Realia-2", DANGLING_ID, ["Word-7"]),
        ],
    )

    result = client.simulate_get(f"/fragments/{fragment.number}")

    assert result.status == falcon.HTTP_OK
    assert result.json["realiaInfo"] == [
        {"realiaId": APKALLU_ID, "lemma": "Apkallu", "type": ["Divine names"]}
    ]


def test_realia_info_empty_without_annotations(client, fragmentarium):
    fragment = TransliteratedFragmentFactory.build()
    fragmentarium.create(fragment)

    result = client.simulate_get(f"/fragments/{fragment.number}")

    assert result.status == falcon.HTTP_OK
    assert result.json["realiaInfo"] == []


def test_write_neither_requires_nor_stores_realia_info(
    client, fragmentarium, realia_repository
):
    store_realia(realia_repository, APKALLU_ID, "Apkallu", ["Divine names"])
    fragment = TransliteratedFragmentFactory.build().set_token_ids()
    fragmentarium.create(fragment)
    url = f"/fragments/{fragment.number}/named-entities"
    payload = {
        "namedEntities": [],
        "realia": [{"id": "Realia-1", "realiaId": APKALLU_ID, "span": ["Word-2"]}],
        "realiaInfo": [{"realiaId": APKALLU_ID, "lemma": "WRONG", "type": ["Wrong"]}],
    }
    resolved = [{"realiaId": APKALLU_ID, "lemma": "Apkallu", "type": ["Divine names"]}]

    post_result = client.simulate_post(url, json=payload)

    assert post_result.status == falcon.HTTP_OK
    assert post_result.json["realiaInfo"] == resolved

    get_result = client.simulate_get(f"/fragments/{fragment.number}")
    assert get_result.json["realiaInfo"] == resolved


def test_write_response_realia_info_matches_get(
    client, fragmentarium, realia_repository
):
    store_realia(realia_repository, APKALLU_ID, "Apkallu", ["Divine names"])
    store_realia(realia_repository, LAMASSU_ID, "Lamassu", ["Object names"])
    fragment = TransliteratedFragmentFactory.build().set_token_ids()
    fragmentarium.create(fragment)
    url = f"/fragments/{fragment.number}/named-entities"
    payload = {
        "namedEntities": [],
        "realia": [
            {"id": "Realia-1", "realiaId": LAMASSU_ID, "span": ["Word-2"]},
            {"id": "Realia-2", "realiaId": APKALLU_ID, "span": ["Word-7"]},
        ],
    }

    post_result = client.simulate_post(url, json=payload)

    assert post_result.status == falcon.HTTP_OK
    assert post_result.json["realiaInfo"] == [
        {"realiaId": APKALLU_ID, "lemma": "Apkallu", "type": ["Divine names"]},
        {"realiaId": LAMASSU_ID, "lemma": "Lamassu", "type": ["Object names"]},
    ]

    get_result = client.simulate_get(f"/fragments/{fragment.number}")
    assert post_result.json["realiaInfo"] == get_result.json["realiaInfo"]


def test_write_response_realia_info_empty_without_realia(
    client, fragmentarium, realia_repository
):
    store_realia(realia_repository, APKALLU_ID, "Apkallu", ["Divine names"])
    fragment = TransliteratedFragmentFactory.build().set_token_ids()
    fragmentarium.create(fragment)
    url = f"/fragments/{fragment.number}/named-entities"

    post_result = client.simulate_post(url, json={"namedEntities": [], "realia": []})

    assert post_result.status == falcon.HTTP_OK
    assert post_result.json["realiaInfo"] == []
