FROM python:3

RUN pip install pipenv

EXPOSE 8000

WORKDIR /usr/src/app

COPY Pipfile* ./
RUN pipenv install

COPY ./dictionary ./dictionary

CMD ["pipenv", "run", "gunicorn", "-b :8000", "dictionary.app:get_app()"]
