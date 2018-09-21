# Electronic Babylonian Literature API

[![Codeship Status for ElectronicBabylonianLiterature/dictionary](https://app.codeship.com/projects/6f47f4c0-454f-0136-5732-46084bd8d3ec/status?branch=master)](https://app.codeship.com/projects/291865)
[![Test Coverage](https://api.codeclimate.com/v1/badges/425c3968b768ccaa0cdd/test_coverage)](https://codeclimate.com/github/ElectronicBabylonianLiterature/dictionary/test_coverage)
[![Maintainability](https://api.codeclimate.com/v1/badges/425c3968b768ccaa0cdd/maintainability)](https://codeclimate.com/github/ElectronicBabylonianLiterature/dictionary/maintainability)

The API requires a MongoDB database. See the [dictionary-parser](https://github.com/ElectronicBabylonianLiterature/dictionary-parser) and [fragmentarium-parser](https://github.com/ElectronicBabylonianLiterature/fragmentarium-parser) for generating the initial data.

## Setup

Requirements:
- Python 3 & pip
- A JavaScript runtime, e.g. Node.js (Required for running the tests due to MongoDB `map_reduce`.)
- Docker (optional for running the application)

```
pip install pipenv
pipenv install --dev
```

## Running tests

```
pipenv run lint 
pipenv run pep8 
pipenv run test
```

## Running the application

The application reads the configuration from following environment variables: 
 - `AUTH0_AUDIENCE` (the Auth0 API identifier)
 - `AUTH0_ISSUER` (the Auth0 application domain)
 - `AUTH0_PEM` (base64 encoded PEM certificate from the Auth0 application found under advanced settings)
 - `MONGODB_URI` MongoDB connection URI with database
 
 If NewRelic is used:
- `NEW_RELIC_LICENSE_KEY`
- `NEW_RELIC_CONFIG_FILE`

### The API image

Build and run the API image:
```
docker build -t ebl/dictionary . 
docker run -p 8000:8000 --rm -it --env-file=FILE --name dictionary-api ebl/dictionary
```

### Docker Compose

Build the images:
```
docker-compose build
```

Run only the API:
```
docker-compose -f .\docker-compose-api-only.yml up
``` 

Run the full backend including the database:
```
docker-compose up
```

## Updating signs in fragments

The Fragmentarium uses the transliteration mapped to signs. The signs are calculated when a fragment is saved,
but if the sign list is updated the fragments are not automatically updated. The `ebl.fragmentarium.update_signs`
module contains functionality to update the signs in all the fragments. The module can be run from the command line:
```
python -m ebl.fragmentarium.update_signs
```

