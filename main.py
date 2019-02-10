#!/usr/bin/env python
"""
wifi-with-matrix script.
Bridge between https://code.ffdn.org/FFDN/wifi-with-me & a matrix room
"""

from http.server import BaseHTTPRequestHandler, HTTPServer

SERVER_ADDRESS = ('', 4785)


class Forwarder(BaseHTTPRequestHandler):
    """
    Class given to the server, st. it knows what to do with a request.
    This one handles the HTTP request, and forwards it to the matrix room.
    """

    def do_POST(self):
        """
        main method, get a json dict from wifi-with-me, send a message to a matrix room
        """
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
    HTTPServer(SERVER_ADDRESS, Forwarder).serve_forever()
