#!/usr/bin/env python3
"""
Matrix Webhook.

Post a message to a matrix room with a simple HTTP POST
v1: matrix-client & http.server
v2: matrix-nio & aiohttp & markdown
"""

import asyncio
import json
import os
import logging
from http import HTTPStatus
from signal import SIGINT, SIGTERM

from aiohttp import web
from markdown import markdown
from nio import AsyncClient
from nio.exceptions import LocalProtocolError

SERVER_ADDRESS = (os.environ.get('HOST', ''), int(os.environ.get('PORT', 4785)))
MATRIX_URL = os.environ.get('MATRIX_URL', 'https://matrix.org')
MATRIX_ID = os.environ.get('MATRIX_ID', '@wwm:matrix.org')
MATRIX_PW = os.environ['MATRIX_PW']
API_KEY = os.environ['API_KEY']
API_KEY_FIELD = os.environ.get('API_KEY_FIELD', 'key')
ROOM_FIELD = os.environ.get('ROOM_FIELD', 'room')
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

CLIENT = AsyncClient(MATRIX_URL, MATRIX_ID)

logging.basicConfig(level=getattr(logging, LOG_LEVEL))

async def handler(request):
    """
    Coroutine given to the server, st. it knows what to do with an HTTP request.

    This one handles a POST, checks its content, and forwards it to the matrix room.
    """
    data = await request.text()

    try:
        data = json.loads(data)
    except json.decoder.JSONDecodeError:
        return create_json_response(HTTPStatus.BAD_REQUEST, 'Invalid JSON')

    missing_keys = {'text', API_KEY_FIELD} - set(data)
    if missing_keys:
        return create_json_response(
            HTTPStatus.BAD_REQUEST, f'Missing keys: {", ".join(missing_keys)}'
        )

    if data[API_KEY_FIELD] != API_KEY:
        return create_json_response(HTTPStatus.UNAUTHORIZED, 'Invalid ' + API_KEY_FIELD)

    room_id = request.path.lstrip('/') or data.get(ROOM_FIELD)
    if not room_id:
        return create_json_response(HTTPStatus.BAD_REQUEST, 'Missing key: ' + ROOM_FIELD)

    content = {
        'msgtype': 'm.text',
        'body': data['text'],
        'format': 'org.matrix.custom.html',
        'formatted_body': markdown(data['text'], extensions=['extra']),
    }
    try:
        await send_room_message(room_id, content)
    except LocalProtocolError:  # Connection lost, try another login
        await CLIENT.login(MATRIX_PW)
        await send_room_message(room_id, content)

    return create_json_response(HTTPStatus.OK, 'OK')


def create_json_response(status, ret):
    """Create a JSON response."""
    response_data = {'status': status, 'ret': ret}
    return web.json_response(response_data, status=status)


async def send_room_message(room_id, content):
    """Send a message to a room."""
    return await CLIENT.room_send(room_id=room_id,
                                  message_type='m.room.message',
                                  content=content)


async def main(event):
    """
    Launch main coroutine.

    matrix client login & start web server
    """
    await CLIENT.login(MATRIX_PW)

    server = web.Server(handler)
    runner = web.ServerRunner(server)
    await runner.setup()
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
    loop = asyncio.get_event_loop()
    event = asyncio.Event()

    for sig in (SIGINT, SIGTERM):
        loop.add_signal_handler(sig, terminate, event, sig)

    loop.run_until_complete(main(event))

    loop.close()


if __name__ == '__main__':
    run()
