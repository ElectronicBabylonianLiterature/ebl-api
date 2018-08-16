import datetime
from dictdiffer import diff

from ebl.mongo_repository import MongoRepository


class Changelog:
    # pylint: disable=R0903

    def __init__(self, database):
        self._repository = MongoRepository(database, 'changelog')

    def create(self, resource_type, user, old, new):
        entry = {
            'user': user,
            'resource_type': resource_type,
            'resource_id': old['_id'],
            'date': datetime.datetime.utcnow().isoformat(),
            'diff':  list(diff(old, new))
        }
        return self._repository.create(entry)
