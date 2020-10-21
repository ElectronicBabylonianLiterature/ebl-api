FROM pypy:3

# This is needed until CDLI upgrades their servers to use a modern protocol version.
# See also https://security.googleblog.com/2018/10/modernizing-transport-security.html
RUN echo "\n[system_default_sect]\nMinProtocol = TLSv1.0" >> /etc/ssl/openssl.cnf

RUN pip install pipenv

EXPOSE 8000

WORKDIR /usr/src/ebl

COPY Pipfile* ./
RUN pipenv install --system --deploy

COPY ./ebl ./ebl

COPY ./docs ./docs
RUN chmod -R a-wx ./docs

CMD ["waitress-serve", "--port=8000", "--call", "ebl.app:get_app"]
