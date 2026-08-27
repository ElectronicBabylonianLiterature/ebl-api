from ebl.users.domain.user import ApiUser


def test_an_api_user_exposes_its_script_name_as_the_profile_name() -> None:
    user = ApiUser("update_fragments.py")

    assert user.profile == {"name": "update_fragments.py"}


def test_an_api_user_is_always_called_script() -> None:
    assert ApiUser("anything.py").ebl_name == "Script"


def test_two_api_users_keep_their_own_script_names() -> None:
    first = ApiUser("first.py")
    second = ApiUser("second.py")

    assert first.profile != second.profile
