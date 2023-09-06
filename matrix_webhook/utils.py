"""Matrix Webhook utils."""

import logging
from collections import defaultdict
from http import HTTPStatus

from aiohttp import web
from matrix import MatrixClient, MatrixException
from nio.exceptions import LocalProtocolError

ERROR_MAP = defaultdict(
    lambda: HTTPStatus.INTERNAL_SERVER_ERROR,
    {
        "M_FORBIDDEN": HTTPStatus.FORBIDDEN,
        "M_CONSENT_NOT_GIVEN": HTTPStatus.FORBIDDEN,
    },
)
LOGGER = logging.getLogger("matrix_webhook.utils")
CLIENT: None | MatrixClient = None


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
            await CLIENT.join_room(room_id)
            return None
        except MatrixException as e:
            return create_json_response(error_map(e.response), e.response.message)
        except LocalProtocolError as e:
            LOGGER.error(f"Send error: {e}")
        LOGGER.warning("Trying again")
    return create_json_response(HTTPStatus.GATEWAY_TIMEOUT, "Homeserver not responding")


async def send_room_message(room_id, content):
    """Send a message to a room."""
    LOGGER.debug(f"Sending room message in {room_id=}: {content=}")

    for _ in range(10):
        try:
            await CLIENT.send_message(room_id, content)

            return create_json_response(HTTPStatus.OK, "OK")
        except MatrixException as e:
            return create_json_response(error_map(e.response), e.response.message)
        except LocalProtocolError as e:
            LOGGER.error(f"Send error: {e}")
        LOGGER.warning("Trying again")
    return create_json_response(HTTPStatus.GATEWAY_TIMEOUT, "Homeserver not responding")
