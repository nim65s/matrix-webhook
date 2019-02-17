# Matrix Webhook

Post a message to a matrix room with a simple HTTP POST

## Configuration

Set the following environment variables:

- `MATRIX_URL`: the url of the matrix homeserver
- `MATRIX_ID`: the user id of the bot on this server
- `MATRIX_PW`: the password for this user

## Dev

```
pip3 install --user matrix-client
./matrix_webhook.py
```

## Prod

- Use [Traefik](https://traefik.io/) on the `web` docker network, eg. with
  [proxyta.net](https://framagit.org/oxyta.net/proxyta.net)
- Put the configuration into a `.env` file (don't forget about `CHATONS_DOMAIN`, otherwise by default you will stay on
  `localhost`)

```
docker-compose up -d
```

## Test / Usage

```
curl -d '{"text":"new contrib from toto: http://radio.localhost/map/#44", "key": "secret"}' mwh.localhost
```
(or mwh.localhost:4785 without docker)
