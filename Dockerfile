# PyPy 7.3.23 is intentional: locked compiled dependencies have pp73 wheels, while PyPy 8 uses pp80.
FROM pypy:3.11-7.3.23

RUN python -m pip install "pip==26.2.1"
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"
RUN python -m pip install --retries 10 --timeout 100 "poetry==2.4.1"

EXPOSE 8000

WORKDIR /usr/src/ebl

COPY pyproject.toml ./
COPY poetry.* ./
# Retry the full install when PyPI truncates a download mid-stream.
RUN for attempt in 1 2 3; do \
      poetry install --no-root --only main && break; \
      if [ "$attempt" -eq 3 ]; then exit 1; fi; \
      sleep $((attempt * 5)); \
    done

COPY ./ebl ./ebl

COPY ./docs ./docs
RUN chmod -R a-wx ./docs

CMD ["poetry", "run", "waitress-serve", "--port=8000", "--connection-limit=500", "--max-request-body-size=67108864", "--call", "ebl.app:get_app"]
