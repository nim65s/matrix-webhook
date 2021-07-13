#!/usr/bin/env python
"""Entry point to start an instrumentalized bot for coverage and run tests."""

from os import environ
from subprocess import Popen, run
from time import time
from unittest import main

import httpx
import yaml
from synapse._scripts.register_new_matrix_user import request_registration

BOT_URL = 'http://localhost:4785'
MATRIX_URL, MATRIX_ID, MATRIX_PW = (environ[v] for v in ['MATRIX_URL', 'MATRIX_ID', 'MATRIX_PW'])


def wait_available(url: str, key: str, timeout: int = 10) -> bool:
    """Wait until a service answer correctly or timeout."""
    def check_json(url: str, key: str) -> bool:
        """Ensure a service at a given url answers with valid json containing a certain key."""
        try:
            data = httpx.get(url).json()
            return key in data
        except httpx.ConnectError:
            return False

    start = time()
    while True:
        if check_json(url, key):
            return True
        if time() > start + timeout:
            return False


def run_and_test():
    """Launch the bot and its tests."""
    if not wait_available(f'{MATRIX_URL}/_matrix/client/r0/login', 'flows'):
        return False

    # Try to register a user for the bot.
    with open('/srv/homeserver.yaml') as f:
        secret = yaml.safe_load(f.read()).get("registration_shared_secret", None)
    request_registration(MATRIX_ID, MATRIX_PW, MATRIX_URL, secret, admin=True)

    bot = Popen(['coverage', 'run', 'matrix_webhook.py'])

    if not wait_available(BOT_URL, 'status'):
        return False

    ret = main(module=None, exit=False).result.wasSuccessful()
    bot.terminate()
    for cmd in ['report', 'html', 'xml']:
        run(['coverage', cmd])
    return ret


if __name__ == '__main__':
    exit(not run_and_test())
