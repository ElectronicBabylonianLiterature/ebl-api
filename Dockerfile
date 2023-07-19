FROM pypy:3.9-7.3.10

RUN pip install --upgrade pip poetry

EXPOSE 8000

WORKDIR /usr/src/ebl

COPY pyproject.toml ./
COPY poetry.* ./
RUN poetry install --no-root --no-dev

COPY ./ebl ./ebl

COPY ./docs ./docs
RUN chmod -R a-wx ./docs

CMD ["poetry", "run", "waitress-serve", "--port=8000", "--call", "ebl.app:get_app"]
