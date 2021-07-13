"""Main test module."""

import unittest

import nio

from .start import FULL_ID, KEY, MATRIX_ID, MATRIX_PW, MATRIX_URL, bot_req


class BotTest(unittest.IsolatedAsyncioTestCase):
    """Main test class."""

    def test_errors(self):
        """Check the bot's error paths."""
        self.assertEqual(bot_req(), {"status": 400, "ret": "Invalid JSON"})
        self.assertEqual(
            bot_req({"toto": 3}),
            {"status": 400, "ret": "Missing text and/or API key property"},
        )
        self.assertEqual(
            bot_req({"text": 3, "key": None}), {"status": 401, "ret": "Invalid API key"}
        )

        # TODO: we are not sending to a real room, so this should not be "OK"
        self.assertEqual(bot_req({"text": 3}, KEY), {"status": 200, "ret": "OK"})

    async def test_message(self):
        """Send a markdown message, and check the result."""
        text = "# Hello"
        messages = []
        client = nio.AsyncClient(MATRIX_URL, MATRIX_ID)

        await client.login(MATRIX_PW)
        room = await client.room_create()

        self.assertEqual(
            bot_req({"text": text}, KEY, room.room_id), {"status": 200, "ret": "OK"}
        )

        sync = await client.sync()
        messages = await client.room_messages(room.room_id, sync.next_batch)
        await client.close()

        message = messages.chunk[0]
        self.assertEqual(message.sender, FULL_ID)
        self.assertEqual(message.body, text)
        self.assertEqual(message.formatted_body, "<h1>Hello</h1>")
