FROM python:3

RUN pip install gunicorn

EXPOSE 8000

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ARG DICTIONARY_FILE=./tests/dictionary.json
COPY ${DICTIONARY_FILE} ./dictionary.json

CMD ["gunicorn", "-b :8000", "dictionary.app:create_app('./dictionary.json')"]
