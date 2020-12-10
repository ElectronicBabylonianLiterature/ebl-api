import csv

from ebl.app import create_context
from ebl.fragmentarium.application.fragment_matcher import FragmentMatcher

with open("testData.csv") as test_data:
    test_data = list(csv.reader(test_data, delimiter="\t"))

formatted_test_data = []
for entry in test_data[1:]:
    fragment_ids = entry[0].split(",")
    line_to_vec_encodings = [
        line_to_vec_encoding.split("-") for line_to_vec_encoding in entry[1].split(",")
    ]
    if len(fragment_ids) != len(line_to_vec_encodings):
        raise ValueError(f"Something wrong with the data {fragment_ids}")
    matches = dict()
    for key, values in zip(fragment_ids, line_to_vec_encodings):
        matches[key] = values
    formatted_test_data.append(matches)

print(formatted_test_data)

if __name__ == "__main__":
    context = create_context()
    fragment_matcher = FragmentMatcher(context.fragment_repository)
