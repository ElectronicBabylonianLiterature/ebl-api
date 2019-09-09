from ebl.auth0 import User
from ebl.fragment.fragment import Fragment
from ebl.fragment.fragment_info import FragmentInfo


def create_response_dto(fragment: Fragment, user: User):
    return {
        **fragment.to_dict_for(user),
        'atf': fragment.text.atf
    }


def create_fragment_info_dto(fragment_info: FragmentInfo):
    return {
        'number':  fragment_info.number,
        'accession': fragment_info.accession,
        'script': fragment_info.script,
        'description': fragment_info.description,
        'matchingLines': [list(line)
                          for line
                          in fragment_info.matching_lines]
    }
