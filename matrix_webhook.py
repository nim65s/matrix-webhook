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
from http import HTTPStatus
from signal import SIGINT, SIGTERM

from aiohttp import web
from markdown import markdown
from nio import AsyncClient
from nio.exceptions import LocalProtocolError

SERVER_ADDRESS = (os.environ.get('INTERFACE', '127.0.0.1'), int(os.environ.get('PORT', 4785)))
MATRIX_URL = os.environ.get('MATRIX_URL', 'https://matrix.org')
MATRIX_ID = os.environ.get('MATRIX_ID', '@wwm:matrix.org')
MATRIX_PW = os.environ['MATRIX_PW']
API_KEY = os.environ['API_KEY']
CLIENT = AsyncClient(MATRIX_URL, MATRIX_ID)


async def handler(request):
    """
    Coroutine given to the server, st. it knows what to do with an HTTP request.

    This one handles a POST, checks its content, and forwards it to the matrix room.
    """
    data = await request.read()

    try:
        data = json.loads(data.decode())
    except json.decoder.JSONDecodeError:
        return create_json_response(HTTPStatus.BAD_REQUEST, 'Invalid JSON')

    data = parse_grafana_notification(request, data)

    if not all(key in data for key in ['text', 'key']):
        return create_json_response(HTTPStatus.BAD_REQUEST,
                                    'Missing text and/or API key property')

    if data['key'] != API_KEY:
        return create_json_response(HTTPStatus.UNAUTHORIZED, 'Invalid API key')

    room_id = request.path[1:]
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


def parse_grafana_notification(request, data):
    if 'key' in request.rel_url.query:
        data["key"] = request.rel_url.query["key"]
    text = ""
    if "title" in data:
        text = "### " + data["title"] + "\n"
    if "message" in data:
       text = text + data["message"] + "\n\n"
    if "evalMatches" in data:
        for match in data["evalMatches"]:
            text = text + "* " + match["metric"] + ": " + str(match["value"]) + "\n"
    data["text"] = text
    return data


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
