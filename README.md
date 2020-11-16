# Electronic Babylonian Literature API

[![Build Status](https://travis-ci.com/ElectronicBabylonianLiterature/ebl-api.svg?branch=master)](https://travis-ci.com/ElectronicBabylonianLiterature/ebl-api)
[![Test Coverage](https://api.codeclimate.com/v1/badges/63fd8d8e40b2066cb42b/test_coverage)](https://codeclimate.com/github/ElectronicBabylonianLiterature/ebl-api/test_coverage)
[![Maintainability](https://api.codeclimate.com/v1/badges/63fd8d8e40b2066cb42b/maintainability)](https://codeclimate.com/github/ElectronicBabylonianLiterature/ebl-api/maintainability)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

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
pipenv install --dev
```

The following services are needed to run application:

- [Auth0](https://auth0.com)
- [Sentry](https://sentry.io)

### Gitpod

The project comes with a [Gitpod](https://www.gitpod.io) configuration including
select extensions and a local MongoDB. Click the button below, configure the
[environment variables](https://www.gitpod.io/docs/environment-variables/)
(, import the data if you wish to use the local DB) and you are good to go.

[![Open in Gitpod](https://gitpod.io/button/open-in-gitpod.svg)](https://gitpod.io/#https://github.com/ElectronicBabylonianLiterature/ebl-api)

### Visual Studio Code

The project includes a Visual Studio Code
[development container](https://code.visualstudio.com/docs/remote/containers) which
can be used locally or in
[Codespaces](https://code.visualstudio.com/docs/remote/codespaces).

## Codestyle

Use [Black](https://black.readthedocs.io/en/stable/) codestyle.
Line length is 88, and bugbear B950 is used instead of E501.
PEP8 checks should be enabled in PyCharm, but E501, E203, and E231 should be
disabled.

Use type hints in new code and add the to old code when making changes.

### Package dependencies

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

## Running the tests

```shell script
pipenv run black ebl --check
pipenv run lint
pipenv run pyre check
pipenv run test
```

## Database

`pull-db.sh` can be used to pull a database from an another MongoDB instance to
your development MongoDB. It will use `mongodump` and `mongorestore` to get
all data except `changelog` collection, and `photos` and `folios` buckets.

To make the use less tedious the scripts reads defaults from the following
environment varaiables:

```dotenv
PULL_DB_DEFAULT_SOURCE_HOST=<source MongoDB host>
PULL_DB_DEFAULT_SOURCE_USER=<source MongoDB user>
PULL_DB_DEFAULT_SOURCE_PASSWORD=<source MongoDB password>
```

## Configuring services

### Auth0

An API has to be setup in Auth0 and it needs to have the *Scopes*. *Identifier* and *Client ID* are needed for the environment variables (see below).

#### Scopes

`write:bibliography`,
`read:bibliography`,
`access:beta`,
`lemmatize:fragments`,
`transliterate:fragments`,
`read:fragments`,
`write:words`,
`read:words`,
`read:texts`,
`write:texts`,
`create:texts`,
`annotate:fragments	Annotate`,

Folio scopes need to have the following format. 

`read:<Folio name>-folios`

### Sentry

An organization and project need to be setup in Sentry. *DSN* under *Client Keys* is needed for the for the environment variables (see below).

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

### Locally

```shell script
pipenv run start
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

⚠️ You must create a script to create the MongoDB user in
`./docker-entrypoint-initdb.d/create-users.js` before the
the database is started for the first time.

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

## Updating data

Changes to the schemas or parsers can lead the data in the database to become obsolete.
Below are instructions how to migrate Fragmentarium and Corpus to the latest state.

### Fragmentarium

Improving the parser can lead to existing transliterations to become obsolete
tokens or invalid. The signs are calculated when a fragment is saved,
but if the sign list is updated the fragments are not automatically updated.

The `ebl.fragmentarium.update_fragments` module can be used to recreate
transliteration and signs in all fragments. A list of invalid fragments is
saved to `invalid_fragments.tsv`.

The script can be run locally:

```shell script
pipenv run python -m ebl.fragmentarium.update_fragments
```

, as stand alone container:

```shell script
docker build -t ebl/api .
docker run --rm -it --env-file=FILE --name ebl-updater --mount type=bind,source="$(pwd)",target=/usr/src/ebl ebl/api pipenv run python -m ebl.fragmentarium.update_fragments
```

, or with `docker-compose`:

```shell script
docker-compose -f ./docker-compose-updater.yml up
```

If you need to run custom operations inside Docker you can start the shell:

```shell script
docker run --rm -it --env-file=.env --name ebl-shell --mount type=bind,source="$(pwd)",target=/usr/src/ebl ebl/api bash
```

### Corpus

The `ebl.corpus.texts` module can be used to save the texts with the latest schema.
A list of invalid texts is saved to `invalid_texts.tsv`. The script saves the texts
as is. Transliterations are not reparsed.

The script can be run locally:

```shell script
pipenv run python -m ebl.corpus.updte_texts
```

, as stand alone container:

```shell script
docker build -t ebl/api .^
docker run --rm -it --env-file=FILE --name ebl-corpus-updater --mount type=bind,source="$(pwd)",target=/usr/src/ebl ebl/api pipenv run python -m ebl.corpus.update_texts
```

### Steps to update the production database

1) Implement the new functionality.
2) Implement fallback to handle old data, if the new model is incompatible.
3) Test that fragments are updated correctly in the development database.
4) Deploy to production.
5) Run the migration script. Do not start the script until the deployment has been succesfully completed.
6) Fix invalid fragments.
7) Remove fallback logic.
8) Deploy to production.

### Importing .atf files

Importing and conversion of external .atf files which are encoded according to the oracc and c-ATF standards to the eBL-ATF standard.
* For a description of eBL-ATF see: [eBL-ATF specification](https://github.com/ElectronicBabylonianLiterature/ebl-api/blob/master/docs/ebl-atf.md)
* For a list of differences between the ATF flavors see: [eBL ATF and other ATF flavors](https://github.com/ElectronicBabylonianLiterature/generic-documentation/wiki/eBL-ATF-and-other-ATF-flavors)

<!-- usage -->
```sh-session
$ pipenv run python -m ebl-atf_importer.application.atf_importer.py [-h] -i INPUT [-o OUTPUT] [-t] [-v]
```
<!-- usagestop -->
- ## Command line options
  * `-h` shows help message and exits the script
  * `-i` path to the input directory (`required`)
  * `-g` path to the glossary file (`required`)
# Testing
  * run pytest from command line:
  <!-- testing -->
 ```sh-session
 $ pipenv run pytest
 ```
 <!-- testing -->

## Acknowledgements

CSL-JSON schema is based on
[citation-style-language/schema](https://github.com/citation-style-language/schema)
Copyright (c) 2007-2018 Citation Style Language and contributors.
Licensed under MIT License.
