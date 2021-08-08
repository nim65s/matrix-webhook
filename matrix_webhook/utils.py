"""Matrix Webhook utils."""

import logging
from http import HTTPStatus

from aiohttp import web
from nio import AsyncClient
from nio.exceptions import LocalProtocolError
from nio.responses import RoomSendError

from . import conf

ERROR_MAP = {"M_FORBIDDEN": HTTPStatus.FORBIDDEN}
LOGGER = logging.getLogger("matrix_webhook.utils")
CLIENT = AsyncClient(conf.MATRIX_URL, conf.MATRIX_ID)


def create_json_response(status, ret):
    """Create a JSON response."""
    LOGGER.debug(f"Creating json response: {status=}, {ret=}")
    response_data = {"status": status, "ret": ret}
    return web.json_response(response_data, status=status)


async def send_room_message(room_id, content):
    """Send a message to a room."""
    LOGGER.debug(f"Sending room message in {room_id=}: {content=}")

    for _ in range(10):
        try:
            resp = await CLIENT.room_send(
                room_id=room_id, message_type="m.room.message", content=content
            )
            if isinstance(resp, RoomSendError):
                if resp.status_code == "M_UNKNOWN_TOKEN":
                    LOGGER.warning("Reconnecting")
                    await CLIENT.login(conf.MATRIX_PW)
                else:
                    return create_json_response(
                        ERROR_MAP[resp.status_code], resp.message
                    )
            else:
                return create_json_response(HTTPStatus.OK, "OK")
        except LocalProtocolError as e:
            LOGGER.error(f"Send error: {e}")
        LOGGER.warning("Trying again")
    return create_json_response(HTTPStatus.GATEWAY_TIMEOUT, "Homeserver not responding")
