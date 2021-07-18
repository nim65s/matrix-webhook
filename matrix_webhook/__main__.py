#!/usr/bin/env python3
"""
Matrix Webhook.

Post a message to a matrix room with a simple HTTP POST
"""

import asyncio
import json
import logging
from http import HTTPStatus
from signal import SIGINT, SIGTERM

from aiohttp import web
from markdown import markdown
from nio import AsyncClient
from nio.exceptions import LocalProtocolError
from nio.responses import RoomSendError

from . import conf

ERROR_MAP = {"M_FORBIDDEN": HTTPStatus.FORBIDDEN}

CLIENT = AsyncClient(conf.MATRIX_URL, conf.MATRIX_ID)
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

    if data["key"] != conf.API_KEY:
        return create_json_response(HTTPStatus.UNAUTHORIZED, "Invalid API key")

    room_id = request.path[1:]
    content = {
        "msgtype": "m.text",
        "body": data["text"],
        "format": "org.matrix.custom.html",
        "formatted_body": markdown(str(data["text"]), extensions=["extra"]),
    }
    for _ in range(10):
        try:
            resp = await send_room_message(room_id, content)
            if isinstance(resp, RoomSendError):
                if resp.status_code == "M_UNKNOWN_TOKEN":
                    LOGGER.warning("Reconnecting")
                    await CLIENT.login(conf.MATRIX_PW)
                else:
                    return create_json_response(
                        ERROR_MAP[resp.status_code], resp.message
                    )
            else:
                break
        except LocalProtocolError as e:
            LOGGER.error(f"Send error: {e}")
        LOGGER.warning("Trying again")
    else:
        return create_json_response(
            HTTPStatus.GATEWAY_TIMEOUT, "Homeserver not responding"
        )

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
    LOGGER.info(f"Log in {conf.MATRIX_ID=} on {conf.MATRIX_URL=}")
    await CLIENT.login(conf.MATRIX_PW)

    server = web.Server(handler)
    runner = web.ServerRunner(server)
    await runner.setup()
    LOGGER.info(f"Binding on {conf.SERVER_ADDRESS=}")
    site = web.TCPSite(runner, *conf.SERVER_ADDRESS)
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
    logging.basicConfig(level=50 - 10 * conf.VERBOSE, format=log_format)
    run()
