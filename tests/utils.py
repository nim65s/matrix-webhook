"""Utility tools to run tests."""
import asyncio
import os
import time
import unittest

import aiohttp
import yaml
from synapse._scripts.register_new_matrix_user import request_registration

BOT_URL = 'http://localhost:4785'
MATRIX_URL, MATRIX_ID, MATRIX_PW = (os.environ[v] for v in ['MATRIX_URL', 'MATRIX_ID', 'MATRIX_PW'])


class AbstractBotTest(unittest.IsolatedAsyncioTestCase):
    """Abstract test class."""
    async def asyncSetUp(self):
        """Set up the test environment."""
        # Wait for synapse and the bot to answer
        self.assertTrue(
            all(await asyncio.gather(
                wait_available(f'{MATRIX_URL}/_matrix/client/r0/login', 'flows'),
                wait_available(BOT_URL, 'status'),
            )))

        # Try to register an user for the bot. Don't worry if it already exists.
        with open('/srv/homeserver.yaml') as f:
            secret = yaml.safe_load(f.read()).get("registration_shared_secret", None)
        request_registration(MATRIX_ID, MATRIX_PW, MATRIX_URL, secret, admin=False, user_type=None, exit=lambda x: x)


async def check_json(session: aiohttp.ClientSession, url: str, key: str) -> bool:
    """Ensure a service at a given url answers with valid json containing a certain key."""
    try:
        async with session.get(url) as response:
            data = await response.json()
            return key in data
    except aiohttp.client_exceptions.ClientConnectorError:
        return False


async def wait_available(url: str, key: str, timeout: int = 60) -> bool:
    """Wait until a service answer correctly or timeout."""
    start = time.time()
    async with aiohttp.ClientSession() as session:
        while True:
            if await check_json(session, url, key):
                return True
            if time.time() > start + timeout:
                return False
