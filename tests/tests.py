"""Main test module."""

import os
import unittest

import httpx
import nio

from .start import BOT_URL, MATRIX_ID, MATRIX_PW, MATRIX_URL

KEY = os.environ['API_KEY']
FULL_ID = f'@{MATRIX_ID}:{MATRIX_URL.split("/")[2]}'


def bot_req(req=None, key=None, room_id=None):
    """Bot requests boilerplate."""
    if key is not None:
        req['key'] = key
    url = BOT_URL if room_id is None else f'{BOT_URL}/{room_id}'
    return httpx.post(url, json=req).json()


class BotTest(unittest.IsolatedAsyncioTestCase):
    """Main test class."""
    def test_errors(self):
        """Check the bot's error paths."""
        self.assertEqual(bot_req(), {'status': 400, 'ret': 'Invalid JSON'})
        self.assertEqual(bot_req({'toto': 3}), {'status': 400, 'ret': 'Missing text and/or API key property'})
        self.assertEqual(bot_req({'text': 3, 'key': None}), {'status': 401, 'ret': 'Invalid API key'})

        # TODO: we are not sending to a real room, so this should not be "OK"
        self.assertEqual(bot_req({'text': 3}, KEY), {'status': 200, 'ret': 'OK'})

    async def test_message(self):
        """Send a markdown message, and check the result."""
        text = '# Hello'
        messages = []
        client = nio.AsyncClient(MATRIX_URL, MATRIX_ID)

        await client.login(MATRIX_PW)
        room = await client.room_create()

        self.assertEqual(bot_req({'text': text}, KEY, room.room_id), {'status': 200, 'ret': 'OK'})

        sync = await client.sync()
        messages = await client.room_messages(room.room_id, sync.next_batch)
        await client.close()

        message = messages.chunk[0]
        self.assertEqual(message.sender, FULL_ID)
        self.assertEqual(message.body, text)
        self.assertEqual(message.formatted_body, '<h1>Hello</h1>')

    async def test_z_disconnected(self):
        """Send a message after disconnection, and check the error."""
        client = nio.AsyncClient(MATRIX_URL, MATRIX_ID)
        await client.login(MATRIX_PW)
        token = client.access_token

        resp = httpx.post(f'{MATRIX_URL}/_synapse/admin/v1/deactivate/{FULL_ID}',
                          json={'erase': True},
                          params={'access_token': token})
        self.assertEqual(resp.json(), {'id_server_unbind_result': 'success'})

        await client.logout(all_devices=True)
        await client.close()

        # TODO: I was hopping that one wouldn't be happy
        self.assertEqual(bot_req({'text': 'bye'}, KEY), {'status': 200, 'ret': 'OK'})
