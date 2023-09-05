"""Matrix Webhook app."""

import asyncio
import logging
from signal import SIGINT, SIGTERM

from aiohttp import web

import conf
import handler
import utils
from storage import DataStorage
from matrix import MatrixClient

LOGGER = logging.getLogger("matrix_webhook.app")


async def main(event):
    """Launch main coroutine.

    matrix client login & start web server
    """

    storage = DataStorage(conf.STORAGE_LOCATION)
    matrix_client = MatrixClient(storage)

    await matrix_client.login()
    utils.CLIENT = matrix_client

    print("Running")

    server = web.Server(handler.matrix_webhook)
    runner = web.ServerRunner(server)
    await runner.setup()
    LOGGER.info(f"Binding on {conf.SERVER_ADDRESS=}")
    site = web.TCPSite(runner, *conf.SERVER_ADDRESS)
    await site.start()

    # Run until we get a shutdown request
    await event.wait()

    # Cleanup
    await runner.cleanup()
    await matrix_client.close()


def terminate(event, signal):
    """Close handling stuff."""
    event.set()
    asyncio.get_event_loop().remove_signal_handler(signal)


def run():
    """Launch everything."""
    LOGGER.info("Starting...")
    loop = asyncio.get_event_loop()
    event = asyncio.Event()

    for sig in (SIGINT, SIGTERM):
        loop.add_signal_handler(sig, terminate, event, sig)

    loop.run_until_complete(main(event))

    LOGGER.info("Closing...")
    loop.close()
