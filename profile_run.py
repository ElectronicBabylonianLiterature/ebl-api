import os

print(os.getpid())
#os.system("poetry run waitress-serve --port=8000 --call ebl.app:get_app")
#print(os.getpid())

# python -m cProfile -o cProfile.log -m poetry run waitress-serve --port=8000 --call ebl.app:get_app

# ps -aux
# poetry run py-spy top -s -i poetry run python ./profile_run.py

import time
timeout = time.time() + 60*5   # 5 minutes from now
while True:
    test = 0
    if test == 5 or time.time() > timeout:
        break
    test -= 1

import subprocess

subprocess.call(["poetry", "run", "waitress-serve", "--port=8000", "--call", "ebl.app:get_app"])


#from ebl.app import get_app
#from waitress import serve

#if __name__ == "__main__":
#    serve(get_app, port=8000)