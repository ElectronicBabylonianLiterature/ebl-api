import pytest

from marshmallow import ValidationError

from ebl.dictionary.application.word_schema import ProperNounCreationRequestSchema
from ebl.errors import DuplicateError


class TestProperNounCreationRequestSchema:
    @pytest.fixture
    def schema(self):
        return ProperNounCreationRequestSchema()

    def test_schema_accepts_valid_lemma_and_tags(self, schema):
        data = {"lemma": "Marduk", "namedEntityTags": ["DN"]}
        result = schema.load(data)
        assert result == {"lemma": "Marduk", "namedEntityTags": ["DN"]}

    def test_schema_accepts_valid_lemma_with_empty_tags(self, schema):
        data = {"lemma": "Marduk", "namedEntityTags": []}
        result = schema.load(data)
        assert result == {"lemma": "Marduk", "namedEntityTags": []}

    def test_schema_rejects_missing_lemma(self, schema):
        data = {"namedEntityTags": ["DN"]}
        with pytest.raises(ValidationError) as exc_info:
            schema.load(data)
        assert "lemma" in exc_info.value.messages

    def test_schema_rejects_empty_lemma_string(self, schema):
        data = {"lemma": "", "namedEntityTags": ["DN"]}
        with pytest.raises(ValidationError) as exc_info:
            schema.load(data)
        assert "lemma" in exc_info.value.messages

    def test_schema_rejects_tags_that_are_not_a_list(self, schema):
        data = {"lemma": "Marduk", "namedEntityTags": "DN"}
        with pytest.raises(ValidationError) as exc_info:
            schema.load(data)
        assert "namedEntityTags" in exc_info.value.messages

    def test_schema_rejects_tags_with_non_string_values(self, schema):
        data = {"lemma": "Marduk", "namedEntityTags": ["DN", 123]}
        with pytest.raises(ValidationError) as exc_info:
            schema.load(data)
        assert "namedEntityTags" in exc_info.value.messages

    def test_schema_accepts_tags_with_multiple_values(self, schema):
        data = {"lemma": "Marduk", "namedEntityTags": ["DN", "GN", "PN"]}
        result = schema.load(data)
        assert result == {"lemma": "Marduk", "namedEntityTags": ["DN", "GN", "PN"]}

    def test_schema_deserialization_produces_correct_structure(self, schema):
        data = {"lemma": "Ishtar", "namedEntityTags": ["DN"]}
        result = schema.load(data)
        assert isinstance(result, dict)
        assert "lemma" in result
        assert "namedEntityTags" in result
        assert isinstance(result["namedEntityTags"], list)
        assert all(isinstance(tag, str) for tag in result["namedEntityTags"])

    def test_schema_defaults_tags_to_empty_list_when_omitted(self, schema):
        data = {"lemma": "Marduk"}
        result = schema.load(data)
        assert result == {"lemma": "Marduk", "namedEntityTags": []}

    def test_schema_dumps_data_correctly(self, schema):
        data = {"lemma": "Marduk", "namedEntityTags": ["DN"]}
        loaded = schema.load(data)
        dumped = schema.dump(loaded)
        assert dumped == {"lemma": "Marduk", "namedEntityTags": ["DN"]}


