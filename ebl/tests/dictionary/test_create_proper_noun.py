import json
import attr
import pytest
import falcon

from falcon import testing
from falcon_auth import JWTAuthBackend, NoneAuthBackend
from marshmallow import ValidationError

import ebl.app
from ebl.dictionary.application.word_schema import ProperNounCreationRequestSchema
from ebl.users.infrastructure.auth0 import Auth0User


class TestProperNounCreationRequestSchema:
    @pytest.fixture
    def schema(self):
        return ProperNounCreationRequestSchema()

    def test_schema_accepts_valid_lemma_and_pos_tags(self, schema):
        data = {"lemma": "Marduk", "pos": ["DN"]}
        result = schema.load(data)
        assert result == {"lemma": "Marduk", "pos": ["DN"]}

    def test_schema_accepts_valid_lemma_with_empty_pos_tags(self, schema):
        data = {"lemma": "Marduk", "pos": []}
        result = schema.load(data)
        assert result == {"lemma": "Marduk", "pos": []}

    def test_schema_rejects_missing_lemma(self, schema):
        data = {"pos": ["DN"]}
        with pytest.raises(ValidationError) as exc_info:
            schema.load(data)
        assert "lemma" in exc_info.value.messages

    def test_schema_rejects_empty_lemma_string(self, schema):
        data = {"lemma": "", "pos": ["DN"]}
        with pytest.raises(ValidationError) as exc_info:
            schema.load(data)
        assert "lemma" in exc_info.value.messages

    def test_schema_rejects_pos_that_is_not_a_list(self, schema):
        data = {"lemma": "Marduk", "pos": "DN"}
        with pytest.raises(ValidationError) as exc_info:
            schema.load(data)
        assert "pos" in exc_info.value.messages

    def test_schema_rejects_pos_tags_with_non_string_values(self, schema):
        data = {"lemma": "Marduk", "pos": ["DN", 123]}
        with pytest.raises(ValidationError) as exc_info:
            schema.load(data)
        assert "pos" in exc_info.value.messages

    def test_schema_accepts_pos_tags_with_multiple_values(self, schema):
        data = {"lemma": "Marduk", "pos": ["DN", "GN", "PN"]}
        result = schema.load(data)
        assert result == {"lemma": "Marduk", "pos": ["DN", "GN", "PN"]}

    def test_schema_deserialization_produces_correct_structure(self, schema):
        data = {"lemma": "Ishtar", "pos": ["DN"]}
        result = schema.load(data)
        assert isinstance(result, dict)
        assert "lemma" in result
        assert "pos" in result
        assert isinstance(result["pos"], list)
        assert all(isinstance(pos, str) for pos in result["pos"])

    def test_schema_defaults_pos_to_empty_list_when_omitted(self, schema):
        data = {"lemma": "Marduk"}
        result = schema.load(data)
        assert result == {"lemma": "Marduk", "pos": []}

    def test_schema_dumps_data_correctly(self, schema):
        data = {"lemma": "Marduk", "pos": ["DN"]}
        loaded = schema.load(data)
        dumped = schema.dump(loaded)
        assert dumped == {"lemma": "Marduk", "pos": ["DN"]}


