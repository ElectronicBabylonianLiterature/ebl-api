# Electronic Babylonian Library API

![Build Status](https://github.com/ElectronicBabylonianLiterature/ebl-api/workflows/CI/badge.svg?branch=master)
[![Test Coverage](https://api.codeclimate.com/v1/badges/63fd8d8e40b2066cb42b/test_coverage)](https://codeclimate.com/github/ElectronicBabylonianLiterature/ebl-api/test_coverage)
[![Maintainability](https://api.codeclimate.com/v1/badges/63fd8d8e40b2066cb42b/maintainability)](https://codeclimate.com/github/ElectronicBabylonianLiterature/ebl-api/maintainability)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Table of contents

* [Setup](#setup)
* [Development](#development)
* [Running the application](#running-the-application)
* [Updating data](#updating-data)
* [Acknowledgements](#acknowledgements)

## Setup

Requirements:

* [PyPy3.9](https://www.pypy.org) & pip
* [Task](https://taskfile.dev/)

```shell script
pip install poetry
poetry install --no-root
```

For development, use `poetry install --no-root --with dev`.

If `libcst` installation fails (because a binary wheel is not available for Linux/Windows + Pypy) you may need to install
the [rust compiler](https://www.rust-lang.org/tools/install) to solve it.

The following are needed to run application:

* MongoDB 4.4.4
* [Ebl-AI-Api](https://github.com/ElectronicBabylonianLiterature/ebl-ai-api)
* [Auth0](https://auth0.com)
* [Sentry](https://sentry.io)
* Docker (optional, see [Running the application](#running-the-application))

### Auth0

An *API* and *Application* have to be setup in Auth0 and it the API needs to have the *Scopes* listed below.

API *Identifier*, Application *Domain* (or the customdomain if one is used), and Application *Signing Certificate*
are needed for the environment variables (see below). The whole certificate needs (everything in the field or the downloaded PEM file)
has to be base64 encoded before being added to the environment variable.

#### Scopes

Corpus:
`write:texts`,
`create:texts`,

Fragmentarium:
`lemmatize:fragments`,
`transliterate:fragments`,
`annotate:fragments`,

Bibliography:
`write:bibliography`,

Dictionary:
`write:words`,

##### Legacy (currently unused) scopes

`access:beta`,
`read:texts`,
`read:fragments`,
`read:bibliography`,
`read:words`,

Folio scopes have the following format:

`read:<Folio name>-folios`

Fragments have additional scopes in the following format:

`read:<Fragment group>-fragments`

#### Rules

"Add permissions to the user object" must bet set in Authorization Extension and the rule published.
The following rules should be added to the *Auth Pipeleine*.

eBL name:

```javascript
function (user, context, callback) {
  const namespace = 'https://ebabylon.org/';
  context.idToken[namespace + 'eblName'] = user.user_metadata.eblName;
  callback(null, user, context);
}
```

Access token scopes (must be after the Authorization Extension's rule):

```javascript
function (user, context, callback) {
  const permissions = user.permissions || [];
  const requestedScopes = context.request.body.scope || context.request.query.scope;
  context.accessToken.scope = requestedScopes
    .split(' ')
    .filter(scope => scope.indexOf(':') < 0)
    .concat(permissions)
    .join(' ');

  callback(null, user, context);
}
```

#### Users

The users should `eblName` property in the `user_metadata`. E.g.:

```json
{
  "eblName": "Surname"
}
```

### Sentry

An organization and project need to be setup in Sentry. *DSN* under *Client Keys* is needed for the for the environment variables (see below).

## Development

The project comes with a [Gitpod](https://www.gitpod.io) configuration including
select extensions and a local MongoDB. Click the button below, configure the
[environment variables](https://www.gitpod.io/docs/environment-variables/)
(, import the data if you wish to use the local DB) and you are good to go.

[![Open in Gitpod](https://gitpod.io/button/open-in-gitpod.svg)](https://gitpod.io/#https://github.com/ElectronicBabylonianLiterature/ebl-api)

### Running the tests

```shell script
task format  # Format all files.
task format -- --check  # Check file formatting.
task lint  # Run linter.
task type  # Run type check
task test  # Run tests.  
task test -- -n auto  # Run tests in parallel.
task test -- --cov=ebl --cov-report term --cov-report xml  # Run tests with coverage (slow in PyPy).
task test-all  # Run format, lint and type checks, and tests.
```

See [pytest-xdist](https://github.com/pytest-dev/pytest-xdist) documentation
for more information on parallel tests. To avoid race condition when running
the tests in parallel run `poetry run python -m ebl.tests.downloader`.

⚠️ Sometimes test results may differ for PyPy and non-PyPy Python (the latter is used for some automatic checks in this repository). If tests fail with non-PyPy Python alone, make sure to install and use the same Python version for debugging.

## Custom Git Shortcut

```shell script
task cp --- commit-message  # Runs black, flake8 and pyre-check and git add, commit and push
```

### Codestyle

Use [Black](https://black.readthedocs.io/en/stable/) codestyle and
[PEP8 naming conventions](https://www.python.org/dev/peps/pep-0008/#naming-conventions).
Line length is 88, and bugbear B950 is used instead of E501.
PEP8 checks should be enabled in PyCharm, but E501, E203, and E231 should be
disabled.

Use type hints in new code and add the to old code when making changes.

### Package dependencies

* Avoid directed package dependency cycles.
* Domain packages should depend only on other domain packages.
* Application packages should depend only on application and domain packages.
* Web, infrastructure, etc. should depend only on application and domain packges.
* All packages can depend on common modules in the top-level ebl package.

Dependencies can be analyzed with
[pydepgraph](https://github.com/stefano-maggiolo/pydepgraph):

```shell script
pydepgraph -p . -e tests -g 2 | dot -Tpng -o graph.png
```

### Database

See
[dictionary-parser](https://github.com/ElectronicBabylonianLiterature/dictionary-parser),
[proper-name-importer](https://github.com/ElectronicBabylonianLiterature/proper-name-importer),
[fragmentarium-parser](https://github.com/ElectronicBabylonianLiterature/fragmentarium-parser), and
[sign-list-parser](https://github.com/ElectronicBabylonianLiterature/sign-list-parser)
about generating the initial data. There have been chanages to the database structure since the
scripts were initally used and they most likely require updates to work with latest version
of the API.

`pull-db.sh` script can be used to pull a database from an another MongoDB instance to
your development MongoDB. It will use `mongodump` and `mongorestore` to get
all data except `changelog` collection, and `photos` and `folios` buckets.

To make the use less tedious the scripts reads defaults from the following
environment varaiables:

```dotenv
PULL_DB_DEFAULT_SOURCE_HOST=<source MongoDB host>
PULL_DB_DEFAULT_SOURCE_USER=<source MongoDB user>
PULL_DB_DEFAULT_SOURCE_PASSWORD=<source MongoDB password>
```

The test use [pymongo_inmemory](https://github.com/kaizendorks/pymongo_inmemory) for tests.
Depending on your OS it might be necessary to configure it in order to get the correct version
of MongoDB. E.g. for Ubuntu add the following environment variables:

```dotenv
PYMONGOIM__MONGO_VERSION=4.4
PYMONGOIM__OPERATING_SYSTEM=ubuntu
```

### Caching

[Falcon-Caching](https://falcon-caching.readthedocs.io/) middleware can be used for caching.
See the documentation for more information. Configuration is read from `CACHE_CONFIG` environment variable.

```shell script
CACHE_CONFIG='{"CACHE_TYPE": "simple"}' poetry run waitress-serve --port=8000 --call ebl.app:get_app
```

Falcon-Caching v1.0.1 does not cache `media`. `text` must be used.

```python
@cache.cached(timeout=DEFAULT_TIMEOUT)
def on_get(self, req, resp):
    resp.text = ...
```

`cache-control` decorator can be used to add Cache-Control header to responses.

```python
@cache_control(['public', 'max-age=600'])
def on_get(self, req, resp):
    ...
```

A method to control when the header is added can be passed as the second argument.

```python
@cache_control(['public', 'max-age=600'], lambda req, resp: req.auth is None)
def on_get(self, req, resp):
    ...
```

### Authentication and Authorization

[Auth0](https://auth0.com) and [falcon-auth](https://github.com/vertexcover-io/falcon-auth)
are used for authentication and authorization.

An endpoint can be protected using the `@falcon.before` decorator three ways:

* `@falcon.before(require_scope, "your scope name here")`: Simple check if the user is allowed to use the endpoint. Dynamic checks based on the fetched data is not possible.
* `@falcon.before(require_folio_scope)`: Dynamically checks if the user can read folios based on the folio name from the url
* `@falcon.before(require_fragment_read_scope)`: Dynamically checks if the user can read individual fragments by comparing the
`authorized_scopes` from the fragment with the user scopes

For example:

```python
import falcon
from ebl.users.web.require_scope import require_scope, require_fragment_read_scope

@falcon.before(require_fragment_read_scope)
def on_get(self, req, resp):
    ...

@falcon.before(require_scope, "write:texts")
def on_post(self, req, resp):
    ...
```

## Running the application

The application reads the configuration from following environment variables:

 ```dotenv
AUTH0_AUDIENCE=<the Identifier from Auth0 API Settings>
AUTH0_ISSUER=<the Domain from Auth Application Setttings, or the custom domain from Branding>
AUTH0_PEM=<Signing Certificate (PEM) from the Auth0 Application Advanced Settings. The whole certificate needs to be base64 encoded again before adding to environment.>
MONGODB_URI=<MongoDB connection URI with database>
MONGODB_DB=<MongoDB database. Optional, authentication database will be used as default.>
EBL_AI_API=<AI API URL. If you do not have access to and do not need the AI API use a safe dummy value.>
SENTRY_DSN=<Sentry DSN>
SENTRY_ENVIRONMENT=<development or production>
CACHE_CONFIG=<Falcon-Caching configuration. Optional, Null backend will be used as default.>
```

Poetry does not support .env-files. The environment variables need to be configured in the shell,
unless ran via [Task](https://taskfile.dev/). Alternatively and external program can be used to
handle the file e.g. [direnv](https://direnv.net/) or
[Set-PsEnv](https://github.com/rajivharris/Set-PsEnv).

### Locally

```shell script
task start
# or
poetry run waitress-serve --port=8000 --call ebl.app:get_app
```

### Docker image

Build and run the docker image:

```shell script
docker build -t ebl/api .
docker run -p 8000:8000 --rm -it --env-file=FILE --name ebl-api ebl/api
```

If you need to run custom operations inside Docker you can start the shell:

```shell script
docker run --rm -it --env-file=.env --name ebl-shell --mount type=bind,source="$(pwd)",target=/usr/src/ebl ebl/api bash
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

In addition to the variables specified above, the following environment
variables are needed:

```dotenv
MONGODB_URI=mongodb://ebl-api:<password>@mongo:27017/ebl`
MONGO_INITDB_ROOT_USERNAME=<Mongo root user>
MONGO_INITDB_ROOT_PASSWORD=<Mongo root user password>
MONGOEXPRESS_LOGIN=<Mongo Express login username>
MONGOEXPRESS_PASSWORD=<Mongo Express login password>
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
poetry run python -m ebl.fragmentarium.update_fragments
```

, as stand alone container:

```shell script
docker build -t ebl/api .
docker run --rm -it --env-file=.env --name ebl-updater ebl/api poetry run python -m ebl.fragmentarium.update_fragments
```

, or with `docker-compose`:

```shell script
docker-compose -f ./docker-compose-updater.yml up
```

### Corpus

The `ebl.corpus.texts` module can be used to save the texts with the latest schema.
A list of invalid texts is saved to `invalid_texts.tsv`. The script saves the texts
as is. Transliterations are not reparsed.

The script can be run locally:

```shell script
poetry run python -m ebl.corpus.update_texts
```

, as stand alone container:

```shell script
docker build -t ebl/api .
docker run --rm -it --env-file=.env --name ebl-corpus-updater ebl/api poetry run python -m ebl.corpus.update_texts
```

### Alignment

The `ebl.alignment.align_fragmentarium` module can be used to save align all
fragments in the Fragmentarium with the Corpus.
The scripts accepts the following arguments:

```text
-h, --help                     show this help message and exit
-s SKIP, --skip SKIP           Number of fragments to skip.
-l LIMIT, --limit LIMIT        Number of fragments to align.
--minScore MIN_SCORE           Minimum score to show in the results.
--maxLines MAX_LINES           Maximum size of fragment to align.
-o OUTPUT, --output OUTPUT     Filename for saving the results.
-w WORKERS, --workers WORKERS  Number of parallel workers.
-t, --threads                  Use threads instead of processes for workers.
```

The script can be run locally:

```shell script
poetry run python -m ebl.alignment.align_fragmentarium
```

or as stand alone container:

```shell script
docker build -t ebl/api .
docker run --rm -it --env-file=.env --name ebl-corpus-updater ebl/api poetry run python -m ebl.alignment.align_fragmentarium
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

To run use:
<!-- usage -->
```sh-session
poetry run python -m ebl.atf_importer.application.atf_importer [-h] -i INPUT -g GLOSSARIES_DIRECTORY -l LOGDIR [-a] [-s]

```
<!-- usagestop -->
#### Command line options

* `-h` shows help message and exits the script.
* `-i` INPUT, `--input` INPUT : Path of the input directory (`required`).
* `-l` LOGDIR, `--logdir` LOGDIR : Path of the log files directory (`required`).
* `-g` GLODIR, `--glodir` GLODIR : Path to the glossaries (`.glo` files) directory (`required`).
* `-a` AUTHOR, `--author` AUTHOR : Name of the author of the imported fragements. If not specified a name needs to be entered manually for every fragment (`optional`).

* The importer always tries to import all .atf files from one given input `-i` folder. To every imported folder a path to a folder with glossary file(s) (`.glo`) must be specified via `-g`. You can also assign an author to all imported fragments which are processed in one run via the `-a` option. If `-a` is omitted the atf-importer will ask for an author for each imported fragment.

Example calls:

```sh-session
poetry run python -m ebl.atf_importer.application.atf_importer -i "ebl/atf_importer/input/" -l "ebl/atf_importer/logs/" -g  "ebl/atf_importer/glossary" -a "atf_importer"
poetry run python -m ebl.atf_importer.application.atf_importer -i "ebl/atf_importer/input_cdli_atf/" -l "ebl/atf_importer/logs/" -g  "ebl/atf_importer/glossary" -a "test"
poetry run python -m ebl.atf_importer.application.atf_importer -i "ebl/atf_importer/input_c_atf/" -l "ebl/atf_importer/logs/" -g  "ebl/atf_importer/glossary" -a "test"
```

#### Troubleshooting

If a fragment cannot be imported check the console output for errors. Also check the specified log folder (`error_lines.txt`,`unparsable_lines_[fragment_file].txt`, `not_imported_files.txt`) and see which lines could not be parsed.
If lines are faulty, fix them manually and retry the import process. If tokes are not lemmatized correctly, check the log-file `lemmatization_log.txt`.

## Acknowledgements

CSL-JSON schema is based on
[citation-style-language/schema](https://github.com/citation-style-language/schema)
Copyright (c) 2007-2018 Citation Style Language and contributors.
Licensed under MIT License.
