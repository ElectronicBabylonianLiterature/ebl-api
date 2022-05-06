import subprocess

# Make .prof file:
# python -m cProfile -o application.prof profile_run.py
# poetry run py-spy 

# check running proccesses:
# ps aux

# Vizualize file
# (install graphviz:  sudo apt install graphviz)
# poetry run gprof2dot -f pstats application.prof | dot -Tpng -o profiler_viz.png
# poetry run python -m cProfile -o poetry run python waitress-serve --port=8000 --call ebl.app:get_app

# sudo poetry run py-spy top -s poetry run .profile_run.py

# sudo /workspace/ebl-api/.venv/bin/py-spy top -s sudo /workspace/ebl-api/.venv/bin/pypy3 profile_run.py 
# sudo -E /workspace/ebl-api/.venv/bin/py-spy top -s -i poetry run /workspace/ebl-api/.venv/bin/pypy3 profile_run.py

# /workspace/ebl-api/.venv/bin/pypy3

# sudo poetry run py-spy top -p 5559

# sudo poetry run py-spy top poetry run /workspace/ebl-api/.venv/bin/pypy3 /workspace/ebl-api/.venv/bin/waitress-serve --port=8000 --call ebl.app:get_app

# (works, but no subprocesses are exposed:)
# sudo poetry run py-spy top poetry run pypi profile_run.py

if __name__ == "__main__":
    subprocess.call(
        ["poetry", "run", "waitress-serve", "--port=8000", "--call", "ebl.app:get_app"]
    )
