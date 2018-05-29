FROM python:3

RUN pip install gunicorn

EXPOSE 8000

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "-b :8000", "dictionary.app:get_app()"]