class TestMongoWordRepositoryCreateProperNoun:
    COLLECTION = "words"

    def test_create_proper_noun_successful_creation(self, database, word_repository):
        lemma = "Marduk"
        pos_tags = ["DN"]
        word_id = word_repository.create_proper_noun(lemma, pos_tags)

        assert word_id == "Marduk I"
        created_word = database[self.COLLECTION].find_one({"_id": word_id})
        assert created_word is not None

    def test_create_proper_noun_document_structure(self, database, word_repository):
        lemma = "Marduk"
        pos_tags = ["DN"]
        word_id = word_repository.create_proper_noun(lemma, pos_tags)

        created_word = database[self.COLLECTION].find_one({"_id": word_id})
        assert created_word["_id"] == "Marduk I"
        assert created_word["lemma"] == ["Marduk"]
        assert created_word["homonym"] == "I"
        assert created_word["pos"] == ["DN"]
        assert created_word["attested"] is True
        assert created_word["meaning"] == ""
        assert created_word["legacyLemma"] == "Marduk"
        assert created_word["guideWord"] == "Marduk"
        assert created_word["arabicGuideWord"] == ""
        assert created_word["origin"] == ["EBL"]

    def test_create_proper_noun_empty_collections(self, database, word_repository):
        lemma = "Ishtar"
        pos_tags = []
        word_id = word_repository.create_proper_noun(lemma, pos_tags)

        created_word = database[self.COLLECTION].find_one({"_id": word_id})
        assert created_word["forms"] == []
        assert created_word["logograms"] == []
        assert created_word["derived"] == []
        assert created_word["derivedFrom"] is None
        assert created_word["amplifiedMeanings"] == []
        assert created_word["oraccWords"] == []
        assert created_word["roots"] == []

    def test_create_proper_noun_with_single_pos_tag(self, database, word_repository):
        lemma = "Shamash"
        pos_tags = ["DN"]
        word_id = word_repository.create_proper_noun(lemma, pos_tags)

        created_word = database[self.COLLECTION].find_one({"_id": word_id})
        assert created_word["pos"] == ["DN"]

    def test_create_proper_noun_with_empty_pos_tags(self, database, word_repository):
        lemma = "Enlil"
        pos_tags = []
        word_id = word_repository.create_proper_noun(lemma, pos_tags)

        created_word = database[self.COLLECTION].find_one({"_id": word_id})
        assert created_word["pos"] == []

    def test_create_proper_noun_id_format(self, word_repository):
        lemma = "Anu"
        pos_tags = ["DN"]
        word_id = word_repository.create_proper_noun(lemma, pos_tags)

        assert word_id == "Anu I"
        parts = word_id.split(" ")
        assert len(parts) == 2
        assert parts[0] == lemma
        assert parts[1] == "I"

    def test_create_proper_noun_duplicate_lemma_raises_error(
        self, database, word_repository
    ):
        from ebl.errors import DuplicateError

        lemma = "Marduk"
        pos_tags = ["DN"]
        word_repository.create_proper_noun(lemma, pos_tags)

        with pytest.raises(DuplicateError):
            word_repository.create_proper_noun(lemma, pos_tags)

    def test_create_proper_noun_with_multiple_pos_tags(self, database, word_repository):
        lemma = "Ninurta"
        pos_tags = ["DN", "GN"]
        word_id = word_repository.create_proper_noun(lemma, pos_tags)

        created_word = database[self.COLLECTION].find_one({"_id": word_id})
        assert created_word["pos"] == ["DN", "GN"]

    def test_create_proper_noun_special_characters_in_lemma(
        self, database, word_repository
    ):
        lemma = "Ninurta-par"
        pos_tags = ["PN"]
        word_id = word_repository.create_proper_noun(lemma, pos_tags)

        assert word_id == "Ninurta-par I"
        created_word = database[self.COLLECTION].find_one({"_id": word_id})
        assert created_word["lemma"] == ["Ninurta-par"]

    def test_create_proper_noun_preserves_lemma_case(self, database, word_repository):
        lemma = "Marduk"
        pos_tags = ["DN"]
        word_id = word_repository.create_proper_noun(lemma, pos_tags)

        created_word = database[self.COLLECTION].find_one({"_id": word_id})
        assert created_word["lemma"] == [lemma]
        assert created_word["guideWord"] == lemma
        assert created_word["legacyLemma"] == lemma

    def test_create_proper_noun_returns_word_id(self, word_repository):
        lemma = "Anu"
        pos_tags = ["DN"]
        word_id = word_repository.create_proper_noun(lemma, pos_tags)

        assert isinstance(word_id, str)
        assert word_id == "Anu I"


