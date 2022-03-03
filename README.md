# Matrix Webhook

[![Tests](https://github.com/nim65s/matrix-webhook/actions/workflows/test.yml/badge.svg)](https://github.com/nim65s/matrix-webhook/actions/workflows/test.yml)
[![Lints](https://github.com/nim65s/matrix-webhook/actions/workflows/lint.yml/badge.svg)](https://github.com/nim65s/matrix-webhook/actions/workflows/lint.yml)
[![Docker-Hub](https://github.com/nim65s/matrix-webhook/actions/workflows/docker-hub.yml/badge.svg)](https://hub.docker.com/r/nim65s/matrix-webhook)
[![Release](https://github.com/nim65s/matrix-webhook/actions/workflows/release.yml/badge.svg)](https://pypi.org/project/matrix-webhook/)

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![codecov](https://codecov.io/gh/nim65s/matrix-webhook/branch/master/graph/badge.svg?token=BLGISGCYKG)](https://codecov.io/gh/nim65s/matrix-webhook)
[![PyPI version](https://badge.fury.io/py/matrix-webhook.svg)](https://badge.fury.io/py/matrix-webhook)

Post a message to a matrix room with a simple HTTP POST

## Install

```
python3 -m pip install matrix-webhook
# OR
docker pull nim65s/matrix-webhook
```

## Start

Create a matrix user for the bot, and launch this app it with the following arguments or environment variables:

```
python -m matrix_webhook -h
# OR
docker run --rm -it nim65s/matrix-webhook -h
```

```
usage: python -m matrix_webhook [-h] [-H HOST] [-P PORT] [-u MATRIX_URL] -i MATRIX_ID -p MATRIX_PW -k API_KEY [-v]

Configuration for Matrix Webhook.


optional arguments:
  -h, --help            show this help message and exit
  -H HOST, --host HOST  host to listen to. Default: `''`. Environment variable: `HOST`
  -P PORT, --port PORT  port to listed to. Default: 4785. Environment variable: `PORT`
  -u MATRIX_URL, --matrix-url MATRIX_URL
                        matrix homeserver url. Default: `https://matrix.org`. Environment variable: `MATRIX_URL`
  -i MATRIX_ID, --matrix-id MATRIX_ID
                        matrix user-id. Required. Environment variable: `MATRIX_ID`
  -p MATRIX_PW, --matrix-pw MATRIX_PW
                        matrix password. Required. Environment variable: `MATRIX_PW`
  -k API_KEY, --api-key API_KEY
                        shared secret to use this service. Required. Environment variable: `API_KEY`
  -v, --verbose         increment verbosity level
```


## Dev

```
poetry install
# or python3 -m pip install --user markdown matrix-nio
python3 -m matrix_webhook
```

## Prod

A `docker-compose.yml` is provided:

- Use [Traefik](https://traefik.io/) on the `web` docker network, eg. with
  [proxyta.net](https://framagit.org/oxyta.net/proxyta.net)
- Put the configuration into a `.env` file
- Configure your DNS for `${CHATONS_SERVICE:-matrixwebhook}.${CHATONS_DOMAIN:-localhost}`

```
docker-compose up -d
```

## Test / Usage

```
curl -d '{"body":"new contrib from toto: [44](http://radio.localhost/map/#44)", "key": "secret"}' \
  'http://matrixwebhook.localhost/!DPrUlnwOhBEfYwsDLh:matrix.org'
```
(or localhost:4785 without docker)

### For Github

Add a JSON webhook with `?formatter=github`, and put the `API_KEY` as secret

### For Grafana

Add a webhook with an URL ending with `?formatter=grafana&key=API_KEY`

### For Gitlab

At a group level, Gitlab does not permit to setup webhooks. A workaround consists to use Google
Chat or Microsoft Teams notification integration with a custom URL (Gitlab does not check if the url begins with the normal url of the service).

#### Google Chat

Add a Google Chat integration with an URL ending with `?formatter=gitlab_gchat&key=API_KEY`

#### Microsoft Teams

Add a Microsoft Teams integration with an URL ending with `?formatter=gitlab_teams&key=API_KEY`

## Test room

[#matrix-webhook:tetaneutral.net](https://matrix.to/#/!DPrUlnwOhBEfYwsDLh:matrix.org)

## Unit tests

```
docker-compose -f test.yml up --exit-code-from tests --force-recreate --build
```
