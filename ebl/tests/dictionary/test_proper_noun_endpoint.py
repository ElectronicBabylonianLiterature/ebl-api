import json
import attr
import pytest
import falcon

from falcon import testing
from falcon_auth import JWTAuthBackend, NoneAuthBackend

import ebl.app
from ebl.dictionary.application.dictionary_service import Dictionary
from ebl.users.infrastructure.auth0 import Auth0User


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
        body = json.dumps({"lemma": "Marduk", "namedEntityTags": ["DN"]})
        result = create_proper_noun_client.simulate_post(
            "/words/create-proper-noun", body=body
        )

        assert result.status == falcon.HTTP_CREATED
        assert result.json["_id"] == "Marduk I"
        assert result.json["lemma"] == ["Marduk"]
        assert result.json["homonym"] == "I"
        assert result.json["pos"] == []
        assert result.json["namedEntityTags"] == ["DN"]
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

    def test_create_proper_noun_with_empty_tags(
        self, create_proper_noun_client
    ) -> None:
        body = json.dumps({"lemma": "Ishtar"})
        result = create_proper_noun_client.simulate_post(
            "/words/create-proper-noun", body=body
        )

        assert result.status == falcon.HTTP_CREATED
        assert result.json["pos"] == []
        assert result.json["namedEntityTags"] == []

    def test_create_proper_noun_with_multiple_tags(
        self, create_proper_noun_client
    ) -> None:
        body = json.dumps({"lemma": "Ninurta", "namedEntityTags": ["DN", "GN"]})
        result = create_proper_noun_client.simulate_post(
            "/words/create-proper-noun", body=body
        )

        assert result.status == falcon.HTTP_CREATED
        assert result.json["pos"] == []
        assert result.json["namedEntityTags"] == ["DN", "GN"]

    def test_create_proper_noun_missing_lemma(self, create_proper_noun_client) -> None:
        body = json.dumps({"namedEntityTags": ["DN"]})
        result = create_proper_noun_client.simulate_post(
            "/words/create-proper-noun", body=body
        )

        assert result.status == falcon.HTTP_BAD_REQUEST

    def test_create_proper_noun_empty_lemma(self, create_proper_noun_client) -> None:
        body = json.dumps({"lemma": "", "namedEntityTags": ["DN"]})
        result = create_proper_noun_client.simulate_post(
            "/words/create-proper-noun", body=body
        )

        assert result.status == falcon.HTTP_BAD_REQUEST

    def test_create_proper_noun_tags_not_list(self, create_proper_noun_client) -> None:
        body = json.dumps({"lemma": "Marduk", "namedEntityTags": "DN"})
        result = create_proper_noun_client.simulate_post(
            "/words/create-proper-noun", body=body
        )

        assert result.status == falcon.HTTP_BAD_REQUEST

    def test_create_proper_noun_tags_has_non_string_values(
        self, create_proper_noun_client
    ) -> None:
        body = json.dumps({"lemma": "Marduk", "namedEntityTags": ["DN", 123]})
        result = create_proper_noun_client.simulate_post(
            "/words/create-proper-noun", body=body
        )

        assert result.status == falcon.HTTP_BAD_REQUEST

    def test_create_proper_noun_duplicate(self, create_proper_noun_client) -> None:
        body = json.dumps({"lemma": "Marduk", "namedEntityTags": ["DN"]})
        create_proper_noun_client.simulate_post("/words/create-proper-noun", body=body)
        result = create_proper_noun_client.simulate_post(
            "/words/create-proper-noun", body=body
        )

        assert result.status == falcon.HTTP_CONFLICT

    def test_create_proper_noun_missing_scope(self, client) -> None:
        body = json.dumps({"lemma": "Marduk", "namedEntityTags": ["DN"]})
        result = client.simulate_post("/words/create-proper-noun", body=body)

        assert result.status == falcon.HTTP_FORBIDDEN

    def test_create_proper_noun_missing_auth_token(self, unauthorized_client) -> None:
        body = json.dumps({"lemma": "Marduk", "namedEntityTags": ["DN"]})
        result = unauthorized_client.simulate_post(
            "/words/create-proper-noun", body=body
        )

        assert result.status == falcon.HTTP_UNAUTHORIZED

    def test_create_proper_noun_invalid_auth_token(self, unauthorized_client) -> None:
        body = json.dumps({"lemma": "Marduk", "namedEntityTags": ["DN"]})
        result = unauthorized_client.simulate_post(
            "/words/create-proper-noun",
            body=body,
            headers={"Authorization": "Bearer invalid"},
        )

        assert result.status == falcon.HTTP_UNAUTHORIZED

    def test_create_proper_noun_response_content_type(
        self, create_proper_noun_client
    ) -> None:
        body = json.dumps({"lemma": "Marduk", "namedEntityTags": ["DN"]})
        result = create_proper_noun_client.simulate_post(
            "/words/create-proper-noun", body=body
        )

        assert result.headers["Content-Type"] == "application/json"

    def test_create_proper_noun_response_id_matches_word_id(
        self, create_proper_noun_client
    ) -> None:
        body = json.dumps({"lemma": "Shamash", "namedEntityTags": ["DN"]})
        result = create_proper_noun_client.simulate_post(
            "/words/create-proper-noun", body=body
        )

        assert result.json["_id"] == "Shamash I"

    def test_create_proper_noun_rejects_unknown_fields(
        self, create_proper_noun_client
    ) -> None:
        body = json.dumps(
            {"lemma": "Marduk", "namedEntityTags": ["DN"], "extra": "value"}
        )
        result = create_proper_noun_client.simulate_post(
            "/words/create-proper-noun", body=body
        )

        assert result.status == falcon.HTTP_BAD_REQUEST

    def test_create_proper_noun_preserves_lemma_case(
        self, create_proper_noun_client
    ) -> None:
        body = json.dumps({"lemma": "MaRdUk", "namedEntityTags": ["DN"]})
        result = create_proper_noun_client.simulate_post(
            "/words/create-proper-noun", body=body
        )

        assert result.json["lemma"] == ["MaRdUk"]

    def test_create_proper_noun_success_payload_has_required_shape(
        self, create_proper_noun_client
    ) -> None:
        body = json.dumps({"lemma": "Adad", "namedEntityTags": ["DN"]})
        result = create_proper_noun_client.simulate_post(
            "/words/create-proper-noun", body=body
        )

        assert result.status == falcon.HTTP_CREATED
        assert result.json is not None
        assert isinstance(result.json["_id"], str)
        assert isinstance(result.json["lemma"], list)
        assert all(isinstance(lemma, str) for lemma in result.json["lemma"])
        assert isinstance(result.json["pos"], list)
        assert isinstance(result.json["namedEntityTags"], list)
        assert all(isinstance(tag, str) for tag in result.json["namedEntityTags"])

    def test_create_proper_noun_returns_500_when_created_word_not_found(
        self, create_proper_noun_client, monkeypatch
    ) -> None:
        monkeypatch.setattr(Dictionary, "find", lambda _self, _word_id: None)
        body = json.dumps({"lemma": "Dagan", "namedEntityTags": ["DN"]})

        result = create_proper_noun_client.simulate_post(
            "/words/create-proper-noun", body=body
        )

        assert result.status == falcon.HTTP_INTERNAL_SERVER_ERROR

    def test_create_proper_noun_returns_500_when_create_returns_invalid_id(
        self, create_proper_noun_client, monkeypatch
    ) -> None:
        monkeypatch.setattr(
            Dictionary,
            "create_proper_noun",
            lambda _self, _lemma, _tags: None,
        )
        body = json.dumps({"lemma": "Ea", "namedEntityTags": ["DN"]})

        result = create_proper_noun_client.simulate_post(
            "/words/create-proper-noun", body=body
        )

        assert result.status == falcon.HTTP_INTERNAL_SERVER_ERROR
