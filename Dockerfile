FROM python:3

RUN pip install pipenv

EXPOSE 8000

WORKDIR /usr/src/app

COPY Pipfile* ./
RUN pipenv install
RUN pipenv install gunicorn

COPY ./dictionary ./dictionary

ARG PEM_FILE=./auth0.pem
COPY ${PEM_FILE} ./auth0.pem

CMD ["pipenv", "run", "gunicorn", "-b :8000", "dictionary.app:get_app('./auth0.pem')"]
