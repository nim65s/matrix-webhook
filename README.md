# Matrix Webhook

Post a message to a matrix room with a simple HTTP POST. This fork supports parsing Grafana notifications.

## Configuration

Create a matrix user for the bot, make it join the rooms you want it to talk into, and then set the following
environment variables:

- `INTERFACE`: the IP address of the interface on which to bind. Default: `127.0.0.1`
- `PORT`: bind port. Default: `4785`
- `MATRIX_URL`: the url of the matrix homeserver
- `MATRIX_ID`: the user id of the bot on this server
- `MATRIX_PW`: the password for this user
- `API_KEY`: a secret to share with the users of the service

## Dev

```
pip3 install --user markdown matrix-nio
./matrix_webhook.py
```

## Prod

- Use [Traefik](https://traefik.io/) on the `web` docker network, eg. with
  [proxyta.net](https://framagit.org/oxyta.net/proxyta.net)
- Put the configuration into a `.env` file
- Configure your DNS for `${CHATONS_SERVICE:-matrixwebhook}.${CHATONS_DOMAIN:-localhost}`

```
docker-compose up -d
```

## Test / Usage

```
curl -d '{"text":"new contrib from toto: [44](http://radio.localhost/map/#44)", "key": "secret"}' \
  'http://matrixwebhook.localhost/!DPrUlnwOhBEfYwsDLh:matrix.org'
```
(or localhost:4785 without docker)

Alternatively, the `key` can be passed as a get parameter. This is required for Grafana notificaions. The notification URL then is `https://example.com/!DPrUlnwOhBEfYwsDLh:matrix.org?key=YOURTOKEN`.

## Test room

[#matrix-webhook:tetaneutral.net](https://matrix.to/#/!DPrUlnwOhBEfYwsDLh:matrix.org?via=laas.fr&via=tetaneutral.net&via=aen.im)
