#!/usr/bin/env python
"""
wifi-with-matrix script.
Bridge between https://code.ffdn.org/FFDN/wifi-with-me & a matrix room

Needs the following environment variables:
    - MMW_BOT_MATRIX_URL: the url of the matrix homeserver
    - MMW_BOT_MATRIX_ID: the user id of the bot on this server
    - MMW_BOT_MATRIX_PW: the password for this user
    - MMW_BOT_ROOM_ID: the room on which send the notifications
"""

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

from matrix_client.client import MatrixClient

SERVER_ADDRESS = ('', int(os.environ.get('MMW_BOT_PORT', 4785)))
MATRIX_URL = os.environ.get('MMW_BOT_MATRIX_URL', 'https://matrix.org')
MATRIX_ID = os.environ.get('MMW_BOT_MATRIX_ID', 'wwm')
MATRIX_PW = os.environ['MMW_BOT_MATRIX_PW']
ROOM_ID = os.environ['MMW_BOT_ROOM_ID']


class WWMBotServer(HTTPServer):
    """
    an HTTPServer that also contain a matrix client
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.matrix_client = MatrixClient(MATRIX_URL)
        self.matrix_token = self.matrix_client.login(username=MATRIX_ID, password=MATRIX_PW)
        self.matrix_room = self.matrix_client.get_rooms()[ROOM_ID]


class WWMBotForwarder(BaseHTTPRequestHandler):
    """
    Class given to the server, st. it knows what to do with a request.
    This one handles the HTTP request, and forwards it to the matrix room.
    """

    def do_POST(self):
        """
        main method, get a json dict from wifi-with-me, send a message to a matrix room
        """
        length = int(self.headers.get('Content-Length'))
        data = json.loads(self.rfile.read(length).decode())
        self.server.matrix_room.send_text(f'Got a request on {self.path}: {data}')
        self.ret_ok()

    def ret_ok(self):
        """
        return a success status
        """
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(b"{'status': 'OK'}")


if __name__ == '__main__':
    WWMBotServer(SERVER_ADDRESS, WWMBotForwarder).serve_forever()
