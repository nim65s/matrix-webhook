"""Main test module."""

import json
import os

import aiohttp
import nio

from utils import MATRIX_ID, MATRIX_PW, MATRIX_URL, AbstractBotTest

KEY = os.environ['API_KEY']


class BotTest(AbstractBotTest):
    """Main test class."""
    async def test_errors(self):
        """Check the bot's error paths."""
        async with aiohttp.ClientSession() as session:
            async with session.get('http://bot:4785') as response:
                self.assertEqual(await response.json(), {'status': 400, 'ret': 'Invalid JSON'})
            async with session.post('http://bot:4785', data=json.dumps({'toto': 3})) as response:
                self.assertEqual(await response.json(), {'status': 400, 'ret': 'Missing text and/or API key property'})
            async with session.post('http://bot:4785', data=json.dumps({'text': 3, 'key': None})) as response:
                self.assertEqual(await response.json(), {'status': 401, 'ret': 'Invalid API key'})
            async with session.post('http://bot:4785', data=json.dumps({'text': 3, 'key': KEY})) as response:
                # TODO: we are not sending to a real room, so this should not be "OK"
                self.assertEqual(await response.json(), {'status': 200, 'ret': 'OK'})

    async def test_message(self):
        """Send a markdown message, and check the result."""
        text = '# Hello'
        messages = []
        client = nio.AsyncClient(MATRIX_URL, MATRIX_ID)

        await client.login(MATRIX_PW)

        room = await client.room_create()

        url = f'http://bot:4785/{room.room_id}'
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=json.dumps({'text': text, 'key': KEY})) as response:
                self.assertEqual(await response.json(), {'status': 200, 'ret': 'OK'})

        sync = await client.sync()
        messages = await client.room_messages(room.room_id, sync.next_batch)

        message = messages.chunk[0]
        self.assertEqual(message.sender, '@bot:tests')
        self.assertEqual(message.body, text)
        self.assertEqual(message.formatted_body, '<h1>Hello</h1>')
        await client.close()
