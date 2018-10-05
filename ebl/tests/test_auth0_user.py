import pytest
from ebl.auth0 import Auth0User


def test_has_scope():
    scope = 'scope'
    user = Auth0User({'scope': [scope]}, {})

    assert user.has_scope(scope) is True
    assert user.has_scope('other scope') is False


def test_profile():
    profile = {'name': 'john'}
    user = Auth0User({}, profile)

    assert user.profile == profile


@pytest.mark.parametrize("profile,expected", [
    ({'https://ebabylon.org/eblName': 'John', 'name': 'john'}, 'John'),
    ({'name': 'john'}, 'john')

])
def test_ebl_name(profile, expected):
    user = Auth0User({}, profile)

    assert user.ebl_name == expected
