"""Matrix Webhook utils."""

import logging
from http import HTTPStatus

from aiohttp import web
from nio import AsyncClient
from nio.exceptions import LocalProtocolError
from nio.responses import RoomSendError, JoinError

from . import conf

ERROR_MAP = {
    "M_FORBIDDEN": HTTPStatus.FORBIDDEN,
    "M_CONSENT_NOT_GIVEN": HTTPStatus.FORBIDDEN,
}
LOGGER = logging.getLogger("matrix_webhook.utils")
CLIENT = AsyncClient(conf.MATRIX_URL, conf.MATRIX_ID)


def error_map(resp):
    """Map response errors to HTTP status."""
    if resp.status_code == "M_UNKNOWN":
        # in this case, we should directly consider the HTTP status from the response
        # ref. https://matrix.org/docs/spec/client_server/r0.6.1#api-standards
        return resp.transport_response.status
    return ERROR_MAP[resp.status_code]


def create_json_response(status, ret):
    """Create a JSON response."""
    LOGGER.debug(f"Creating json response: {status=}, {ret=}")
    response_data = {"status": status, "ret": ret}
    return web.json_response(response_data, status=status)


async def join_room(room_id):
    """Try to join the room."""
    LOGGER.debug(f"Join room {room_id=}")

    for _ in range(10):
        try:
            resp = await CLIENT.join(room_id)
            if isinstance(resp, JoinError):
                if resp.status_code == "M_UNKNOWN_TOKEN":
                    LOGGER.warning("Reconnecting")
                    await CLIENT.login(conf.MATRIX_PW)
                else:
                    return create_json_response(error_map(resp), resp.message)
            else:
                return None
        except LocalProtocolError as e:
            LOGGER.error(f"Send error: {e}")
        LOGGER.warning("Trying again")
    return create_json_response(HTTPStatus.GATEWAY_TIMEOUT, "Homeserver not responding")


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
                    return create_json_response(error_map(resp), resp.message)
            else:
                return create_json_response(HTTPStatus.OK, "OK")
        except LocalProtocolError as e:
            LOGGER.error(f"Send error: {e}")
        LOGGER.warning("Trying again")
    return create_json_response(HTTPStatus.GATEWAY_TIMEOUT, "Homeserver not responding")
