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

from markdown import markdown

from aiohttp import web
from nio import AsyncClient

SERVER_ADDRESS = ('', int(os.environ.get('PORT', 4785)))
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
    data = json.loads(data.decode())
    status, ret = HTTPStatus.BAD_REQUEST, 'I need a json dict with text & key'
    if all(key in data for key in ['text', 'key']):
        status, ret = HTTPStatus.UNAUTHORIZED, 'I need the good "key"'
        if data['key'] == API_KEY:
            status, ret = HTTPStatus.OK, 'OK'
            await CLIENT.room_send(room_id=str(request.rel_url)[1:],
                                   message_type="m.room.message",
                                   content={
                                       "msgtype": "m.text",
                                       "body": data['text'],
                                       "format": "org.matrix.custom.html",
                                       "formatted_body": markdown(data['text']),
                                   })

    return web.Response(text='{"status": %i, "ret": "%s"}' % (status, ret),
                        content_type='application/json',
                        status=status)


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
