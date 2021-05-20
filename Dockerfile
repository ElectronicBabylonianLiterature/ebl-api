FROM pypy:3.7

ENV PIPENV_VENV_IN_PROJECT 1

RUN pip install pipenv

EXPOSE 8000

WORKDIR /usr/src/ebl

COPY Pipfile* ./
RUN pipenv install --dev

COPY ./ebl ./ebl

COPY ./docs ./docs
RUN chmod -R a-wx ./docs

COPY newrelic.ini ./

CMD ["pipenv", "run", "start"]
