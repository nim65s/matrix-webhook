"""Test module for the captioned ``m.image`` upload feature."""

import struct
import threading
import unittest
import zlib
from http.server import BaseHTTPRequestHandler, HTTPServer

import httpx
import nio

from .start import BOT_URL, FULL_ID, KEY, MATRIX_ID, MATRIX_PW, MATRIX_URL


def _tiny_png():
    """Generate a minimal valid 1x1 RGBA PNG, no external fixture needed."""

    def chunk(name, data):
        return (
            struct.pack(">I", len(data))
            + name
            + data
            + struct.pack(">I", zlib.crc32(name + data))
        )

    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0)
    idat = zlib.compress(b"\x00\x00\x00\x00\x00")  # filter + transparent pixel
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", idat)
        + chunk(b"IEND", b"")
    )


PNG_BYTES = _tiny_png()
FIXTURE_PORT = 4786
FIXTURE_URL = f"http://localhost:{FIXTURE_PORT}/poster.png"


class _FixtureHandler(BaseHTTPRequestHandler):
    """Serve PNG_BYTES at /poster.png; 404 elsewhere."""

    def do_GET(self):
        """Handle the GET request."""
        if self.path == "/poster.png":
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", str(len(PNG_BYTES)))
            self.end_headers()
            self.wfile.write(PNG_BYTES)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):  # noqa: A002
        """Silence the default access log."""


class CaptionedImageTest(unittest.IsolatedAsyncioTestCase):
    """Verify explicit ``image_url`` produces captioned ``m.image`` events."""

    @classmethod
    def setUpClass(cls):
        """Start a threaded HTTP fixture server for the whole test class."""
        cls.server = HTTPServer(("localhost", FIXTURE_PORT), _FixtureHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        """Shut down the fixture server."""
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    async def test_image_with_caption(self):
        """Body + image_url -> m.image with body as caption."""
        body = "**Title**\n\nDescription text."
        client = nio.AsyncClient(MATRIX_URL, MATRIX_ID)

        await client.login(MATRIX_PW)
        room = await client.room_create()

        self.assertEqual(
            httpx.post(
                f"{BOT_URL}/{room.room_id}",
                json={"body": body, "image_url": FIXTURE_URL, "key": KEY},
            ).json(),
            {"status": 200, "ret": "OK"},
        )

        sync = await client.sync()
        messages = await client.room_messages(room.room_id, sync.next_batch)
        await client.close()

        msg = messages.chunk[0]
        self.assertEqual(msg.sender, FULL_ID)
        self.assertIsInstance(msg, nio.RoomMessageImage)
        self.assertTrue(msg.url.startswith("mxc://"))
        self.assertEqual(msg.body, body)
        src = msg.source["content"]
        self.assertEqual(src["filename"], "poster.png")
        self.assertEqual(src["info"]["mimetype"], "image/png")
        self.assertEqual(src["info"]["size"], len(PNG_BYTES))
        self.assertIn("<strong>Title</strong>", src["formatted_body"])

    async def test_no_image_url_sends_text(self):
        """No image_url -> m.text."""
        body = "Plain text, no image."
        client = nio.AsyncClient(MATRIX_URL, MATRIX_ID)

        await client.login(MATRIX_PW)
        room = await client.room_create()

        self.assertEqual(
            httpx.post(
                f"{BOT_URL}/{room.room_id}",
                json={"body": body, "key": KEY},
            ).json(),
            {"status": 200, "ret": "OK"},
        )

        sync = await client.sync()
        messages = await client.room_messages(room.room_id, sync.next_batch)
        await client.close()

        msg = messages.chunk[0]
        self.assertIsInstance(msg, nio.RoomMessageText)
        self.assertEqual(msg.body, body)

    async def test_empty_image_url_sends_text(self):
        """Empty image_url string -> m.text."""
        body = "Plain text, no image."
        client = nio.AsyncClient(MATRIX_URL, MATRIX_ID)

        await client.login(MATRIX_PW)
        room = await client.room_create()

        self.assertEqual(
            httpx.post(
                f"{BOT_URL}/{room.room_id}",
                json={"body": body, "image_url": "", "key": KEY},
            ).json(),
            {"status": 200, "ret": "OK"},
        )

        sync = await client.sync()
        messages = await client.room_messages(room.room_id, sync.next_batch)
        await client.close()

        msg = messages.chunk[0]
        self.assertIsInstance(msg, nio.RoomMessageText)
        self.assertEqual(msg.body, body)

    async def test_failed_image_falls_back_to_text(self):
        """If the upload fails, body is sent as m.text without the URL."""
        bad_url = f"http://localhost:{FIXTURE_PORT}/missing.png"
        body = "caption text"
        client = nio.AsyncClient(MATRIX_URL, MATRIX_ID)

        await client.login(MATRIX_PW)
        room = await client.room_create()

        self.assertEqual(
            httpx.post(
                f"{BOT_URL}/{room.room_id}",
                json={"body": body, "image_url": bad_url, "key": KEY},
            ).json(),
            {"status": 200, "ret": "OK"},
        )

        sync = await client.sync()
        messages = await client.room_messages(room.room_id, sync.next_batch)
        await client.close()

        msg = messages.chunk[0]
        self.assertIsInstance(msg, nio.RoomMessageText)
        self.assertEqual(msg.body, body)
        self.assertNotIn(bad_url, msg.body)
        for event in messages.chunk:
            self.assertNotIsInstance(event, nio.RoomMessageImage)

    async def test_unreachable_image_host_falls_back_to_text(self):
        """An image_url whose host doesn't resolve must NOT crash the request."""
        bad_url = "http://this-host-does-not-exist.invalid/poster.png"
        body = "caption text"
        client = nio.AsyncClient(MATRIX_URL, MATRIX_ID)

        await client.login(MATRIX_PW)
        room = await client.room_create()

        self.assertEqual(
            httpx.post(
                f"{BOT_URL}/{room.room_id}",
                json={"body": body, "image_url": bad_url, "key": KEY},
            ).json(),
            {"status": 200, "ret": "OK"},
        )

        sync = await client.sync()
        messages = await client.room_messages(room.room_id, sync.next_batch)
        await client.close()

        msg = messages.chunk[0]
        self.assertIsInstance(msg, nio.RoomMessageText)
        self.assertEqual(msg.body, body)
        self.assertNotIn(bad_url, msg.body)