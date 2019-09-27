import pydash


def create_mongo_entry(entry):
    return pydash.map_keys(
        entry,
        lambda _, key: '_id' if key == 'id' else key
    )


def create_object_entry(entry):
    return pydash.map_keys(
        entry,
        lambda _, key: 'id' if key == '_id' else key
    )
