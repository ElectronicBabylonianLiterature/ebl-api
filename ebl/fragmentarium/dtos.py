def create_response_dto(fragment, user):
    return {
        **fragment.to_dict_for(user),
        'atf': fragment.text.atf
    }
