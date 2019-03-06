#!/usr/bin/env python3
"""
Matrix Webhook
Post a message to a matrix room with a simple HTTP POST
"""

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

from matrix_client.client import MatrixClient

SERVER_ADDRESS = ('', int(os.environ.get('PORT', 4785)))
MATRIX_URL = os.environ.get('MATRIX_URL', 'https://matrix.org')
MATRIX_ID = os.environ.get('MATRIX_ID', 'wwm')
MATRIX_PW = os.environ['MATRIX_PW']
API_KEY = os.environ['API_KEY']


class MatrixWebhookServer(HTTPServer):
    """
    an HTTPServer that embeds a matrix client
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = MatrixClient(MATRIX_URL)
        self.client.login(username=MATRIX_ID, password=MATRIX_PW)
        self.rooms = self.client.get_rooms()


class MatrixWebhookHandler(BaseHTTPRequestHandler):
    """
    Class given to the server, st. it knows what to do with an HTTP request.
    This one handles a POST, checks its content, and forwards it to the matrix room.
    """

    def do_POST(self):
        """
        get a json dict from the request, send a message to a matrix room
        """
        length = int(self.headers.get('Content-Length'))
        data = json.loads(self.rfile.read(length).decode())
        status, ret = 400, 'I need a json dict with text & key'
        if all(key in data for key in ['text', 'key']):
            status, ret = 401, 'I need the good "key"'
            if data['key'] == API_KEY:
                status, ret = 404, 'I need the id of the room as a path, and to be in this room'
                if self.path[1:] not in self.server.rooms:
                    # try to see if this room has been joined recently
                    self.server.rooms = self.server.client.get_rooms()
                if self.path[1:] in self.server.rooms:
                    status, ret = 200, json.dumps(self.server.rooms[self.path[1:]].send_text(data['text']))

        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"status": %i, "ret": "%a"}' % (status, ret))


if __name__ == '__main__':
    MatrixWebhookServer(SERVER_ADDRESS, MatrixWebhookHandler).serve_forever()
