#!/usr/bin/env python3
"""
wifi-with-matrix script.
Bridge between https://code.ffdn.org/FFDN/wifi-with-me & a matrix room
"""

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

from matrix_client.client import MatrixClient

SERVER_ADDRESS = ('', int(os.environ.get('PORT', 4785)))
MATRIX_URL = os.environ.get('MATRIX_URL', 'https://matrix.org')
MATRIX_ID = os.environ.get('MATRIX_ID', 'wwm')
MATRIX_PW = os.environ['MATRIX_PW']
ROOM_ID = os.environ['ROOM_ID']
API_KEY = os.environ['API_KEY']


class WWMBotServer(HTTPServer):
    """
    an HTTPServer that also contain a matrix client
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        client = MatrixClient(MATRIX_URL)
        client.login(username=MATRIX_ID, password=MATRIX_PW)
        self.room = client.get_rooms()[ROOM_ID]


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
        status = 'I need a json dict with name, url, key'
        if all(key in data for key in ['name', 'url', 'key']):
            status = 'wrong key'
            if data['key'] == API_KEY:
                status = 'OK'
                self.server.room.send_text(f'Nouvelle demande de {data["name"]}: {data["url"]}')

        self.send_response(200 if status == 'OK' else 401)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(b"{'status': %a}" % status)


if __name__ == '__main__':
    print('Wifi-With-Matrix bridge starting…')
    WWMBotServer(SERVER_ADDRESS, WWMBotForwarder).serve_forever()