class TestMongoWordRepositoryCreateProperNoun:
    COLLECTION = "words"

    def test_create_proper_noun_successful_creation(self, database, word_repository):
        word_id = word_repository.create_proper_noun("Marduk", ["DN"])

        assert word_id == "Marduk I"
        created_word = database[self.COLLECTION].find_one({"_id": word_id})
        assert created_word is not None

    def test_create_proper_noun_document_structure(self, database, word_repository):
        word_id = word_repository.create_proper_noun("Marduk", ["DN"])

        created_word = database[self.COLLECTION].find_one({"_id": word_id})
        assert created_word["_id"] == "Marduk I"
        assert created_word["lemma"] == ["Marduk"]
        assert created_word["homonym"] == "I"
        assert created_word["pos"] == []
        assert created_word["namedEntityTags"] == ["DN"]
        assert created_word["attested"] is True
        assert created_word["meaning"] == ""
        assert created_word["legacyLemma"] == "Marduk"
        assert created_word["guideWord"] == "Marduk"
        assert created_word["arabicGuideWord"] == ""
        assert created_word["origin"] == ["EBL"]

    def test_create_proper_noun_empty_collections(self, database, word_repository):
        word_id = word_repository.create_proper_noun("Ishtar", [])

        created_word = database[self.COLLECTION].find_one({"_id": word_id})
        assert created_word["forms"] == []
        assert created_word["logograms"] == []
        assert created_word["derived"] == []
        assert created_word["derivedFrom"] is None
        assert created_word["amplifiedMeanings"] == []
        assert created_word["oraccWords"] == []
        assert created_word["roots"] == []

    def test_create_proper_noun_with_single_tag(self, database, word_repository):
        word_id = word_repository.create_proper_noun("Shamash", ["DN"])

        created_word = database[self.COLLECTION].find_one({"_id": word_id})
        assert created_word["pos"] == []
        assert created_word["namedEntityTags"] == ["DN"]

    def test_create_proper_noun_with_empty_tags(self, database, word_repository):
        word_id = word_repository.create_proper_noun("Enlil", [])

        created_word = database[self.COLLECTION].find_one({"_id": word_id})
        assert created_word["pos"] == []
        assert created_word["namedEntityTags"] == []

    def test_create_proper_noun_id_format(self, word_repository):
        word_id = word_repository.create_proper_noun("Anu", ["DN"])

        assert word_id == "Anu I"
        parts = word_id.split(" ")
        assert len(parts) == 2
        assert parts[0] == "Anu"
        assert parts[1] == "I"

    def test_create_proper_noun_duplicate_lemma_raises_error(
        self, database, word_repository
    ):
        word_repository.create_proper_noun("Marduk", ["DN"])

        with pytest.raises(DuplicateError):
            word_repository.create_proper_noun("Marduk", ["DN"])

    def test_create_proper_noun_with_multiple_tags(self, database, word_repository):
        word_id = word_repository.create_proper_noun("Ninurta", ["DN", "GN"])

        created_word = database[self.COLLECTION].find_one({"_id": word_id})
        assert created_word["namedEntityTags"] == ["DN", "GN"]

    def test_create_proper_noun_special_characters_in_lemma(
        self, database, word_repository
    ):
        word_id = word_repository.create_proper_noun("Ninurta-par", ["PN"])

        assert word_id == "Ninurta-par I"
        created_word = database[self.COLLECTION].find_one({"_id": word_id})
        assert created_word["lemma"] == ["Ninurta-par"]

    def test_create_proper_noun_preserves_lemma_case(self, database, word_repository):
        word_id = word_repository.create_proper_noun("Marduk", ["DN"])

        created_word = database[self.COLLECTION].find_one({"_id": word_id})
        assert created_word["lemma"] == ["Marduk"]
        assert created_word["guideWord"] == "Marduk"
        assert created_word["legacyLemma"] == "Marduk"

    def test_create_proper_noun_returns_word_id(self, word_repository):
        word_id = word_repository.create_proper_noun("Anu", ["DN"])

        assert isinstance(word_id, str)
        assert word_id == "Anu I"


class TestDictionaryCreateProperNoun:
    def test_delegation_to_repository(self, dictionary, word_repository):
        word_id = dictionary.create_proper_noun("Marduk", ["DN"])

        assert word_id == "Marduk I"
        retrieved_word = word_repository.query_by_id(word_id)
        assert retrieved_word is not None
        assert retrieved_word["lemma"] == ["Marduk"]

    def test_return_value_is_word_id(self, dictionary):
        word_id = dictionary.create_proper_noun("Shamash", ["DN"])

        assert isinstance(word_id, str)
        assert word_id == "Shamash I"

    def test_with_empty_tags(self, dictionary, word_repository):
        word_id = dictionary.create_proper_noun("Enlil", [])

        retrieved_word = word_repository.query_by_id(word_id)
        assert retrieved_word["pos"] == []
        assert retrieved_word["namedEntityTags"] == []

    def test_with_multiple_tags(self, dictionary, word_repository):
        word_id = dictionary.create_proper_noun("Ninurta", ["DN", "GN"])

        retrieved_word = word_repository.query_by_id(word_id)
        assert retrieved_word["namedEntityTags"] == ["DN", "GN"]

    def test_service_returns_exact_word_id_from_repository(self, dictionary):
        service_result = dictionary.create_proper_noun("Anu", ["DN"])

        assert service_result == "Anu I"

    def test_repository_exceptions_propagate(self, dictionary):
        dictionary.create_proper_noun("Marduk", ["DN"])

        with pytest.raises(DuplicateError):
            dictionary.create_proper_noun("Marduk", ["DN"])
