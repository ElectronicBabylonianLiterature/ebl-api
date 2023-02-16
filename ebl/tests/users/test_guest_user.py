from ebl.users.domain.user import Guest

USER = Guest()


def test_has_scope():
    assert USER.has_scope("some:scope") is False


def test_profile():
    assert USER.profile == {"name": "Guest"}


def test_ebl_name():
    assert USER.ebl_name == "Guest"


def test_can_read_folio():
    assert USER.can_read_folio("WRM") is False
    assert USER.can_read_folio("NOT_HIDDEN") is True


def test_can_read_fragment():
    assert USER.can_read_fragment([]) is True
    assert USER.can_read_fragment(["CAIC"]) is False
