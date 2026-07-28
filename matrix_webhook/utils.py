"""Matrix Webhook utils."""

import logging
from asyncio import create_task
from collections import defaultdict
from http import HTTPStatus
from re import sub

from aiohttp import web
from nio import AsyncClient, InviteEvent, MatrixRoom
from nio.exceptions import LocalProtocolError
from nio.responses import JoinError, RoomSendError

from . import conf

ERROR_MAP = defaultdict(
    lambda: HTTPStatus.INTERNAL_SERVER_ERROR,
    {
        "M_FORBIDDEN": HTTPStatus.FORBIDDEN,
        "M_CONSENT_NOT_GIVEN": HTTPStatus.FORBIDDEN,
    },
)
LOGGER = logging.getLogger("matrix_webhook.utils")
CLIENT = AsyncClient(conf.MATRIX_URL, conf.MATRIX_ID, proxy=conf.PROXY)


def format_url(data):
    data = sub(
        r"(<(https?://[\w.-]+(?:\.[\w\.-]+)+[\w\-\._~:/?#[\]@!\$&'\(\)\*\+,;=.]+)\|([\w\s]+)>)",
        r'<a href="\2">\3</a>',
        data,
    )
    return sub(
        r"(<)(https?://[\w.-]+(?:\.[\w\.-]+)+[\w\-\._~:/?#[\]@!\$&'\(\)\*\+,;=.]+)(>)",
        r'<a href="\2">\2</a>',
        data,
    )


def error_map(resp):
    """Map response errors to HTTP status."""
    if resp.status_code == "M_UNKNOWN":
        # in this case, we should directly consider the HTTP status from the response
        # ref. https://matrix.org/docs/spec/client_server/r0.6.1#api-standards
        return resp.transport_response.status
    return ERROR_MAP[resp.status_code]


def create_json_response(status, ret, formatter: str = None):
    """Create a JSON response."""
    msg = f"Creating json response: {status=}, {ret=}"
    if formatter == "slack":
        response_data = {"ok": 200 <= status.value < 300, "error": ret}
    else:
        response_data = {"status": status, "ret": ret}
    return web.json_response(response_data, status=status)


async def join_room(room_id, formatter: str = None):
    """Try to join the room."""
    msg = f"Join room {room_id=}"
    LOGGER.debug(msg)

    for _ in range(10):
        try:
            resp = await CLIENT.join(room_id)
            if isinstance(resp, JoinError):
                if resp.status_code == "M_UNKNOWN_TOKEN":
                    LOGGER.warning("Reconnecting")
                    if conf.MATRIX_PW:
                        await CLIENT.login(conf.MATRIX_PW)
                else:
                    return create_json_response(
                        status=error_map(resp), ret=resp.message, formatter=formatter
                    )
            else:
                return None
        except LocalProtocolError as e:
            msg = f"Send error: {e}"
            LOGGER.error(msg)
            LOGGER.warning("Reconnecting")
            if conf.MATRIX_PW:
                await CLIENT.login(conf.MATRIX_PW)
        LOGGER.warning("Trying again")
    return create_json_response(
        status=HTTPStatus.GATEWAY_TIMEOUT,
        ret="Homeserver not responding",
        formatter=formatter,
    )


async def accept_invitation(room: MatrixRoom, event: InviteEvent):
    LOGGER.info(f"Got invite to room {room.room_id=}")
    await CLIENT.join(room.room_id)


def watch_for_invitation():
    CLIENT.add_event_callback(accept_invitation, InviteEvent)
    return create_task(CLIENT.sync_forever())


async def send_room_message(room_id, content, formatter: str = None):
    """Send a message to a room."""
    msg = f"Sending room message in {room_id=}: {content=}"
    LOGGER.debug(msg)

    for _ in range(10):
        try:
            resp = await CLIENT.room_send(
                room_id=room_id,
                message_type="m.room.message",
                content=content,
            )
            if isinstance(resp, RoomSendError):
                if resp.status_code == "M_UNKNOWN_TOKEN":
                    LOGGER.warning("Reconnecting")
                    if conf.MATRIX_PW:
                        await CLIENT.login(conf.MATRIX_PW)
                else:
                    return create_json_response(
                        status=error_map(resp), ret=resp.message, formatter=formatter
                    )
            else:
                return create_json_response(
                    status=HTTPStatus.OK, ret="OK", formatter=formatter
                )
        except LocalProtocolError as e:
            msg = f"Send error: {e}"
            LOGGER.error(msg)
            LOGGER.warning("Reconnecting")
            if conf.MATRIX_PW:
                await CLIENT.login(conf.MATRIX_PW)
        LOGGER.warning("Trying again")
    return create_json_response(
        status=HTTPStatus.GATEWAY_TIMEOUT,
        ret="Homeserver not responding",
        formatter=formatter,
    )
