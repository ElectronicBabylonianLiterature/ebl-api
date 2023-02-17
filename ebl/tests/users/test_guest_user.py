from ebl.common.domain.scopes import Scope
from ebl.users.domain.user import Guest

USER = Guest()


def test_has_scope():
    scope = Scope.WRITE_BIBLIOGRAPHY
    assert USER.has_scope(scope) is False


def test_profile():
    assert USER.profile == {"name": "Guest"}


def test_ebl_name():
    assert USER.ebl_name == "Guest"


def test_can_read_folio():
    assert USER.can_read_folio("WRM") is False
    assert USER.can_read_folio("CB") is True


def test_can_read_fragment():
    assert USER.can_read_fragment([]) is True
    assert USER.can_read_fragment([Scope.READ_CAIC_FRAGMENTS]) is False
