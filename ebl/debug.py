from marshmallow import EXCLUDE

from ebl.app import create_context
from ebl.fragmentarium.application.fragment_schema import FragmentSchema

if __name__ == "__main__":
    context = create_context()
    fragment_raw = context.fragment_repository._fragments.find_one({"_id": "BM.34313"})
    fragment = FragmentSchema(unknown=EXCLUDE).load(fragment_raw)
    print()