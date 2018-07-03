# dictionary

[![Codeship Status for ElectronicBabylonianLiterature/dictionary](https://app.codeship.com/projects/6f47f4c0-454f-0136-5732-46084bd8d3ec/status?branch=master)](https://app.codeship.com/projects/291865)
[![Test Coverage](https://api.codeclimate.com/v1/badges/425c3968b768ccaa0cdd/test_coverage)](https://codeclimate.com/github/ElectronicBabylonianLiterature/dictionary/test_coverage)
[![Maintainability](https://api.codeclimate.com/v1/badges/425c3968b768ccaa0cdd/maintainability)](https://codeclimate.com/github/ElectronicBabylonianLiterature/dictionary/maintainability)

Dictionary API

An API to serve a dictionary created with the [dictionary-parser](https://github.com/ElectronicBabylonianLiterature/dictionary-parser).

## Setup

```
pip install pipenv
pipenv install --dev
```

## Running tests

```
pipenv run pylint ebl tests
pipenv run pytest --cov=ebl tests
```

## Running the application

The application reads the configuration from following environment variables: `AUTH0_AUDIENCE` (the Auth0 API identifier), `AUTH0_ISSUER` (the Auth0 application domain), `AUTH0_PEM` (base64 encoded PEM certificate from the Auth0 application found under advanced settings),  and `MONGODB_URI`.

### The API image

Build and run the API image:
```
docker build -t ebl/dictionary . 
docker run -p 8000:8000 --rm -it --env-file=FILE --name dictionary-api ebl/dictionary
```

### Docker Compse

Run the full API including the database:
```
docker-compose up
```