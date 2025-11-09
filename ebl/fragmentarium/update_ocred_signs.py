"""
Script to update ocredSigns field in fragments collection.

Usage:
    # Update from JSON file
    python -m ebl.fragmentarium.update_ocred_signs --file ocred_signs_data.json

    # Update single fragment
    python -m ebl.fragmentarium.update_ocred_signs --number "K.1" --signs "ABZ427\nABZ354"

JSON file format:
[
    {
        "filename": "BM.30000.jpg",
        "ocredSigns": "ABZ427 \\nABZ354 \\nABZ328",
        "ocredSignsCoordinates": [[x1, y1, x2, y2], ...]
    },
    {
        "filename": "BM.30009.jpg",
        "ocredSigns": "ABZ579 \\nABZ128"
    }
]

Note: Museum number is extracted from filename (e.g., "BM.30000.jpg" -> "BM.30000")
"""

import os
import argparse
import json
from typing import Dict
from tqdm import tqdm

from ebl.app import create_context
from ebl.fragmentarium.application.fragment_updater import FragmentUpdater
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.users.domain.user import ApiUser


# Fixed user for all update operations
SCRIPT_FILE_NAME =os.path.basename(__file__)


def update_ocred_signs(
    fragment_updater: FragmentUpdater,
    museum_number: MuseumNumber,
    ocred_signs: str,
) -> None:
    """Update ocredSigns field for a single fragment."""
    user = ApiUser(SCRIPT_FILE_NAME)
    try:
        fragment_updater.update_ocred_signs(museum_number, ocred_signs, user)
        return True, None
    except Exception as error:
        return False, str(error)


def parse_museum_number(number_str: str) -> MuseumNumber:
    try:
        return MuseumNumber.of(number_str)
    except Exception as error:
        raise ValueError(f"Invalid museum number: {number_str}") from error


def extract_museum_number_from_filename(filename: str) -> str:
    # Remove file extension
    if filename.endswith('.jpg') or filename.endswith('.jpeg'):
        return filename.rsplit('.jpg', 1)[0].rsplit('.jpeg', 1)[0]
    return filename


def update_from_json_file(
    fragment_updater: FragmentUpdater, json_file_path: str
) -> Dict[str, int]:
    """Update ocredSigns from a JSON file."""
    with open(json_file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    results = {"success": 0, "failed": 0, "errors": []}

    for entry in tqdm(data, desc="Updating fragments"):
        filename = entry.get("filename")
        ocred_signs = entry.get("ocredSigns", "")

        if not filename:
            results["failed"] += 1
            results["errors"].append(
                {"number": "unknown", "error": "Missing filename"}
            )
            continue

        try:
            # Extract museum number from filename
            museum_number_str = extract_museum_number_from_filename(filename)
            museum_number = parse_museum_number(museum_number_str)
            
            success, error = update_ocred_signs(
                fragment_updater, museum_number, ocred_signs
            )

            if success:
                results["success"] += 1
                print(f"✓ Updated {museum_number_str} (from {filename})")
            else:
                results["failed"] += 1
                results["errors"].append({"number": museum_number_str, "error": error})
                print(f"✗ Failed {museum_number_str} (from {filename}): {error}")

        except Exception as error:
            results["failed"] += 1
            results["errors"].append({"number": filename, "error": str(error)})
            print(f"✗ Failed {filename}: {error}")

    return results


def update_single_fragment(
    fragment_updater: FragmentUpdater, number_str: str, ocred_signs: str
) -> bool:
    """Update a single fragment's ocredSigns field."""
    try:
        museum_number = parse_museum_number(number_str)
        success, error = update_ocred_signs(
            fragment_updater, museum_number, ocred_signs
        )

        if success:
            print(f"✓ Successfully updated {number_str}")
            return True
        else:
            print(f"✗ Failed to update {number_str}: {error}")
            return False

    except Exception as error:
        print(f"✗ Error updating {number_str}: {error}")
        return False


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

    context = create_context()

    # Create the fragment updater
    fragment_updater = FragmentUpdater(
        context.fragment_repository,
        context.changelog,
        context.bibliography,
        context.photos,
        context.parallel_line_injector,
    )

    if args.file:
        print(f"Reading data from {args.file}...")
        print("Using FragmentUpdater method...")
        results = update_from_json_file(fragment_updater, args.file)

        print("\n" + "=" * 50)
        print("Update completed!")
        print(f"Success: {results['success']}")
        print(f"Failed: {results['failed']}")

        if results["errors"]:
            print("\nErrors:")
            for error_entry in results["errors"][:10]:  # Show first 10 errors
                print(f"  - {error_entry['number']}: {error_entry['error']}")

            if len(results["errors"]) > 10:
                print(f"  ... and {len(results['errors']) - 10} more errors")

    elif args.number and args.signs:
        print(f"Updating single fragment: {args.number}")
        update_single_fragment(fragment_updater, args.number, args.signs)

    else:
        parser.print_help()
        print("\nError: Please provide either --file or both --number and --signs")
