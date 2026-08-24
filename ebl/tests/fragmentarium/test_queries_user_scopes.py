from ebl.common.domain.scopes import Scope
from ebl.fragmentarium.infrastructure.queries import match_user_scopes

UNSCOPED = [
    {"authorizedScopes": {"$exists": False}},
    {"authorizedScopes": {"$size": 0}},
]


def test_only_unscoped_fragments_match_without_user_scopes():
    assert match_user_scopes() == {"$or": UNSCOPED}


def test_user_scopes_widen_the_match():
    assert match_user_scopes([Scope.READ_CAIC_FRAGMENTS]) == {
        "$or": [*UNSCOPED, {"authorizedScopes": "read:CAIC-fragments"}]
    }


def test_every_user_scope_is_included():
    matcher = match_user_scopes(
        [Scope.READ_CAIC_FRAGMENTS, Scope.READ_COPENHAGEN_FRAGMENTS]
    )

    assert matcher["$or"][2:] == [
        {"authorizedScopes": "read:CAIC-fragments"},
        {"authorizedScopes": "read:COPENHAGEN-fragments"},
    ]


def test_a_joined_field_can_be_matched():
    field = "fragment.authorizedScopes"

    assert match_user_scopes([Scope.READ_CAIC_FRAGMENTS], field) == {
        "$or": [
            {field: {"$exists": False}},
            {field: {"$size": 0}},
            {field: "read:CAIC-fragments"},
        ]
    }


def test_a_joined_field_without_user_scopes_matches_only_unscoped():
    field = "fragment.authorizedScopes"

    assert match_user_scopes(field=field) == {
        "$or": [{field: {"$exists": False}}, {field: {"$size": 0}}]
    }
