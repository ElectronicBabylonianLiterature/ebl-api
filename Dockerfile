FROM pypy:3.7

RUN curl -sSL https://install.python-poetry.org | python3 -

EXPOSE 8000

WORKDIR /usr/src/ebl

COPY pyproject.toml ./
COPY poetry.* ./
RUN poetry install --no-root --no-dev

COPY ./ebl ./ebl

COPY ./docs ./docs
RUN chmod -R a-wx ./docs

CMD ["poetry", "run", "waitress-serve", "--port=8000", "--call ebl.app:get_app"]
