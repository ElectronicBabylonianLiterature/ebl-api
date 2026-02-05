#!/usr/bin/env python3
"""
Single-Pass ATF Importer with Interactive Lemmatization

This script runs the import in one pass, prompting for unknown lemmata
as they are encountered. New lemma mappings are immediately saved to
the JSON file and reused when the same lemma+guideword appears again.

IMPORTANT: Run this script with poetry to ensure database access:
    cd /workspaces/ebl-api
    poetry run python ebl/atf_importer/runner/interactive_import_onepass.py
"""

import subprocess
import sys
import re
import os
import json
import threading
import queue

# Lookup table: key = "lemma|guideword", value = eBL lemma id
LEMMA_LOOKUP = {}

LOOKUP_FILE = "ebl/atf_importer/runner/missing_lemmata.json"


def load_saved_lemmas():
    """Load previously saved lemmata from file"""
    if os.path.exists(LOOKUP_FILE):
        try:
            with open(LOOKUP_FILE, "r") as f:
                saved = json.load(f)
                LEMMA_LOOKUP.update(saved)
                print(
                    f"✅ Loaded {len(saved)} saved lemma mappings from previous sessions"
                )
        except Exception as e:
            print(f"⚠️  Warning: Could not load saved lemmata: {e}")


def save_lemma(key, value):
    """Save a single lemma mapping immediately to file"""
    LEMMA_LOOKUP[key] = value
    try:
        with open(LOOKUP_FILE, "w") as f:
            json.dump(LEMMA_LOOKUP, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️  Warning: Could not save lemma: {e}")


def extract_lemma_info(text):
    """Extract lemma information from prompt text"""
    lemma_match = re.search(r"lemma: '([^']+)'", text)
    trans_match = re.search(r"Transliteration: '([^']+)'", text)
    guide_match = re.search(r"guide word: '([^']+)'", text)
    pos_match = re.search(r"POS: '([^']+)'", text)

    return {
        "lemma": lemma_match.group(1) if lemma_match else None,
        "transliteration": trans_match.group(1) if trans_match else None,
        "guideword": guide_match.group(1) if guide_match else None,
        "pos": pos_match.group(1) if pos_match else None,
    }


def make_lookup_key(lemma, guideword):
    """Create composite key for lemma lookup"""
    return f"{lemma}|{guideword}"


def verify_lemma_id(lemma_id):
    """Verify that a lemma ID exists in the database"""
    if not lemma_id:
        return True  # Empty is valid (means skip)

    # Import here to avoid loading MongoDB unless needed
    from pymongo import MongoClient

    mongo_url = os.getenv("MONGODB_URI")
    db_name = os.getenv("MONGODB_DB", "ebl")

    if not mongo_url:
        print("  ⚠️  Warning: MONGODB_URI not set, skipping verification")
        return True

    try:
        client = MongoClient(mongo_url)
        db = client[db_name]

        cursor = db.get_collection("words").aggregate(
            [{"$match": {"_id": lemma_id}}, {"$project": {"_id": 1}}]
        )

        result = len(list(cursor)) > 0
        client.close()
        return result
    except Exception as e:
        print(f"  ⚠️  Warning: Could not verify lemma ID: {e}")
        return True  # Allow it if we can't verify


def prompt_for_lemma_with_verification(info):
    """Prompt for a single lemma with verification, retry if invalid"""
    print(f"\n{'=' * 70}")
    print(f"UNKNOWN LEMMA ENCOUNTERED")
    print(f"{'=' * 70}")
    print(f"  Lemma: {info['lemma']}")
    print(f"  Transliteration: {info['transliteration']}")
    print(f"  Guide word: {info['guideword']}")
    print(f"  POS: {info['pos']}")
    print(f"{'=' * 70}")

    while True:
        print(f"  Enter eBL lemma ID (e.g., 'bītu I') or press Enter to skip:")
        print(f"  > ", end="", flush=True)

        answer = input().strip()

        # Verify the answer
        if verify_lemma_id(answer):
            if answer:
                print(
                    f"  ✅ Verified and saved: {info['lemma']} [{info['guideword']}] → {answer}"
                )
            else:
                print(f"  ⊘ Will skip: {info['lemma']} [{info['guideword']}]")
            return answer
        else:
            print(
                f"  ❌ Lemma id '{answer}' is not found in the eBL database. Please try again."
            )


def is_generic_prompt(buffer):
    """Detect if buffer contains a generic prompt waiting for user input"""
    # Look for explicit prompt patterns
    patterns = [
        r"press enter:",
        r"then press enter:",
        r"Please enter",
        r"Enter the",
        r"provide your input",
        r"type your",
    ]

    for pattern in patterns:
        if re.search(pattern, buffer, re.IGNORECASE):
            # Make sure it's not just a log line - check if the pattern appears
            # in the last few lines (not buried in earlier log output)
            lines = buffer.strip().split("\n")
            last_lines = "\n".join(lines[-10:])
            if re.search(pattern, last_lines, re.IGNORECASE):
                return True

    return False


def enqueue_output(out, queue):
    """Read output from process and put it in a queue"""
    for char in iter(lambda: out.read(1), ""):
        queue.put(char)
    out.close()


def run_import():
    """Run the import with real-time lemma resolution"""
    print("\n" + "=" * 70)
    print("ATF IMPORTER - SINGLE-PASS INTERACTIVE MODE")
    print("=" * 70 + "\n")

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    cmd = [
        "poetry",
        "run",
        "python",
        "-u",
        "-m",
        "ebl.atf_importer.application.atf_importer",
        "-i",
        "ebl/atf_importer/runner/data/",
        "-l",
        "ebl/atf_importer/runner/data/logs/",
        "-g",
        "ebl/atf_importer/runner/data/",
        "-a",
        "Sachs/Hunger",
    ]

    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=0,
        cwd="/workspaces/ebl-api",
        env=env,
    )

    # Use a queue to read output in a non-blocking way
    q = queue.Queue()
    t = threading.Thread(target=enqueue_output, args=(process.stdout, q))
    t.daemon = True
    t.start()

    buffer = ""
    prompt_count = 0
    new_lemmas_count = 0
    imported_texts = {}  # Use dict to avoid duplicates: key = museum_number, value = filename
    no_output_cycles = 0
    processed_lines = set()  # Track which success messages we've already processed

    try:
        while True:
            # Try to get output from queue with timeout
            try:
                char = q.get(timeout=0.1)
                sys.stdout.write(char)
                sys.stdout.flush()
                buffer += char
                no_output_cycles = 0
            except queue.Empty:
                # No output for 0.1 seconds
                no_output_cycles += 1

                # Check if process has finished
                if process.poll() is not None:
                    break

                # After 3 cycles (0.3s) of no output, check for prompts
                if no_output_cycles >= 3 and len(buffer) > 0:
                    # Check for prompts that might be waiting
                    if (
                        "Manually enter the eBL lemma id" in buffer
                        and not buffer.endswith("\n")
                    ):
                        pass  # Will be handled below
                    elif (
                        "Answer with 'Y'(es) / 'N'(o)" in buffer
                        and not buffer.endswith("\n")
                    ):
                        pass  # Will be handled below
                    elif is_generic_prompt(buffer) and not buffer.endswith("\n"):
                        pass  # Will be handled below
                    else:
                        continue
                else:
                    continue

            # Track successful imports - pattern: "filename.atf successfully imported as MUSEUM.NUMBER"
            # Only process complete lines (those that have been terminated with \n)
            if "\n" in buffer and "successfully imported as" in buffer:
                # Split and only process lines that were complete (all but the last one if buffer doesn't end with \n)
                lines = buffer.split("\n")
                # If buffer doesn't end with \n, the last element is incomplete
                complete_lines = lines[:-1] if not buffer.endswith("\n") else lines

                for line in complete_lines:
                    if (
                        "successfully imported as" in line
                        and line not in processed_lines
                    ):
                        # Match complete museum numbers at end of line
                        import_match = re.search(
                            r"([^/\s]+\.atf) successfully imported as ([A-Z]+(?:\.\d+)+[A-Z]*)$",
                            line.strip(),
                        )
                        if import_match:
                            imported_file = import_match.group(1)
                            imported_museum_number = import_match.group(2)
                            imported_texts[imported_museum_number] = imported_file
                            processed_lines.add(line)

            # Handle specific lemma prompt
            if "Manually enter the eBL lemma id" in buffer and (
                buffer.endswith("\n") or no_output_cycles >= 3
            ):
                info = extract_lemma_info(buffer)
                lemma = info["lemma"]
                guideword = info["guideword"]

                if not lemma or not guideword:
                    print(
                        f"⚠️  Warning: Could not extract lemma or guideword, skipping",
                        flush=True,
                    )
                    process.stdin.write("\n")
                    process.stdin.flush()
                    buffer = ""
                    continue

                lookup_key = make_lookup_key(lemma, guideword)
                prompt_count += 1

                if lookup_key in LEMMA_LOOKUP:
                    # Known lemma - use saved answer
                    answer = LEMMA_LOOKUP[lookup_key]
                    if answer:
                        print(
                            f"→ Using saved mapping: {lemma} [{guideword}] → {answer}",
                            flush=True,
                        )
                    else:
                        print(
                            f"→ Using saved skip for: {lemma} [{guideword}]", flush=True
                        )
                    process.stdin.write(answer + "\n")
                    process.stdin.flush()
                else:
                    # Unknown lemma - prompt user and save immediately
                    answer = prompt_for_lemma_with_verification(info)
                    save_lemma(lookup_key, answer)
                    new_lemmas_count += 1
                    print(
                        f"💾 Saved to lookup file (total: {len(LEMMA_LOOKUP)} mappings)\n",
                        flush=True,
                    )

                    process.stdin.write(answer + "\n")
                    process.stdin.flush()

                buffer = ""
                no_output_cycles = 0

            # Handle Y/N prompt
            elif "Answer with 'Y'(es) / 'N'(o)" in buffer and (
                buffer.endswith("\n") or no_output_cycles >= 3
            ):
                print("→ Answering: Y", flush=True)
                process.stdin.write("Y\n")
                process.stdin.flush()
                buffer = ""
                no_output_cycles = 0

            # Handle other prompts (like lemmatization length mismatch)
            elif is_generic_prompt(buffer) and (
                buffer.endswith("\n") or no_output_cycles >= 3
            ):
                # Extract the last few lines that contain the actual prompt
                lines = buffer.strip().split("\n")
                # Get last 5 lines or fewer if buffer is shorter
                prompt_context = "\n".join(lines[-5:])

                print(f"\n{'=' * 70}", flush=True)
                print("USER INPUT REQUIRED", flush=True)
                print(f"{'=' * 70}", flush=True)
                print(prompt_context, flush=True)
                print(f"{'=' * 70}", flush=True)
                print("> ", end="", flush=True)

                user_input = input().strip()

                if user_input:
                    print(f"→ Sending: {user_input}", flush=True)
                else:
                    print(f"→ Sending blank (skip)", flush=True)

                process.stdin.write(user_input + "\n")
                process.stdin.flush()
                buffer = ""
                no_output_cycles = 0

            if len(buffer) > 2000:
                buffer = buffer[-1000:]

    except KeyboardInterrupt:
        print("\n\n⚠️  Import interrupted by user")
        process.terminate()

    process.wait()

    print(f"\n{'=' * 70}")
    print(f"IMPORT COMPLETE")
    print(f"{'=' * 70}")
    print(f"  Exit code: {process.returncode}")
    print(f"  Total prompts: {prompt_count}")
    print(f"  New lemmas added: {new_lemmas_count}")
    print(f"  Total saved mappings: {len(LEMMA_LOOKUP)}")
    print(f"  Lookup file: {LOOKUP_FILE}")
    print(f"  Imported texts: {len(imported_texts)}")

    if imported_texts:
        print(f"\n  Imported Texts:")
        for museum_number, filename in sorted(imported_texts.items()):
            print(f"    - {museum_number} (from {filename})")

    print(f"{'=' * 70}\n")


def main():
    # Load any previously saved lemmata
    load_saved_lemmas()

    # Run the import
    run_import()


if __name__ == "__main__":
    main()
