"""Test module for threaded replies via ``thread_root``."""

import unittest

import nio

from .start import FULL_ID, KEY, MATRIX_ID, MATRIX_PW, MATRIX_URL, assert_sent, bot_req


class ThreadTest(unittest.IsolatedAsyncioTestCase):
    """Verify ``thread_root`` attaches the message to a thread."""

    async def test_thread_reply(self):
        """Root -> event_id; reply with thread_root -> m.thread relation."""
        client = nio.AsyncClient(MATRIX_URL, MATRIX_ID)

        await client.login(MATRIX_PW)
        room = await client.room_create()

        root = bot_req({"body": "**headline**"}, KEY, room.room_id)
        assert_sent(self, root)

        reply = bot_req(
            {"body": "```\ndetails\n```", "thread_root": root["event_id"]},
            KEY,
            room.room_id,
        )
        assert_sent(self, reply)
        self.assertNotEqual(reply["event_id"], root["event_id"])

        sync = await client.sync()
        messages = await client.room_messages(room.room_id, sync.next_batch)
        await client.close()

        by_id = {m.event_id: m for m in messages.chunk}
        self.assertEqual(by_id[root["event_id"]].sender, FULL_ID)
        self.assertNotIn("m.relates_to", by_id[root["event_id"]].source["content"])

        relation = by_id[reply["event_id"]].source["content"]["m.relates_to"]
        self.assertEqual(relation["rel_type"], "m.thread")
        self.assertEqual(relation["event_id"], root["event_id"])
        self.assertTrue(relation["is_falling_back"])
        self.assertEqual(relation["m.in_reply_to"], {"event_id": root["event_id"]})

    async def test_empty_thread_root_is_ignored(self):
        """An empty ``thread_root`` sends a normal, unrelated message."""
        client = nio.AsyncClient(MATRIX_URL, MATRIX_ID)

        await client.login(MATRIX_PW)
        room = await client.room_create()

        resp = bot_req({"body": "plain", "thread_root": ""}, KEY, room.room_id)
        assert_sent(self, resp)

        sync = await client.sync()
        messages = await client.room_messages(room.room_id, sync.next_batch)
        await client.close()

        self.assertNotIn("m.relates_to", messages.chunk[0].source["content"])
