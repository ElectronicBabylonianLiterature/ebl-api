FROM python:3

RUN pip install pipenv

EXPOSE 8000

WORKDIR /usr/src/app

COPY Pipfile* ./
RUN pipenv install
RUN pipenv install gunicorn

COPY ./dictionary ./dictionary

ARG DICTIONARY_FILE=./dictionary.json
COPY ${DICTIONARY_FILE} ./dictionary.json

ARG PEM_FILE=./auth0.pem
COPY ${PEM_FILE} ./auth0.pem

ARG AUTH0_FILE=./auth0.json
COPY ${AUTH0_FILE} ./auth0.json

CMD ["pipenv", "run", "gunicorn", "-b :8000", "dictionary.app:get_app('./dictionary.json', './auth0.json', './auth0.pem')"]
