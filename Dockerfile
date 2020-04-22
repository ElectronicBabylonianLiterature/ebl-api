FROM pypy:3

RUN pip install pipenv

EXPOSE 8000

WORKDIR /usr/src/ebl

COPY Pipfile* ./
RUN pipenv install --dev

COPY run_tests.sh ./
RUN chmod +x ./run_tests.sh
COPY .coveragerc ./
COPY .flake8 ./
COPY mypy.ini ./
COPY ./ebl ./ebl

COPY ./docs ./docs
RUN chmod -R a-wx ./docs

CMD ["pipenv", "run", "gunicorn",  "-b :8000", "ebl.app:get_app()"]
