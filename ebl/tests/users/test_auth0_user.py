import pytest

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
    scope = "scope"
    user = Auth0User({"scope": scope}, create_default_profile)

    assert user.has_scope(scope) is True
    assert user.has_scope("other:scope") is False


def test_profile():
    user = Auth0User({}, create_default_profile)

    assert user.profile == PROFILE


def test_memoize_profile():
    profile_factory = ProfileFactory(PROFILE)
    user = Auth0User({}, profile_factory.create)

    user.profile
    user.profile
    user.ebl_name

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
        ("write:WGL-folios", "WGL", False),
        ("read:XXX-folios", "WGL", False),
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
            ["CAIC", "SIPPARLIBRARY", "URUKLBU", "ITALIANNINEVEH"],
            True,
        ),
        (
            ["read:SIPPARLIBRARY-fragments", "read:URUKLBU-fragments"],
            ["CAIC", "SIPPARLIBRARY", "URUKLBU", "ITALIANNINEVEH"],
            False,
        ),
        (["read:SIPPARLIBRARY-fragments"], ["CAIC"], False),
        ([], [], True),
    ],
)
def test_can_read_fragment(user_scope, scopes, expected):
    user = Auth0User({"scope": user_scope}, create_default_profile)
    assert user.can_read_fragment(scopes) == expected