class TestDictionaryCreateProperNoun:
    def test_delegation_to_repository(self, dictionary, word_repository):
        lemma = "Marduk"
        pos_tags = ["DN"]
        word_id = dictionary.create_proper_noun(lemma, pos_tags)

        assert word_id == "Marduk I"
        retrieved_word = word_repository.query_by_id(word_id)
        assert retrieved_word is not None
        assert retrieved_word["lemma"] == [lemma]

    def test_return_value_is_word_id(self, dictionary):
        lemma = "Shamash"
        pos_tags = ["DN"]
        word_id = dictionary.create_proper_noun(lemma, pos_tags)

        assert isinstance(word_id, str)
        assert word_id == "Shamash I"

    def test_with_empty_pos_tags(self, dictionary, word_repository):
        lemma = "Enlil"
        pos_tags = []
        word_id = dictionary.create_proper_noun(lemma, pos_tags)

        retrieved_word = word_repository.query_by_id(word_id)
        assert retrieved_word["pos"] == []

    def test_with_multiple_pos_tags(self, dictionary, word_repository):
        lemma = "Ninurta"
        pos_tags = ["DN", "GN"]
        word_id = dictionary.create_proper_noun(lemma, pos_tags)

        retrieved_word = word_repository.query_by_id(word_id)
        assert retrieved_word["pos"] == ["DN", "GN"]

    def test_service_returns_exact_word_id_from_repository(self, dictionary):
        lemma = "Anu"
        pos_tags = ["DN"]
        service_result = dictionary.create_proper_noun(lemma, pos_tags)

        assert service_result == "Anu I"

    def test_repository_exceptions_propagate(self, dictionary):
        from ebl.errors import DuplicateError

        lemma = "Marduk"
        pos_tags = ["DN"]
        dictionary.create_proper_noun(lemma, pos_tags)

        with pytest.raises(DuplicateError):
            dictionary.create_proper_noun(lemma, pos_tags)


