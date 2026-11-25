import os
import sys

pytest_plugins = [
    "ebl.tests.fixtures.repository_fixtures",
    "ebl.tests.fixtures.service_fixtures",
    "ebl.tests.fixtures.file_fixtures",
    "ebl.tests.fixtures.data_fixtures",
    "ebl.tests.fixtures.context_fixtures",
]

production_dbs = ["ebl", "ebldev"]
current_db = os.environ.get("MONGODB_DB")

if current_db in production_dbs:
    print(
        f"\n{'=' * 80}\n"
        f"⚠️  PRODUCTION DATABASE DETECTED: MONGODB_DB='{current_db}'\n"
        f"{'=' * 80}\n"
        f"\n"
        f"For safety, automatically unsetting production environment variables.\n"
        f"Tests will use an isolated in-memory database instead.\n"
        f"\n"
        f"Production databases {production_dbs} are NEVER used in tests.\n"
        f"{'=' * 80}\n",
        file=sys.stderr,
    )
    if "MONGODB_DB" in os.environ:
        del os.environ["MONGODB_DB"]
    if "MONGODB_URI" in os.environ:
        del os.environ["MONGODB_URI"]
