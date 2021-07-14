#!/usr/bin/env python3
"""
Matrix Webhook.

Post a message to a matrix room with a simple HTTP POST
"""

import argparse
import asyncio
import json
import logging
import os
from http import HTTPStatus
from signal import SIGINT, SIGTERM

from aiohttp import web
from markdown import markdown
from nio import AsyncClient
from nio.exceptions import LocalProtocolError

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    "-H",
    "--host",
    default=os.environ.get("HOST", ""),
    help="host to listen to. Default: `''`. Environment variable: `HOST`",
)
parser.add_argument(
    "-P",
    "--port",
    type=int,
    default=os.environ.get("PORT", 4785),
    help="port to listed to. Default: 4785. Environment variable: `PORT`",
)
parser.add_argument(
    "-u",
    "--matrix-url",
    default=os.environ.get("MATRIX_URL", "https://matrix.org"),
    help="matrix homeserver url. Default: `https://matrix.org`. Environment variable: `MATRIX_URL`",
)
parser.add_argument(
    "-i",
    "--matrix-id",
    help="matrix user-id. Required. Environment variable: `MATRIX_ID`",
    **(
        {"default": os.environ["MATRIX_ID"]}
        if "MATRIX_ID" in os.environ
        else {"required": True}
    ),
)
parser.add_argument(
    "-p",
    "--matrix-pw",
    help="matrix password. Required. Environment variable: `MATRIX_PW`",
    **(
        {"default": os.environ["MATRIX_PW"]}
        if "MATRIX_PW" in os.environ
        else {"required": True}
    ),
)
parser.add_argument(
    "-k",
    "--api-key",
    help="shared secret to use this service. Required. Environment variable: `API_KEY`",
    **(
        {"default": os.environ["API_KEY"]}
        if "API_KEY" in os.environ
        else {"required": True}
    ),
)
parser.add_argument(
    "-v", "--verbose", action="count", default=0, help="increment verbosity level"
)

args = parser.parse_args()

SERVER_ADDRESS = (args.host, args.port)
MATRIX_URL = args.matrix_url
MATRIX_ID = args.matrix_id
MATRIX_PW = args.matrix_pw
API_KEY = args.api_key
CLIENT = AsyncClient(args.matrix_url, args.matrix_id)
LOGGER = logging.getLogger("matrix-webhook")


async def handler(request):
    """
    Coroutine given to the server, st. it knows what to do with an HTTP request.

    This one handles a POST, checks its content, and forwards it to the matrix room.
    """
    LOGGER.debug(f"Handling {request=}")
    data = await request.read()

    try:
        data = json.loads(data.decode())
    except json.decoder.JSONDecodeError:
        return create_json_response(HTTPStatus.BAD_REQUEST, "Invalid JSON")

    if not all(key in data for key in ["text", "key"]):
        return create_json_response(
            HTTPStatus.BAD_REQUEST, "Missing text and/or API key property"
        )

    if data["key"] != API_KEY:
        return create_json_response(HTTPStatus.UNAUTHORIZED, "Invalid API key")

    room_id = request.path[1:]
    content = {
        "msgtype": "m.text",
        "body": data["text"],
        "format": "org.matrix.custom.html",
        "formatted_body": markdown(str(data["text"]), extensions=["extra"]),
    }
    try:
        await send_room_message(room_id, content)
    except LocalProtocolError as e:  # Connection lost, try another login
        LOGGER.error(f"Send error: {e}")
        LOGGER.warning("Reconnecting and trying again")
        await CLIENT.login(MATRIX_PW)
        await send_room_message(room_id, content)

    return create_json_response(HTTPStatus.OK, "OK")


def create_json_response(status, ret):
    """Create a JSON response."""
    LOGGER.debug(f"Creating json response: {status=}, {ret=}")
    response_data = {"status": status, "ret": ret}
    return web.json_response(response_data, status=status)


async def send_room_message(room_id, content):
    """Send a message to a room."""
    LOGGER.debug(f"Sending room message in {room_id=}: {content=}")
    return await CLIENT.room_send(
        room_id=room_id, message_type="m.room.message", content=content
    )


async def main(event):
    """
    Launch main coroutine.

    matrix client login & start web server
    """
    LOGGER.info(f"Log in {MATRIX_ID=} on {MATRIX_URL=}")
    await CLIENT.login(MATRIX_PW)

    server = web.Server(handler)
    runner = web.ServerRunner(server)
    await runner.setup()
    LOGGER.info(f"Binding on {SERVER_ADDRESS=}")
    site = web.TCPSite(runner, *SERVER_ADDRESS)
    await site.start()

    # Run until we get a shutdown request
    await event.wait()

    # Cleanup
    await runner.cleanup()
    await CLIENT.close()


def terminate(event, signal):
    """Close handling stuff."""
    event.set()
    asyncio.get_event_loop().remove_signal_handler(signal)


def run():
    """Launch everything."""
    LOGGER.info("Starting...")
    loop = asyncio.get_event_loop()
    event = asyncio.Event()

    for sig in (SIGINT, SIGTERM):
        loop.add_signal_handler(sig, terminate, event, sig)

    loop.run_until_complete(main(event))

    LOGGER.info("Closing...")
    loop.close()


if __name__ == "__main__":
    log_format = "%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s"
    logging.basicConfig(level=50 - 10 * args.verbose, format=log_format)
    run()
