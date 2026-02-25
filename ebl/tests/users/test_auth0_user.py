import pytest
from ebl.common.domain.scopes import Scope

from ebl.users.infrastructure.auth0 import Auth0User

PROFILE = {"name": "john"}


class ProfileFactory:
    def __init__(self, profile):
        self.count = 0
        self._profile = profile

    def create(self):
        self.count += 1
        return self._profile


def create_default_profile():
    return PROFILE


def test_has_scope():
    scope = Scope.READ_TEXTS
    other_scope = Scope.WRITE_TEXTS
    user = Auth0User({"scope": str(scope)}, create_default_profile)

    assert user.has_scope(scope) is True
    assert user.has_scope(other_scope) is False


def test_profile():
    user = Auth0User({}, create_default_profile)

    assert user.profile == PROFILE


def mock_fetch_user_info(user):
    _ = user.profile
    _ = user.profile
    _ = user.ebl_name


def test_memoize_profile():
    profile_factory = ProfileFactory(PROFILE)
    user = Auth0User({}, profile_factory.create)

    mock_fetch_user_info(user)

    assert profile_factory.count == 1


@pytest.mark.parametrize(
    "profile,expected",
    [
        ({"https://ebabylon.org/eblName": "John", "name": "john"}, "John"),
        ({"name": "john"}, "john"),
    ],
)
def test_ebl_name(profile, expected):
    user = Auth0User({}, ProfileFactory(profile).create)

    assert user.ebl_name == expected


@pytest.mark.parametrize(
    "scopes,folio_name,expected",
    [
        ("read:WGL-folios", "WGL", True),
        ("read:EVW-folios", "ARG", False),
    ],
)
def test_can_read_folio(scopes, folio_name, expected):
    user = Auth0User({"scope": scopes}, create_default_profile)

    assert user.can_read_folio(folio_name) == expected


@pytest.mark.parametrize(
    "user_scope,scopes,expected",
    [
        (
            [
                "read:CAIC-fragments",
                "read:SIPPARLIBRARY-fragments",
                "read:URUKLBU-fragments",
                "read:ITALIANNINEVEH-fragments",
            ],
            [
                "read:CAIC-fragments",
                "read:SIPPARLIBRARY-fragments",
                "read:URUKLBU-fragments",
                "read:ITALIANNINEVEH-fragments",
            ],
            True,
        ),
        (
            ["read:SIPPARLIBRARY-fragments", "read:URUKLBU-fragments"],
            ["read:CAIC-fragments", "read:ITALIANNINEVEH-fragments"],
            False,
        ),
        (["read:SIPPARLIBRARY-fragments"], ["read:CAIC-fragments"], False),
        ([], [], True),
    ],
)
def test_can_read_fragment(user_scope, scopes, expected):
    user = Auth0User({"scope": " ".join(user_scope)}, create_default_profile)
    assert (
        user.can_read_fragment([Scope.from_string(scope) for scope in scopes])
        == expected
    )


def test_get_scopes():
    user = Auth0User(
        {"scope": "read:bibliography write:texts unknown_scope_that_should_be_skipped"},
        create_default_profile,
    )
    assert user.get_scopes() == [Scope.READ_BIBLIOGRAPHY, Scope.WRITE_TEXTS]


def test_permissions_only_has_scope():
    user = Auth0User(
        {
            "scope": "openid profile offline_access",
            "permissions": ["transliterate:fragments"],
        },
        create_default_profile,
    )

    assert user.has_scope(Scope.TRANSLITERATE_FRAGMENTS) is True


def test_get_scopes_merges_and_deduplicates_scope_and_permissions():
    user = Auth0User(
        {
            "scope": "write:texts transliterate:fragments",
            "permissions": ["transliterate:fragments", "lemmatize:fragments"],
        },
        create_default_profile,
    )

    assert user.get_scopes() == [
        Scope.WRITE_TEXTS,
        Scope.TRANSLITERATE_FRAGMENTS,
        Scope.LEMMATIZE_FRAGMENTS,
    ]


def test_get_scopes_filters_permissions_by_prefix_and_suffix():
    user = Auth0User(
        {
            "permissions": [
                "read:CAIC-fragments",
                "read:WGL-folios",
                "transliterate:fragments",
            ]
        },
        create_default_profile,
    )

    assert user.get_scopes(prefix="read:", suffix="-fragments") == [
        Scope.READ_CAIC_FRAGMENTS
    ]


def test_get_scopes_ignores_unknown_and_invalid_permissions_values():
    user = Auth0User(
        {
            "scope": "write:texts",
            "permissions": [
                "unknown_scope_that_should_be_skipped",
                "annotate:fragments",
                1,
                None,
            ],
        },
        create_default_profile,
    )

    assert user.get_scopes() == [Scope.WRITE_TEXTS, Scope.ANNOTATE_FRAGMENTS]


def test_get_scopes_without_scope_claim_uses_permissions_only():
    user = Auth0User(
        {
            "permissions": ["transliterate:fragments"],
        },
        create_default_profile,
    )

    assert user.get_scopes() == [Scope.TRANSLITERATE_FRAGMENTS]
