def create_mongo_entry(entry: dict) -> dict:
    return {("_id" if key == "id" else key): value for key, value in entry.items()}


def create_object_entry(entry: dict) -> dict:
    return {("id" if key == "_id" else key): value for key, value in entry.items()}
