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
            {"status": 400, "ret": "Missing body, key, room_id"},
        )
        self.assertEqual(
            bot_req({"body": 3}, "wrong_key", "wrong_room"),
            {"status": 401, "ret": "Invalid API key"},
        )
        self.assertEqual(
            bot_req({"body": 3}, "wrong_key", "wrong_room", key_as_param=True),
            {"status": 401, "ret": "Invalid API key"},
        )
        self.assertEqual(
            bot_req({"body": 3}, KEY, params={"formatter": "wrong_formatter"}),
            {"status": 400, "ret": "Unknown formatter"},
        )
        # TODO: if the client from matrix_webhook has olm support,
        # this won't be a 403 from synapse, but a LocalProtocolError from matrix_webhook
        self.assertEqual(
            bot_req({"body": 3}, KEY, "wrong_room"),
            {"status": 400, "ret": "wrong_room was not legal room ID or room alias"},
        )
        self.assertEqual(
            bot_req({"body": 3}, KEY, "wrong_room", key_as_param=True),
            {"status": 400, "ret": "wrong_room was not legal room ID or room alias"},
        )

    async def test_message(self):
        """Send a markdown message with the old format, and check the result."""
        text = "# Hello"
        messages = []
        client = nio.AsyncClient(MATRIX_URL, MATRIX_ID)

        await client.login(MATRIX_PW)
        room = await client.room_create()

        self.assertEqual(
            bot_req({"text": text}, KEY, room.room_id),
            {"status": 200, "ret": "OK"},
        )

        sync = await client.sync()
        messages = await client.room_messages(room.room_id, sync.next_batch)
        await client.close()

        message = messages.chunk[0]
        self.assertEqual(message.sender, FULL_ID)
        self.assertEqual(message.body, text)
        self.assertEqual(message.formatted_body, "<h1>Hello</h1>")

    async def test_room_id_req(self):
        """Send a markdown message in a room given as data, and check the result."""
        body = "# Hello"
        messages = []
        client = nio.AsyncClient(MATRIX_URL, MATRIX_ID)

        await client.login(MATRIX_PW)
        room = await client.room_create()

        self.assertEqual(
            bot_req({"body": body, "room_id": room.room_id}, KEY, room.room_id),
            {"status": 200, "ret": "OK"},
        )

        sync = await client.sync()
        messages = await client.room_messages(room.room_id, sync.next_batch)
        await client.close()

        message = messages.chunk[0]
        self.assertEqual(message.sender, FULL_ID)
        self.assertEqual(message.body, body)
        self.assertEqual(message.formatted_body, "<h1>Hello</h1>")

    async def test_room_id_parameter(self):
        """Send a markdown message in a room given as parameter."""
        body = "# Hello"
        messages = []
        client = nio.AsyncClient(MATRIX_URL, MATRIX_ID)

        await client.login(MATRIX_PW)
        room = await client.room_create()

        self.assertEqual(
            bot_req({"body": body}, KEY, room.room_id, room_as_parameter=True),
            {"status": 200, "ret": "OK"},
        )

        sync = await client.sync()
        messages = await client.room_messages(room.room_id, sync.next_batch)
        await client.close()

        message = messages.chunk[0]
        self.assertEqual(message.sender, FULL_ID)
        self.assertEqual(message.body, body)
        self.assertEqual(message.formatted_body, "<h1>Hello</h1>")

    async def test_markdown_body(self):
        """Send a markdown message, and check the result."""
        body = "# Hello"
        messages = []
        client = nio.AsyncClient(MATRIX_URL, MATRIX_ID)

        await client.login(MATRIX_PW)
        room = await client.room_create()

        self.assertEqual(
            bot_req({"body": body}, KEY, room.room_id),
            {"status": 200, "ret": "OK"},
        )

        sync = await client.sync()
        messages = await client.room_messages(room.room_id, sync.next_batch)
        await client.close()

        message = messages.chunk[0]
        self.assertEqual(message.sender, FULL_ID)
        self.assertEqual(message.body, body)
        self.assertEqual(message.formatted_body, "<h1>Hello</h1>")

    async def test_formatted_body(self):
        """Send a formatted message, and check the result."""
        body = "Formatted message"
        formatted_body = "<del>markdown</del><strong>Formatted</strong> message"
        messages = []
        client = nio.AsyncClient(MATRIX_URL, MATRIX_ID)

        await client.login(MATRIX_PW)
        room = await client.room_create()

        self.assertEqual(
            bot_req(
                {"body": body, "formatted_body": formatted_body},
                KEY,
                room.room_id,
            ),
            {"status": 200, "ret": "OK"},
        )

        sync = await client.sync()
        messages = await client.room_messages(room.room_id, sync.next_batch)
        await client.close()

        message = messages.chunk[0]
        self.assertEqual(message.sender, FULL_ID)
        self.assertEqual(message.body, body)
        self.assertEqual(message.formatted_body, formatted_body)

    async def test_reconnect(self):
        """Check the reconnecting path."""
        client = nio.AsyncClient(MATRIX_URL, MATRIX_ID)
        await client.login(MATRIX_PW)
        room = await client.room_create()
        await client.logout(all_devices=True)
        await client.close()
        self.assertEqual(
            bot_req({"body": "Re"}, KEY, room.room_id),
            {"status": 200, "ret": "OK"},
        )
