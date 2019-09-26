# Electronic Babylonian Literature API

[![Codeship Status for ElectronicBabylonianLiterature/dictionary](https://app.codeship.com/projects/6f47f4c0-454f-0136-5732-46084bd8d3ec/status?branch=master)](https://app.codeship.com/projects/291865)
[![Test Coverage](https://api.codeclimate.com/v1/badges/63fd8d8e40b2066cb42b/test_coverage)](https://codeclimate.com/github/ElectronicBabylonianLiterature/ebl-api/test_coverage)
[![Maintainability](https://api.codeclimate.com/v1/badges/63fd8d8e40b2066cb42b/maintainability)](https://codeclimate.com/github/ElectronicBabylonianLiterature/ebl-api/maintainability)

The API requires a MongoDB database. See the [dictionary-parser](https://github.com/ElectronicBabylonianLiterature/dictionary-parser) and [fragmentarium-parser](https://github.com/ElectronicBabylonianLiterature/fragmentarium-parser) for generating the initial data.

## Setup

Requirements:
- Python 3.7 & pip
- A JavaScript runtime, e.g. Node.js (Only required for running the tests using MongoDB `map_reduce`.)
- Docker (optional for running the application)

```
pip install pipenv
pipenv install --dev
```

## Running tests

```
pipenv run flake8
pipenv run mypy -p ebl
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

Sentry:
- `SENTRY_DSN`
- `SENTRY_ENVIRONMENT`

For docker compose with DB:

Create a script to create the MongoDB user in `./docker-entrypoint-initdb.d/create-users.js`:

```
db.createUser(
  {
    user: "ebl-api",
    pwd: "<password>",
    roles: [
       { role: "readWrite", db: "ebl" }
    ]
  }
)
```

- `MONGODB_URI` use `mongodb://ebl-api:<password>@mongo:27017/ebl`
- `MONGO_INITDB_ROOT_USERNAME`
- `MONGO_INITDB_ROOT_PASSWORD`
- `MONGOEXPRESS_LOGIN`
- `MONGOEXPRESS_PASSWORD`

### The API image

Build and run the API image:
```
docker build -t ebl/api . 
docker run -p 8000:8000 --rm -it --env-file=FILE --name ebl-api ebl/api
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

Run the full backend including the database and admin interface:
```
docker-compose up
```


## Updating transliterations and signs in fragments

Improving the parser can lead to existing transliterations to have obsolete tokens or becoming invalid.
The signs are calculated when a fragment is saved, but if the sign list is updated the fragments are not automatically updated.

The `ebl.fragmentarium.update_fragments` module can be used to recreate transliteratioin and signs in all fragments. A list of invalid
fragments is saved to `invalid_fragments.tsv`.

```
pipenv run  python -m ebl.fragmentarium.update_fragments
```

## Updating transliterations in fragments



## Type hints

It is not mandatory to use type hints, but try to use them whenever possible, especially in the domain model.

Type checks can be run with `mypy`:
```
pipenv run mypy -p ebl
```

## Acknowledgements

CSL-JSON schema is based on [citation-style-language/schema](https://github.com/citation-style-language/schema)
Copyright (c) 2007-2018 Citation Style Language and contributors. Licensed under MIT License.
