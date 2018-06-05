# dictionary

[![Codeship Status for ElectronicBabylonianLiterature/dictionary](https://app.codeship.com/projects/6f47f4c0-454f-0136-5732-46084bd8d3ec/status?branch=master)](https://app.codeship.com/projects/291865)
[![Test Coverage](https://api.codeclimate.com/v1/badges/425c3968b768ccaa0cdd/test_coverage)](https://codeclimate.com/github/ElectronicBabylonianLiterature/dictionary/test_coverage)
[![Maintainability](https://api.codeclimate.com/v1/badges/425c3968b768ccaa0cdd/maintainability)](https://codeclimate.com/github/ElectronicBabylonianLiterature/dictionary/maintainability)

Dictionary API

## Setup

```
pip install pipenv
pipenv install --dev
```

## Running tests

```
pipenv run pylint dictionary tests
pipenv run pytest --cov=dictionary tests
```

## Running the application

The application requires a dictionary file in the format provided by [dictionary-parser](https://github.com/ElectronicBabylonianLiterature/dictionary-parser), a PEM certificate from Auth0 application (can be found under advanced settings) and a configuration JSON for Auth0. The configuration should contain attributes `audience` (the API identofier) and `issuer` (the application doamin).

By default filenames `dictionary.json`, `auth0.pem`, and `auth0.json` are used. If needed a custom filename can be provided via build args (e.g. `--build-arg DICTIONARY_FILE=my-dictionary.json`). See `Dockerfile` for details.

```
docker build -t ebl/dictionary . 
docker run -p 8000:8000 --rm -it --name dictionary-api ebl/dictionary
```