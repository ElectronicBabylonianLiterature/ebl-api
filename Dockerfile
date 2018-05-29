FROM python:3

RUN pip install gunicorn
RUN pip install falcon

EXPOSE 8000

WORKDIR ./app

COPY . /app

CMD ["gunicorn", "-b :8000", "dictionary.app"]
