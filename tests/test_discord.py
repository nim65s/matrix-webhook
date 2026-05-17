"""Test module for discord formatter.

ref https://discord.com/developers/docs/resources/webhook#execute-webhook
"""

import unittest
from pathlib import Path

import httpx
import nio

from .start import BOT_URL, FULL_ID, KEY, MATRIX_ID, MATRIX_PW, MATRIX_URL


class DiscordFormatterTest(unittest.IsolatedAsyncioTestCase):
    """Discord formatter test class."""

    async def test_discord_body(self):
        """Send a mock Discord webhook payload, and check the result."""
        client = nio.AsyncClient(MATRIX_URL, MATRIX_ID)

        await client.login(MATRIX_PW)
        room = await client.room_create()

        with Path("tests/example_discord.json").open() as f:
            example_discord_request = f.read()
        self.assertEqual(
            httpx.post(
                f"{BOT_URL}/{room.room_id}",
                params={"formatter": "discord", "key": KEY},
                content=example_discord_request,
            ).json(),
            {"status": 200, "ret": "OK"},
        )

        sync = await client.sync()
        messages = await client.room_messages(room.room_id, sync.next_batch)
        await client.close()

        gh = "https://github.com/nim65s"
        compare = f"{gh}/matrix-webhook/compare/ac7d1d964700...4bcdb25c8093"
        expected = (
            "**GitHub**: New commit pushed\n\n"
            f"[nim65s]({gh})\n"
            f"#### [matrix-webhook: 1 new commit]({compare})\n\n"
            "formatters: also get headers\n\n"
            "**Repository**: matrix-webhook\n"
            "**Branch**: devel\n\n"
            "Pushed by nim65s\n"
        )

        message = messages.chunk[0]
        self.assertEqual(message.sender, FULL_ID)
        self.assertEqual(message.body, expected)
