import pydash


def create_response_dto(fragment, user):
    return {
        **fragment.to_dict_for(user),
        'atf': fragment.text.atf
    }


def create_fragment_info_dto(fragment):
    return pydash.omit_by({
        'number':  fragment.number,
        'accession': fragment.accession,
        'script': fragment.script,
        'description': fragment.description,
        'matching_lines': fragment.matching_lines
    }, pydash.is_none)
