FROM python:3.7

RUN pip install pipenv

EXPOSE 8000

WORKDIR /usr/src/ebl

COPY Pipfile* ./
RUN pipenv install --dev

COPY .coveragerc ./
COPY mypy.ini ./
COPY run_tests.sh ./
COPY ./ebl ./ebl

CMD ["pipenv", "run", "gunicorn",  "-b :8000", "ebl.app:get_app()"]
