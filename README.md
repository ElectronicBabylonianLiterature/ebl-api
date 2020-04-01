# Electronic Babylonian Literature API

[![Build Status](https://travis-ci.com/ElectronicBabylonianLiterature/ebl-api.svg?branch=master)](https://travis-ci.com/ElectronicBabylonianLiterature/ebl-api)
[![Test Coverage](https://api.codeclimate.com/v1/badges/63fd8d8e40b2066cb42b/test_coverage)](https://codeclimate.com/github/ElectronicBabylonianLiterature/ebl-api/test_coverage)
[![Maintainability](https://api.codeclimate.com/v1/badges/63fd8d8e40b2066cb42b/maintainability)](https://codeclimate.com/github/ElectronicBabylonianLiterature/ebl-api/maintainability)

The API requires a MongoDB database. See the 
[dictionary-parser](https://github.com/ElectronicBabylonianLiterature/dictionary-parser)
and
[fragmentarium-parser](https://github.com/ElectronicBabylonianLiterature/fragmentarium-parser) 
or generating the initial data.

## Setup

Requirements:

- [PyPy3.6](https://www.pypy.org) & pip
- Docker (optional for running the application)

```shell script
pip install pipenv
pip install pyre-check
pipenv install --dev
```

## Codestyle

Line length is 88, and bugbear B950 is used instead of E501.
PEP8 checks should be enabled in PyCharm, but E501, E203, and E231 should be
disabled.

## Running the tests

```shell script
pipenv run flake8 ebl
pyre check
pipenv run test
```

## Running the application

The application reads the configuration from following environment variables:
 
 ```dotenv
AUTH0_AUDIENCE=<the Auth0 API identifier>
AUTH0_ISSUER=<the Auth0 application domain>
AUTH0_PEM=<base64 encoded PEM certificate from the Auth0 application found under advanced settings>
MONGODB_URI=<MongoDB connection URI with database>
MONGODB_DB=<MongoDB database. Optional, authentication database will be used as default.>
SENTRY_DSN=<Sentry DSN>
SENTRY_ENVIRONMENT=<development or production>
# If NewRelic is used:
#NEW_RELIC_LICENSE_KEY=<NewRelic license key>
#NEW_RELIC_CONFIG_FILE=newrelic.ini
```

For docker compose with DB:

Create a script to create the MongoDB user in
`./docker-entrypoint-initdb.d/create-users.js`:

```javascript
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

In addition to the variables specified above, the following environment 
variables are needed:

```dotenv
MONGODB_URI=mongodb://ebl-api:<password>@mongo:27017/ebl`
MONGO_INITDB_ROOT_USERNAME=<Mongo root user>
MONGO_INITDB_ROOT_PASSWORD=<Mongo root user password>
MONGOEXPRESS_LOGIN=<Mongo Express login username>
MONGOEXPRESS_PASSWORD=<Mongo Express login password>
```

### Docker image

Build and run the docker image:

```shell script
docker build -t ebl/api . 
docker run -p 8000:8000 --rm -it --env-file=FILE --name ebl-api ebl/api
```

### Docker Compose

Build the images:

```shell script
docker-compose build
```

Run only the API:
```shell script
docker-compose -f ./docker-compose-api-only.yml up
``` 

Run the full backend including the database and admin interface:

```shell script
docker-compose up
```

## Updating transliterations and signs in fragments

Improving the parser can lead to existing transliterations to have obsolete
tokens or becoming invalid. The signs are calculated when a fragment is saved,
but if the sign list is updated the fragments are not automatically updated.

The `ebl.fragmentarium.update_fragments` module can be used to recreate
transliteration and signs in all fragments. A list of invalid fragments is
saved to `invalid_fragments.tsv`.

```shell script
pipenv run  python -m ebl.fragmentarium.update_fragments
```

## Type hints

Use type hints in new code and add the to old code when making changes.

## Package dependencies

- Avoid directed package dependency cycles.
- Domain packages should depend only on other domain packages.
- Application packages should depend only on application and domain packages.
- Wed and infrastructure should depend only on application and domain packges.
- All packages can depend on common modules in the top-level ebl package.

Dependencies can be analyzed with
[pydepgraph](https://github.com/stefano-maggiolo/pydepgraph):

```shell script
pydepgraph -p . -e tests -g 2 | dot -Tpng -o graph.png
```

## Acknowledgements

CSL-JSON schema is based on
[citation-style-language/schema](https://github.com/citation-style-language/schema)
Copyright (c) 2007-2018 Citation Style Language and contributors.
Licensed under MIT License.
