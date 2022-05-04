import subprocess

# Make .prof file:
# python -m cProfile -o application.prof profile_run.py

# Vizualize file
# poetry run gprof2dot -f pstats application.prof | dot -Tpng -o profiler_viz.png

if __name__ == "__main__":
    subprocess.call(
        ["poetry", "run", "waitress-serve", "--port=8000", "--call", "ebl.app:get_app"]
    )
