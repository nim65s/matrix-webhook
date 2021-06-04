# Matrix Webhook

Post a message to a matrix room with a simple HTTP POST

## Configuration

Create a matrix user for the bot, make it join the rooms you want it to talk into, and then set the following
environment variables:

- `MATRIX_URL`: the url of the matrix homeserver
- `MATRIX_ID`: the user id of the bot on this server
- `MATRIX_PW`: the password for this user
- `API_KEY`: a secret to share with the users of the service
- `API_KEY_FIELD`: The field name inside the request payload holding
  the api key. Default: `key`
- `ROOM_FIELD`: The field name inside the request payload holding
  the matrix room id. Default: `room`. The key, value pair is only
  used if the room id is not passed via the request URL
- `HOST`: HOST to listen on, all interfaces if `''` (default).
- `PORT`: PORT to listed on, default to 4785.
- `LOG_LEVEL`: One of `DEBUG`, `INFO`, `WARNING`, `ERROR`,
  `CRITICAL`. Default: `INFO`

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

## Test room

[#matrix-webhook:tetaneutral.net](https://matrix.to/#/!DPrUlnwOhBEfYwsDLh:matrix.org?via=laas.fr&via=tetaneutral.net&via=aen.im)

## Support for mattermost webhooks

This is useful if you want to let e.g. gitlab use this webhook. At the
moment there is no native matrix integration. Instead you can abuse
the mattermost integration.
To use it:

```
docker-compose -f docker-compose.yml -f docker-compose-mattermost.yml up -d
```

Then setup a mattermost integration in gitlab:
`Settings` -> `Integrations` -> `Mattermost notifications`.

* Set `username` to the `API_KEY` you chose
* `Webhook`: The URL of your host, without the matrix room id
  (e.g. `http://matrixwebhook.localhost`)
* For each notification type, activate the checkbox and put a matrix
  room id into the channel field
