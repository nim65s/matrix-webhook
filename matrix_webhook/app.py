"""Matrix Webhook app."""

import asyncio
import logging
from pathlib import Path
from signal import SIGINT, SIGTERM

from aiohttp import web

from . import conf, handler, utils

LOGGER = logging.getLogger("matrix_webhook.app")


async def main(event):
    """Launch main coroutine.

    matrix client login & start web server
    """
    if conf.MATRIX_PW:
        msg = f"Log in {conf.MATRIX_ID=} on {conf.MATRIX_URL=}"
        LOGGER.info(msg)
        await utils.CLIENT.login(conf.MATRIX_PW)
    else:
        msg = f"Restoring log in {conf.MATRIX_ID=} on {conf.MATRIX_URL=}"
        LOGGER.info(msg)
        utils.CLIENT.access_token = conf.MATRIX_TOKEN

    server = web.Server(handler.matrix_webhook)
    runner = web.ServerRunner(server)
    await runner.setup()
    msg = f"Binding on {conf.SERVER_ADDRESS=}"
    LOGGER.info(msg)
    if conf.SERVER_PATH:
        site = web.UnixSite(runner, conf.SERVER_PATH)
    else:
        site = web.TCPSite(runner, *conf.SERVER_ADDRESS)
    await site.start()

    if conf.SERVER_PATH:
        Path(conf.SERVER_PATH).chmod(0o664)

    # Run until we get a shutdown request
    await event.wait()

    # Cleanup
    await runner.cleanup()
    await utils.CLIENT.close()


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
