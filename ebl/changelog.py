import datetime
from dictdiffer import diff

from ebl.mongo_repository import MongoRepository


def create_entry(user_profile, resource_type, resource_id, diff):
    return {
        'user_profile': user_profile,
        'resource_type': resource_type,
        'resource_id': resource_id,
        'date': datetime.datetime.utcnow().isoformat(),
        'diff':  diff
    }


class Changelog:
    # pylint: disable=R0903

    def __init__(self, database):
        self._repository = MongoRepository(database, 'changelog')

    def create(self, resource_type, user_profile, old, new):
        entry = create_entry(
            user_profile,
            resource_type,
            old['_id'],
            list(diff(old, new))
        )
        return self._repository.create(entry)
