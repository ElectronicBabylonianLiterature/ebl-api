#import subprocess
from waitress import serve
from ebl.app import get_app

# Make .prof file:
# python -m cProfile -o application.prof profile_run.py
# poetry run py-spy 

# check running proccesses:
# ps aux

# sudo -E RUST_BACKTRACE=full /workspace/ebl-api/.venv/bin/py-spy top -s poetry run /workspace/ebl-api/.venv/bin/python3 profile_run.py

# sudo py-spy top -s poetry run python3 profile_run.py

# sudo -E RUST_BACKTRACE=full /workspace/ebl-api/.venv/bin/py-spy top -s /workspace/ebl-api/.venv/bin/poetry run /workspace/ebl-api/.venv/bin/python3 profile_run.py

# sudo env "PATH=$PATH RUST_BACKTRACE=full" /workspace/ebl-api/.venv/bin/py-spy top -s poetry run /workspace/ebl-api/.venv/bin/python3 profile_run.py

# sudo env "PATH=$PATH RUST_BACKTRACE=full" /workspace/ebl-api/.venv/bin/py-spy top -s poetry run /workspace/ebl-api/.venv/bin/python3 profile_run.py

# sudo env "PATH=$PATH" py-spy top -s poetry run /workspace/ebl-api/.venv/bin/python3 profile_run.py

if __name__ == "__main__":
    pass
    serve(get_app(), port=8000)
#    while True:
#        print('--')
#    subprocess.call(
#        ["poetry", "run", "waitress-serve", "--port=8000", "--call", "ebl.app:get_app"]
#    )
