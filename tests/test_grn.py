"""Test module for Github Release Notifier (grn) formatter.

ref https://github.com/femtopixel/github-release-notifier
"""

import unittest
from pathlib import Path

import httpx
import nio

from .start import BOT_URL, FULL_ID, KEY, MATRIX_ID, MATRIX_PW, MATRIX_URL


class GithubReleaseNotifierFormatterTest(unittest.IsolatedAsyncioTestCase):
    """GRN formatter test class."""

    async def test_grn_body(self):
        """Send a markdown message, and check the result."""
        messages = []
        client = nio.AsyncClient(MATRIX_URL, MATRIX_ID)

        await client.login(MATRIX_PW)
        room = await client.room_create()

        with Path("tests/example_grn.json").open() as f:
            example_grn_request = f.read()
        self.assertEqual(
            httpx.post(
                f"{BOT_URL}/{room.room_id}",
                params={"formatter": "grn", "key": KEY},
                content=example_grn_request,
            ).json(),
            {"status": 200, "ret": "OK"},
        )

        sync = await client.sync()
        messages = await client.room_messages(room.room_id, sync.next_batch)
        await client.close()

        message = messages.chunk[0]
        self.assertEqual(message.sender, FULL_ID)
        self.assertEqual(
            message.body,
            "#### [Alerting] Panel Title alert\nNotification Message\n\n* Count: 1\n",
        )
