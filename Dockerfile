FROM python:3.7-rc

RUN pip install pipenv

EXPOSE 8000

WORKDIR /usr/src/ebl

COPY Pipfile* ./
RUN pipenv install

COPY ./ebl ./ebl

CMD ["pipenv", "run", "gunicorn", "-b :8000", "ebl.app:get_app()"]
