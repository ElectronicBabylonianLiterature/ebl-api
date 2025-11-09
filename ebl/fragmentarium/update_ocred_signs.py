import os
import argparse
import json
from tqdm import tqdm
from pymongo import MongoClient

from ebl.transliteration.domain.museum_number import MuseumNumber


def get_database():
    client = MongoClient(os.environ["MONGODB_URI"])
    return client.get_database(os.environ.get("MONGODB_DB"))


def update_ocred_signs(
    collection,
    museum_number: MuseumNumber,
    ocred_signs: str,
) -> tuple:
    try:
        result = collection.update_one(
            {
                "museumNumber.prefix": museum_number.prefix,
                "museumNumber.number": museum_number.number,
                "museumNumber.suffix": museum_number.suffix,
            },
            {"$set": {"ocredSigns": ocred_signs}},
        )

        if result.matched_count == 0:
            return False, "Fragment not found"

        return True, ""
    except Exception as error:
        return False, str(error)


def parse_museum_number(number_str: str) -> MuseumNumber:
    try:
        return MuseumNumber.of(number_str)
    except Exception as error:
        raise ValueError(f"Invalid museum number: {number_str}") from error


def extract_museum_number_from_filename(filename: str) -> str:
    if filename.endswith(".jpg") or filename.endswith(".jpeg"):
        return filename.rsplit(".jpg", 1)[0].rsplit(".jpeg", 1)[0]
    return filename


def update_from_json_file(collection, json_file_path: str) -> dict:
    with open(json_file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    success_count: int = 0
    failed_count: int = 0
    errors: list = []

    for entry in tqdm(data, desc="Updating fragments"):
        filename = entry.get("filename")
        ocred_signs = entry.get("ocredSigns", "")

        if not filename:
            failed_count += 1
            errors.append({"number": "unknown", "error": "Missing filename"})
            continue

        try:
            museum_number_str = extract_museum_number_from_filename(filename)
            museum_number = parse_museum_number(museum_number_str)

            is_success, error = update_ocred_signs(
                collection, museum_number, ocred_signs
            )

            if is_success:
                success_count += 1
                print(f"Updated {museum_number_str} (from {filename})")
            else:
                failed_count += 1
                errors.append({"number": museum_number_str, "error": error})
                print(f"Failed {museum_number_str} (from {filename}): {error}")

        except Exception as error:
            failed_count += 1
            errors.append({"number": filename, "error": str(error)})
            print(f"Failed {filename}: {error}")

    return {"success": success_count, "failed": failed_count, "errors": errors}


def update_single_fragment(collection, number_str: str, ocred_signs: str) -> bool:
    try:
        museum_number = parse_museum_number(number_str)
        success, error = update_ocred_signs(collection, museum_number, ocred_signs)

        if success:
            print(f"Successfully updated {number_str}")
            return True
        else:
            print(f"Failed to update {number_str}: {error}")
            return False

    except Exception as error:
        print(f"Error updating {number_str}: {error}")
        return False


def main(args):
    db = get_database()
    fragments_collection = db["fragments"]

    if args.file:
        print(f"Reading data from {args.file}...")
        print("Updating directly in MongoDB...")
        results = update_from_json_file(fragments_collection, args.file)

        print("\n" + "=" * 50)
        print("Update completed!")
        print(f"Success: {results['success']}")
        print(f"Failed: {results['failed']}")

        if results["errors"]:
            print("\nErrors:")
            for error_entry in results["errors"][:10]:
                print(f"  - {error_entry['number']}: {error_entry['error']}")

            if len(results["errors"]) > 10:
                print(f"  ... and {len(results['errors']) - 10} more errors")

    elif args.number and args.signs:
        print(f"Updating single fragment: {args.number}")
        update_single_fragment(fragments_collection, args.number, args.signs)

    else:
        parser.print_help()
        print("\nError: Please provide either --file or both --number and --signs")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Update ocredSigns field in fragments collection"
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Path to JSON file containing ocredSigns data",
    )
    parser.add_argument(
        "--number",
        type=str,
        help="Museum number for single fragment update (e.g., 'K.1')",
    )
    parser.add_argument(
        "--signs",
        type=str,
        help="OCR signs string for single fragment update",
    )

    args = parser.parse_args()
    print(args)
    main(args)
