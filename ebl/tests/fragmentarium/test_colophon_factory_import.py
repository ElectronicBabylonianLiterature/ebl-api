import subprocess
import sys


def test_colophon_factory_loads_in_a_fresh_interpreter() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from ebl.tests.factories.colophon import ColophonFactory; ColophonFactory.build()",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
