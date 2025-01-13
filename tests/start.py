#!/usr/bin/env python
"""Entry point to start an instrumentalized bot for coverage and run tests."""

import argparse
import logging
from os import environ
from pathlib import Path
from subprocess import Popen, run
from time import time
from unittest import main

import httpx
import yaml
from synapse._scripts.register_new_matrix_user import request_registration

BOT_URL = "http://localhost:4785"
KEY, MATRIX_URL, MATRIX_ID, MATRIX_PW = (
    environ[v] for v in ["API_KEY", "MATRIX_URL", "MATRIX_ID", "MATRIX_PW"]
)
FULL_ID = f"@{MATRIX_ID}:{MATRIX_URL.split('/')[2]}"
LOGGER = logging.getLogger("matrix-webhook.tests.start")

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    "-v",
    "--verbose",
    action="count",
    default=0,
    help="increment verbosity level",
)


def bot_req(
    req=None,
    key=None,
    room_id=None,
    params=None,
    key_as_param=False,
    room_as_parameter=False,
):
    """Bot requests boilerplate."""
    if params is None:
        params = {}
    if key is not None:
        if key_as_param:
            params["key"] = key
        else:
            req["key"] = key
    if room_as_parameter:
        params["room_id"] = room_id
    url = BOT_URL if room_id is None or room_as_parameter else f"{BOT_URL}/{room_id}"
    return httpx.post(url, params=params, json=req).json()


def wait_available(url: str, key: str, timeout: int = 10) -> bool:
    """Wait until a service answer correctly or timeout."""

    def check_json(url: str, key: str) -> bool:
        """Ensure a service answers with valid json including a certain key."""
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
    # Start the server, and wait for it
    LOGGER.info("Spawning synapse")
    srv = Popen(
        [
            "python",
            "-m",
            "synapse.app.homeserver",
            "--config-path",
            "/srv/homeserver.yaml",
        ],
    )
    if not wait_available(f"{MATRIX_URL}/_matrix/client/r0/login", "flows"):
        return False

    # Register a user for the bot.
    LOGGER.info("Registering the bot")
    with Path("/srv/homeserver.yaml").open() as f:
        secret = yaml.safe_load(f.read()).get("registration_shared_secret", None)
    request_registration(MATRIX_ID, MATRIX_PW, MATRIX_URL, secret, admin=True)

    # Start the bot, and wait for it
    LOGGER.info("Spawning the bot")
    bot = Popen(["coverage", "run", "-m", "matrix_webhook", "-vvvvv"])
    if not wait_available(BOT_URL, "status"):
        return False

    # Run the main unittest module
    LOGGER.info("Runnig unittests")
    ret = main(module=None, exit=False).result.wasSuccessful()

    LOGGER.info("Stopping synapse")
    srv.terminate()

    # TODO Check what the bot says when the server is offline
    # print(bot_req({'data': 'bye'}, KEY), {'status': 200, 'ret': 'OK'})

    LOGGER.info("Stopping the bot")
    bot.terminate()

    LOGGER.info("Processing coverage")
    for cmd in ["report", "html", "xml"]:
        run(["coverage", cmd])
    return ret


if __name__ == "__main__":
    args = parser.parse_args()
    log_format = "%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s"
    logging.basicConfig(level=50 - 10 * args.verbose, format=log_format)
    exit(not run_and_test())
