from typing import List, Sequence, TypedDict, cast
from ebl.corpus.application.schemas import (
    ManuscriptAttestationSchema,
    UncertainFragmentAttestationSchema,
)
from ebl.corpus.domain.manuscript_attestation import ManuscriptAttestation
from ebl.corpus.domain.uncertain_fragment_attestation import (
    UncertainFragmentAttestation,
)
from ebl.corpus.infrastructure.queries import (
    join_text,
)
from ebl.transliteration.application.museum_number_schema import MuseumNumberSchema
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.corpus.infrastructure.mongo_text_repository_base import (
    MongoTextRepositoryBase,
)
from ebl.corpus.application.text_repository import CorpusFragmentsMapping


class MuseumNumberMapping(TypedDict):
    prefix: str
    number: str
    suffix: str


def get_museum_number_mappings(
    museum_numbers: Sequence[MuseumNumber],
) -> List[MuseumNumberMapping]:
    return [
        cast(
            MuseumNumberMapping,
            {
                "prefix": museum_number["prefix"],
                "number": museum_number["number"],
                "suffix": museum_number["suffix"],
            },
        )
        for museum_number in MuseumNumberSchema().dump(museum_numbers, many=True)
    ]


class MongoTextRepositoryQueryFragment(MongoTextRepositoryBase):
    def query_corpus_by_manuscripts(
        self, museum_numbers: List[MuseumNumber]
    ) -> List[ManuscriptAttestation]:
        cursor = self._chapters.aggregate(
            [
                {"$unwind": "$manuscripts"},
                {
                    "$set": {
                        "museumNumbers": {
                            "prefix": "$manuscripts.museumNumber.prefix",
                            "number": "$manuscripts.museumNumber.number",
                            "suffix": "$manuscripts.museumNumber.suffix",
                        }
                    }
                },
                {
                    "$match": {
                        "museumNumbers": {
                            "$in": get_museum_number_mappings(museum_numbers)
                        }
                    },
                },
                {
                    "$replaceRoot": {
                        "newRoot": {
                            "chapterId": {
                                "textId": "$textId",
                                "stage": "$stage",
                                "name": "$name",
                            },
                            "manuscript": "$manuscripts",
                        }
                    }
                },
                *join_text(),
                {"$unwind": "$text"},
            ]
        )
        return ManuscriptAttestationSchema(
            context={"provenance_service": self._provenance_service}
        ).load(cursor, many=True)

    def query_corpus_by_uncertain_fragments(
        self, museum_numbers: List[MuseumNumber]
    ) -> List[UncertainFragmentAttestation]:
        cursor = self._chapters.aggregate(
            [
                {"$unwind": "$uncertainFragments"},
                {
                    "$set": {
                        "museumNumbers": {
                            "prefix": "$uncertainFragments.prefix",
                            "number": "$uncertainFragments.number",
                            "suffix": "$uncertainFragments.suffix",
                        }
                    }
                },
                {
                    "$match": {
                        "museumNumbers": {
                            "$in": get_museum_number_mappings(museum_numbers)
                        }
                    },
                },
                {
                    "$replaceRoot": {
                        "newRoot": {
                            "chapterId": {
                                "textId": "$textId",
                                "stage": "$stage",
                                "name": "$name",
                            },
                        }
                    }
                },
                *join_text(),
                {"$unwind": "$text"},
            ]
        )
        return UncertainFragmentAttestationSchema(
            context={"provenance_service": self._provenance_service}
        ).load(cursor, many=True)

    def query_corpus_by_related_fragments(
        self, museum_numbers: List[MuseumNumber]
    ) -> CorpusFragmentsMapping:
        return {
            "manuscripts": self.query_corpus_by_manuscripts(museum_numbers),
            "uncertain_fragments": self.query_corpus_by_uncertain_fragments(
                museum_numbers
            ),
        }