class TestProperNounCreationEndpoint:
    @pytest.fixture
    def create_proper_noun_client(self, context) -> testing.TestClient:
        user = Auth0User(
            {"scope": "create:proper_nouns"},
            lambda: {
                "name": "test.user@example.com",
                "https://ebabylon.org/eblName": "User",
            },
        )
        api = ebl.app.create_app(
            attr.evolve(context, auth_backend=NoneAuthBackend(lambda: user))
        )
        return testing.TestClient(api)

    @pytest.fixture
    def unauthorized_client(self, context) -> testing.TestClient:
        def user_loader(_payload):
            return Auth0User({"scope": ""}, lambda: {"name": "Unauthorized"})

        auth_backend = JWTAuthBackend(
            user_loader,
            "secret",
            auth_header_prefix="Bearer",
        )
        api = ebl.app.create_app(attr.evolve(context, auth_backend=auth_backend))
        return testing.TestClient(api)

    def test_create_proper_noun_success(self, create_proper_noun_client) -> None:
        body = json.dumps({"lemma": "Marduk", "pos": ["DN"]})
        result = create_proper_noun_client.simulate_post(
            "/words/create-proper-noun", body=body
        )

        assert result.status == falcon.HTTP_CREATED
        assert result.json["_id"] == "Marduk I"
        assert result.json["lemma"] == ["Marduk"]
        assert result.json["homonym"] == "I"
        assert result.json["pos"] == ["DN"]
        assert result.json["attested"] is True
        assert result.json["meaning"] == ""
        assert result.json["legacyLemma"] == "Marduk"
        assert result.json["guideWord"] == "Marduk"
        assert result.json["arabicGuideWord"] == ""
        assert result.json["origin"] == ["EBL"]
        assert result.json["forms"] == []
        assert result.json["logograms"] == []
        assert result.json["derived"] == []
        assert result.json["derivedFrom"] is None
        assert result.json["amplifiedMeanings"] == []
        assert result.json["oraccWords"] == []
        assert result.json["roots"] == []

    def test_create_proper_noun_with_empty_pos(self, create_proper_noun_client) -> None:
        body = json.dumps({"lemma": "Ishtar"})
        result = create_proper_noun_client.simulate_post(
            "/words/create-proper-noun", body=body
        )

        assert result.status == falcon.HTTP_CREATED
        assert result.json["pos"] == []

    def test_create_proper_noun_with_multiple_pos(
        self, create_proper_noun_client
    ) -> None:
        body = json.dumps({"lemma": "Ninurta", "pos": ["DN", "GN"]})
        result = create_proper_noun_client.simulate_post(
            "/words/create-proper-noun", body=body
        )

        assert result.status == falcon.HTTP_CREATED
        assert result.json["pos"] == ["DN", "GN"]

    def test_create_proper_noun_missing_lemma(self, create_proper_noun_client) -> None:
        body = json.dumps({"pos": ["DN"]})
        result = create_proper_noun_client.simulate_post(
            "/words/create-proper-noun", body=body
        )

        assert result.status == falcon.HTTP_BAD_REQUEST

    def test_create_proper_noun_empty_lemma(self, create_proper_noun_client) -> None:
        body = json.dumps({"lemma": "", "pos": ["DN"]})
        result = create_proper_noun_client.simulate_post(
            "/words/create-proper-noun", body=body
        )

        assert result.status == falcon.HTTP_BAD_REQUEST

    def test_create_proper_noun_pos_not_list(self, create_proper_noun_client) -> None:
        body = json.dumps({"lemma": "Marduk", "pos": "DN"})
        result = create_proper_noun_client.simulate_post(
            "/words/create-proper-noun", body=body
        )

        assert result.status == falcon.HTTP_BAD_REQUEST

    def test_create_proper_noun_pos_has_non_string_values(
        self, create_proper_noun_client
    ) -> None:
        body = json.dumps({"lemma": "Marduk", "pos": ["DN", 123]})
        result = create_proper_noun_client.simulate_post(
            "/words/create-proper-noun", body=body
        )

        assert result.status == falcon.HTTP_BAD_REQUEST

    def test_create_proper_noun_duplicate(self, create_proper_noun_client) -> None:
        body = json.dumps({"lemma": "Marduk", "pos": ["DN"]})
        create_proper_noun_client.simulate_post("/words/create-proper-noun", body=body)
        result = create_proper_noun_client.simulate_post(
            "/words/create-proper-noun", body=body
        )

        assert result.status == falcon.HTTP_CONFLICT

    def test_create_proper_noun_missing_scope(self, client) -> None:
        body = json.dumps({"lemma": "Marduk", "pos": ["DN"]})
        result = client.simulate_post("/words/create-proper-noun", body=body)

        assert result.status == falcon.HTTP_FORBIDDEN

    def test_create_proper_noun_missing_auth_token(self, unauthorized_client) -> None:
        body = json.dumps({"lemma": "Marduk", "pos": ["DN"]})
        result = unauthorized_client.simulate_post(
            "/words/create-proper-noun", body=body
        )

        assert result.status == falcon.HTTP_UNAUTHORIZED

    def test_create_proper_noun_invalid_auth_token(self, unauthorized_client) -> None:
        body = json.dumps({"lemma": "Marduk", "pos": ["DN"]})
        result = unauthorized_client.simulate_post(
            "/words/create-proper-noun",
            body=body,
            headers={"Authorization": "Bearer invalid"},
        )

        assert result.status == falcon.HTTP_UNAUTHORIZED

    def test_create_proper_noun_response_content_type(
        self, create_proper_noun_client
    ) -> None:
        body = json.dumps({"lemma": "Marduk", "pos": ["DN"]})
        result = create_proper_noun_client.simulate_post(
            "/words/create-proper-noun", body=body
        )

        assert result.headers["Content-Type"] == "application/json"

    def test_create_proper_noun_response_id_matches_word_id(
        self, create_proper_noun_client
    ) -> None:
        body = json.dumps({"lemma": "Shamash", "pos": ["DN"]})
        result = create_proper_noun_client.simulate_post(
            "/words/create-proper-noun", body=body
        )

        assert result.json["_id"] == "Shamash I"

    def test_create_proper_noun_rejects_unknown_fields(
        self, create_proper_noun_client
    ) -> None:
        body = json.dumps({"lemma": "Marduk", "pos": ["DN"], "extra": "value"})
        result = create_proper_noun_client.simulate_post(
            "/words/create-proper-noun", body=body
        )

        assert result.status == falcon.HTTP_BAD_REQUEST

    def test_create_proper_noun_preserves_lemma_case(
        self, create_proper_noun_client
    ) -> None:
        body = json.dumps({"lemma": "MaRdUk", "pos": ["DN"]})
        result = create_proper_noun_client.simulate_post(
            "/words/create-proper-noun", body=body
        )

        assert result.json["lemma"] == ["MaRdUk"]
