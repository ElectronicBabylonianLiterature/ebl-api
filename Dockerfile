FROM python:3

RUN pip install pipenv

EXPOSE 8000

WORKDIR /usr/src/app

COPY Pipfile* ./
RUN pipenv install
RUN pipenv install gunicorn

COPY ./dictionary ./dictionary

ARG DICTIONARY_FILE=./tests/dictionary.json
COPY ${DICTIONARY_FILE} ./dictionary.json

CMD ["pipenv", "run", "gunicorn", "-b :8000", "dictionary.app:create_app('./dictionary.json')"]
