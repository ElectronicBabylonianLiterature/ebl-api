FROM pypy:3

# This is needed until CDLI upgrades their servers to use a modern protocol version.
# See also https://security.googleblog.com/2018/10/modernizing-transport-security.html
RUN echo -e "\n[system_default_sect]\nMinProtocol = TLSv1.0" > /etc/ssl/openssl.cnf

RUN pip install pipenv

EXPOSE 8000
nmap --script ssl-enum-ciphers -p 443 cdli.ucla.edu

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
